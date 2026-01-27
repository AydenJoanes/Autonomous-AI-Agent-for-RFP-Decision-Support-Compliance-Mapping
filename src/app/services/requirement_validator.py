"""
Requirement Validator
Validates extracted requirements using LLM to catch errors and ensure checkability.
"""

import json
from typing import List, Optional, Dict, Any
from loguru import logger

from src.app.models.requirement import Requirement, RequirementType
from src.app.utils.llm_client import get_llm_client
from src.app.services.llm_config import get_llm_config


# System prompt for validation
VALIDATION_SYSTEM_PROMPT = """You are validating extracted RFP requirements.

Your goal is to KEEP genuine constraints and capabilities while removing noise.

AUTOMATICALLY MARK AS INVALID (is_valid: false):
-   Generic marketing fluff ("world class", "state of the art")
-   Vague "must" statements with no measurable outcome (e.g. "must be good")
-   Boilerplate legal headers not relevant to the solution

MARK AS VALID (is_valid: true) IF:
-   It describes a SCOPE BOUNDARY (Included/Excluded)
-   It defines an ENGAGEMENT MODEL (Fixed bid, Time & Materials, Managed Service, etc.)
-   It specifies DELIVERABLES (Reports, Dashboards, Documentation)
-   It mandates a STANDARD or CERTIFICATION (ISO, HIPAA)
-   It requires specific TECHNOLOGY or INFRASTRUCTURE (AWS, Azure, Python)
-   It specifies TIMELINE or BUDGET
-   It describes DATA HANDLING or SECURITY constraints

VALIDATION RULES:
1.  **Scope/Process/Engagement**: THESE ARE VALID. Do not filter them out just because they aren't a "database lookup".
    -   Valid: "Fixed price only", "No managed services", "Weekly reports required"
2.  **Specific Values**: Prefer specific values, but accept clear constraints.
    -   Valid: "Aggregated data only" (Clear constraint)
    -   Invalid: "Ensuring data quality" (Vague goal)

Return JSON: {"validations": [{"index": 0, "is_valid": true/false, "reason": "...", "confidence": 0.9}]}"""


def build_validation_user_prompt(requirements: List[Requirement]) -> str:
    """
    Build user prompt for validation.
    
    Args:
        requirements: Requirements to validate
        
    Returns:
        Formatted user prompt
    """
    # Convert requirements to simple dict format
    req_dicts = []
    for i, req in enumerate(requirements):
        req_dicts.append({
            "index": i,
            "type": req.type.value,
            "original_text": req.text,
            "extracted_value": req.extracted_value,
            "is_mandatory": req.is_mandatory
        })
    
    return f"""Validate these extracted RFP requirements:

{json.dumps(req_dicts, indent=2)}

For each requirement, assess validity and correctness. Return a JSON object with a "validations" array containing validation results."""


class RequirementValidator:
    """Validate extracted requirements using LLM."""
    
    def __init__(self):
        """Initialize the validator."""
        self.llm_client = get_llm_client()
        self.config = get_llm_config()
    
    def parse_validation_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse LLM validation response.
        
        Args:
            response: Parsed JSON response from LLM
            
        Returns:
            List of validation results
        """
        validations = response.get("validations", [])
        
        if not isinstance(validations, list):
            logger.error("Invalid validation response format")
            return []
        
        return validations
    
    def apply_validation(
        self,
        requirement: Requirement,
        validation: Dict[str, Any]
    ) -> Optional[Requirement]:
        """
        Apply validation result to requirement.
        
        Args:
            requirement: Original requirement
            validation: Validation result from LLM
            
        Returns:
            Updated requirement or None if invalid
        """
        # Check if valid
        is_valid = validation.get("is_valid", True)
        if not is_valid:
            reason = validation.get("reason", "Unknown")
            logger.debug(f"Requirement invalid: {requirement.extracted_value} - {reason}")
            return None
        
        # Check if type needs correction
        corrected_type = validation.get("corrected_type")
        if corrected_type:
            try:
                new_type = RequirementType[corrected_type.upper()]
                logger.debug(
                    f"Correcting requirement type: {requirement.type.value} → {new_type.value} "
                    f"for '{requirement.extracted_value}'"
                )
                requirement.type = new_type
            except KeyError:
                logger.warning(f"Invalid corrected type: {corrected_type}")
        
        # Check if value needs correction
        corrected_value = validation.get("corrected_value")
        if corrected_value:
            logger.debug(
                f"Correcting extracted value: '{requirement.extracted_value}' → '{corrected_value}'"
            )
            requirement.extracted_value = corrected_value
        
        # Add confidence score (if we extend Requirement model later)
        confidence = validation.get("confidence", 1.0)
        
        return requirement
    
    def validate_requirements(self, requirements: List[Requirement]) -> List[Requirement]:
        """
        Validate a list of requirements.
        
        Args:
            requirements: Requirements to validate
            
        Returns:
            Validated and filtered requirements
        """
        if not requirements:
            return []
        
        logger.info(f"Validating {len(requirements)} requirements using LLM")
        
        # Batch requirements
        batch_size = self.config.max_requirements_per_batch
        validated = []
        
        for i in range(0, len(requirements), batch_size):
            batch = requirements[i:i + batch_size]
            
            try:
                # Build prompts
                user_prompt = build_validation_user_prompt(batch)
                
                # Call LLM
                response = self.llm_client.call_llm_json(
                    system_prompt=VALIDATION_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    model=self.config.llm_validation_model,
                    temperature=self.config.validation_temperature,
                    timeout=self.config.validation_timeout
                )
                
                # Parse validations
                validations = self.parse_validation_response(response)
                
                # Apply validations
                for req, val in zip(batch, validations):
                    validated_req = self.apply_validation(req, val)
                    if validated_req:
                        validated.append(validated_req)
                
                logger.info(
                    f"Validated batch {i // batch_size + 1}: "
                    f"{len(batch)} → {len([v for v in validations if v.get('is_valid', True)])} valid"
                )
                
            except Exception as e:
                logger.error(f"Validation failed for batch {i // batch_size + 1}: {e}")
                # On error, keep all requirements from this batch (fail-open)
                validated.extend(batch)
        
        logger.info(f"Validation complete: {len(requirements)} → {len(validated)} requirements")
        
        return validated
    
    def validate_single_requirement(self, requirement: Requirement) -> Optional[Requirement]:
        """
        Validate a single requirement.
        
        Args:
            requirement: Requirement to validate
            
        Returns:
            Validated requirement or None if invalid
        """
        result = self.validate_requirements([requirement])
        return result[0] if result else None
