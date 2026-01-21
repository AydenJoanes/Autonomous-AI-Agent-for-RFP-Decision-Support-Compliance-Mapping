from typing import Type
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel, Field
from difflib import SequenceMatcher

from langchain.tools import BaseTool

from src.app.database.connection import SessionLocal
from src.app.database.repositories.cert_repository import CertificationRepository
from src.app.models.compliance import ComplianceLevel, ToolResult


class CertificationCheckerInput(BaseModel):
    certification_name: str = Field(..., description="The certification name to check")


class CertificationCheckerTool(BaseTool):
    name: str = "certification_checker"
    description: str = "Checks if company has required certification. Input should be certification name."
    args_schema: Type[BaseModel] = CertificationCheckerInput

    def _run(self, certification_name: str) -> str:
        logger.info(f"CertificationCheckerTool: Checking '{certification_name}'")
        
        session = SessionLocal()
        repository = CertificationRepository(session)
        
        try:
            # Step 1: Search certification (normalize)
            normalized_name = certification_name.strip()
            
            # Try exact match first
            cert = repository.get_by_name(normalized_name)
            exact_match = True
            
            # If not found, try fuzzy match
            if not cert:
                cert, exact_match = self._fuzzy_match(repository, normalized_name)
            
            # Step 2: Determine status and compliance
            if not cert:
                # NOT FOUND
                result = ToolResult(
                    tool_name=self.name,
                    requirement=certification_name,
                    status="NOT_FOUND",
                    compliance_level=ComplianceLevel.UNKNOWN,
                    confidence=0.9,
                    details={"searched_name": normalized_name},
                    message="Certification not found in database. Manual verification needed."
                )
                return result.model_dump_json()
            
            # Found certification - analyze it
            status = cert.get('status', 'unknown').lower()
            valid_until = cert.get('valid_until')
            cert_name = cert.get('name', normalized_name)
            
            compliance_level = ComplianceLevel.UNKNOWN
            confidence = 1.0
            risks = []
            message = ""
            details = {
                "cert_name": cert_name,
                "status": status,
                "valid_until": str(valid_until) if valid_until else None,
                "issuing_body": cert.get('issuing_body'),
                "scope": cert.get('scope')
            }
            
            # Handle different statuses
            final_status = status.upper()  # Default to DB status
            
            if status == "active":
                # Check expiry date
                if valid_until:
                    days_until_expiry = (valid_until - datetime.now().date()).days
                    details["days_until_expiry"] = days_until_expiry
                    
                    if days_until_expiry > 365:  # > 12 months
                        compliance_level = ComplianceLevel.COMPLIANT
                        confidence = 1.0
                        final_status = "VALID"
                        message = f"Certification '{cert_name}' is active and valid for {days_until_expiry} days."
                    
                    elif 90 <= days_until_expiry <= 365:  # 3-12 months
                        compliance_level = ComplianceLevel.WARNING
                        confidence = 1.0
                        final_status = "EXPIRING_SOON"
                        risks.append(f"Certification expiring in {days_until_expiry} days")
                        message = f"Certification '{cert_name}' is active but expiring in {days_until_expiry} days. Consider renewal."
                    
                    elif days_until_expiry < 90 and days_until_expiry >= 0:  # < 3 months but not expired
                        compliance_level = ComplianceLevel.WARNING
                        confidence = 1.0
                        final_status = "EXPIRING_SOON"
                        risks.append(f"Certification expiring soon ({days_until_expiry} days)")
                        message = f"WARNING: Certification '{cert_name}' expiring in {days_until_expiry} days. Urgent renewal needed."
                    
                    else:  # Already expired (negative days)
                        compliance_level = ComplianceLevel.NON_COMPLIANT
                        confidence = 1.0
                        final_status = "EXPIRED"
                        risks.append("Certification has expired")
                        message = f"Certification '{cert_name}' has expired {abs(days_until_expiry)} days ago."
                else:
                    # Active but no expiry date (perpetual or not tracked)
                    compliance_level = ComplianceLevel.COMPLIANT
                    confidence = 1.0
                    final_status = "VALID"
                    message = f"Certification '{cert_name}' is active (no expiry date on record)."
            
            elif status == "expired":
                compliance_level = ComplianceLevel.NON_COMPLIANT
                confidence = 1.0
                message = f"Certification '{cert_name}' has expired."
                risks.append("Certification status is expired")
            
            elif status == "pending":
                compliance_level = ComplianceLevel.PARTIAL
                confidence = 0.7
                message = f"Certification '{cert_name}' is pending approval/issuance."
                risks.append("Certification not yet finalized")
            
            elif status == "ready":
                compliance_level = ComplianceLevel.COMPLIANT
                confidence = 0.9
                message = f"Certification '{cert_name}' is ready (pre-approved or in progress)."
            
            else:
                # Unknown status
                compliance_level = ComplianceLevel.UNKNOWN
                confidence = 0.5
                message = f"Certification '{cert_name}' found with unknown status: {status}"
            
            # Step 3: Fuzzy match handling
            if not exact_match:
                confidence = max(0.0, confidence - 0.2)
                message += f" (Matched similar certification: {cert_name})"
                details["fuzzy_matched"] = True
            
            # Step 4: Return ToolResult as JSON
            result = ToolResult(
                tool_name=self.name,
                requirement=certification_name,
                status=final_status,
                compliance_level=compliance_level,
                confidence=confidence,
                details=details,
                risks=risks,
                message=message
            )
            
            return result.model_dump_json()
        
        except Exception as e:
            logger.error(f"CertificationCheckerTool Error: {e}")
            error_result = ToolResult(
                tool_name=self.name,
                requirement=certification_name,
                status="ERROR",
                compliance_level=ComplianceLevel.UNKNOWN,
                confidence=0.0,
                details={"error": str(e)},
                message=f"System error during certification check: {str(e)}"
            )
            return error_result.model_dump_json()
        
        finally:
            session.close()
    
    def _fuzzy_match(self, repository: CertificationRepository, search_name: str):
        """
        Attempt fuzzy matching on certification names.
        Returns (cert, exact_match) tuple.
        """
        all_certs = repository.get_all()
        
        best_match = None
        best_ratio = 0.0
        threshold = 0.8  # 80% similarity required
        
        for cert in all_certs:
            cert_name = cert.get('name', '')
            ratio = SequenceMatcher(None, search_name.lower(), cert_name.lower()).ratio()
            
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = cert
        
        if best_match:
            logger.info(f"Fuzzy matched '{search_name}' to '{best_match.get('name')}' (similarity: {best_ratio:.2%})")
            return best_match, False
        
        return None, False
    
    def _arun(self, certification_name: str):
        raise NotImplementedError("Async not implemented")
