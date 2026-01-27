"""
Recommendation Service
Main orchestrator for the entire RFP recommendation flow.
"""

import os
import time
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict
from loguru import logger

from src.app.models.requirement import Requirement, RequirementType
from src.app.models.compliance import ComplianceLevel, ToolResult
from src.app.models.recommendation import (
    Recommendation,
    RecommendationDecision,
    ComplianceSummary,
    ToolResultSummary,
    RFPMetadata,
    RiskItem,
    RiskSeverity,
    RiskCategory
)
from src.app.services.tool_executor import ToolExecutorService
from src.app.services.decision_engine import DecisionEngine
from src.app.services.justification_generator import JustificationGenerator
from src.app.strategies.compliance_strategy import aggregate_compliance

from src.app.services.reflection_engine import ReflectionEngine
from src.app.services.clarification_generator import ClarificationGenerator
from src.app.services.phase6_orchestrator import Phase6Orchestrator

# LLM Services
try:
    from src.app.services.llm_config import get_llm_config
    from src.app.services.llm_requirement_extractor import LLMRequirementExtractor
    from src.app.services.requirement_validator import RequirementValidator
    from src.app.services.requirement_validator import RequirementValidator
    from src.app.services.evidence_synthesizer import EvidenceSynthesizer
    from src.app.utils.embeddings import generate_batch_embeddings
    LLM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LLM services not available: {e}")
    LLM_AVAILABLE = False


class RecommendationService:
    """Main orchestrator for RFP recommendation generation."""
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc'}

    def __init__(self):
        """Initialize all service dependencies."""
        self._tool_executor = ToolExecutorService()
        self._decision_engine = DecisionEngine()
        self._justification_generator = JustificationGenerator()
        from src.app.parsers import UnifiedParser
        from src.app.agent.tools import RequirementProcessorTool
        self._unified_parser = UnifiedParser()
        self._requirement_processor = RequirementProcessorTool()
        self._reflection_engine = ReflectionEngine()
        self._clarification_generator = ClarificationGenerator()
        self._phase6_orchestrator = Phase6Orchestrator()
        
        # Initialize LLM services if available
        if LLM_AVAILABLE:
            try:
                self._llm_config = get_llm_config()
                self._llm_extractor = LLMRequirementExtractor()
                self._requirement_validator = RequirementValidator()
                self._evidence_synthesizer = EvidenceSynthesizer()
                logger.info("[SERVICE] LLM services initialized")
            except Exception as e:
                logger.warning(f"[SERVICE] LLM services initialization failed: {e}")
                self._llm_config = None
        else:
            self._llm_config = None
        
        logger.info("[SERVICE] RecommendationService initialized with all dependencies")

    def process_rfp(self, file_path: str) -> Tuple[str, List[Requirement], RFPMetadata]:
        """
        Parse RFP document and extract requirements.
        
        Args:
            file_path: Path to RFP file (PDF or DOCX)
            
        Returns:
            Tuple of (markdown_text, requirements, metadata)
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file extension not supported
        """
        logger.info(f"[SERVICE] Processing RFP: {file_path}")
        
        # Step 1: Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"RFP file not found: {file_path}")
        
        # Step 2: Validate file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}. Supported: {self.SUPPORTED_EXTENSIONS}")
        
        # Step 3: Parse document using Unified Parser
        try:
            parsed_doc = self._unified_parser.parse(file_path)
            markdown_text = parsed_doc.normalized_text
            
            logger.info(f"[SERVICE] Parsed with {parsed_doc.parser_used} (Quality: {parsed_doc.quality_score:.2f})")
            
            # Log warnings if any
            if parsed_doc.warnings:
                logger.warning(f"[SERVICE] Parse warnings: {parsed_doc.warnings}")
                
        except Exception as e:
            logger.error(f"[SERVICE] RFP parsing failed: {e}")
            raise RuntimeError(f"Failed to parse RFP document: {e}")
            
        # Step 3.5: Build initial metadata
        metadata = RFPMetadata(
            filename=os.path.basename(file_path),
            file_path=file_path,
            processed_date=datetime.now(timezone.utc),
            word_count=parsed_doc.word_count,
            requirement_count=0
        )
        
        # Add parser-specific metadata if supported by model
        # (Assuming RFPMetadata extensible or just logging for now)
        logger.info(f"[SERVICE] Metadata: Language={parsed_doc.language}, Conf={parsed_doc.language_confidence:.2f}")
        
        # Step 4: Extract requirements
        logger.info(f"DEBUG: LLM_AVAILABLE={LLM_AVAILABLE}")
        if self._llm_config:
            logger.info(f"DEBUG: Enable LLM Extraction={self._llm_config.enable_llm_extraction}")
        logger.info(f"DEBUG: Markdown text length={len(markdown_text) if markdown_text else 0}")

        try:
            # Try LLM extraction first if available
            if LLM_AVAILABLE and self._llm_config and self._llm_config.enable_llm_extraction:
                try:
                    logger.info("[SERVICE] Using LLM requirement extraction")
                    # Create parser-specific metadata
                    from src.app.models.parser import RFPMetadata as ParserMetadata
                    parser_meta = ParserMetadata(
                        filename=metadata.filename,
                        file_path=metadata.file_path,
                        file_size=os.path.getsize(file_path),
                        page_count=0  # Parser doesn't return page count yet
                    )
                    requirements = self._llm_extractor.extract_requirements_with_llm(markdown_text, parser_meta)
                except Exception as llm_error:
                    logger.warning(f"[SERVICE] LLM extraction failed, falling back to pattern-based: {llm_error}")
                    requirements = self._requirement_processor._run(markdown_text)
            else:
                # Use pattern-based extraction
                requirements = self._requirement_processor._run(markdown_text)
            
            # Validate requirements if LLM validation is enabled
            if LLM_AVAILABLE and self._llm_config and self._llm_config.enable_llm_validation and requirements:
                try:
                    logger.info("[SERVICE] Validating requirements with LLM")
                    original_count = len(requirements)
                    requirements = self._requirement_validator.validate_requirements(requirements)
                    logger.info(f"[SERVICE] Validation: {original_count} → {len(requirements)} requirements")
                except Exception as val_error:
                    logger.warning(f"[SERVICE] Requirement validation failed: {val_error}")
                    # Continue with unvalidated requirements
                    
        except Exception as e:
            logger.error(f"[SERVICE] Requirement extraction failed: {e}")
            requirements = []  # Graceful degradation
        
        # Step 4.25: Apply hard limit - REMOVED per user requirement
        # MAX_REQUIREMENTS = 50 limit removed to allow full extraction
        # if requirements and len(requirements) > MAX_REQUIREMENTS:
        #     logger.warning(f"[SERVICE] Too many requirements ({len(requirements)}), applying hard limit of {MAX_REQUIREMENTS}")
        #     ...
        #     requirements = sorted(requirements, key=lambda r: (priority_order.get(r.type, 99), -r.priority))[:MAX_REQUIREMENTS]
        
        logger.info(f"[SERVICE] Processing {len(requirements)} requirements (No Limit)")
        
        # Step 4.5: Generate embeddings for requirements
        if requirements and LLM_AVAILABLE:
            try:
                logger.info(f"[SERVICE] Generating embeddings for {len(requirements)} requirements")
                req_texts = [r.text for r in requirements]
                embeddings = generate_batch_embeddings(req_texts)
                
                for req, emb in zip(requirements, embeddings):
                    req.embedding = emb
            except Exception as e:
                logger.error(f"[SERVICE] Embedding generation failed: {e}")
                # Continue without embeddings (tools needing them will fail/skip)
        
        # Step 5: Update metadata
        metadata.requirement_count = len(requirements)
        
        logger.info(f"[SERVICE] Parsed RFP: {metadata.word_count} words, {metadata.requirement_count} requirements")
        
        return (markdown_text, requirements, metadata)

    def _build_tool_summaries(self, tool_results: List[ToolResult]) -> List[ToolResultSummary]:
        """
        Convert ToolResult objects to ToolResultSummary objects.
        
        Args:
            tool_results: List of ToolResult from tools
            
        Returns:
            List of ToolResultSummary for ComplianceSummary
        """
        summaries = []
        
        for result in tool_results:
            summary = ToolResultSummary(
                tool_name=result.tool_name,
                requirement=result.requirement[:100] if result.requirement else "",
                compliance_level=result.compliance_level,
                confidence=result.confidence,
                status=result.status
            )
            summaries.append(summary)
        
        return summaries

    def analyze_requirements(self, requirements: List[Requirement]) -> Tuple[List[ToolResult], ComplianceSummary]:
        """
        Analyze requirements using reasoning tools and aggregate compliance.
        
        Args:
            requirements: List of extracted requirements
            
        Returns:
            Tuple of (tool_results, compliance_summary)
        """
        logger.info(f"[SERVICE] Analyzing {len(requirements)} requirements")
        
        # Step 1: Execute all tools
        tool_results = self._tool_executor.execute_all_tools(requirements)
        
        # Step 2: Aggregate compliance
        aggregation = aggregate_compliance(tool_results)
        
        # Step 3: Build ToolResultSummary list
        tool_summaries = self._build_tool_summaries(tool_results)
        
        # Step 4: Build ComplianceSummary
        compliance_summary = ComplianceSummary(
            overall_compliance=aggregation["overall_compliance"],
            compliant_count=aggregation["compliant_count"],
            non_compliant_count=aggregation["non_compliant_count"],
            partial_count=aggregation["partial_count"],
            warning_count=aggregation["warning_count"],
            unknown_count=aggregation["unknown_count"],
            total_evaluated=aggregation["total_evaluated"],
            confidence_avg=aggregation["confidence_avg"],
            mandatory_met=aggregation["mandatory_requirements_met"],
            mandatory_unknown=aggregation.get("mandatory_unknown", False),
            mandatory_failed=aggregation.get("mandatory_failed", False),
            tool_results=tool_summaries
        )
        
        logger.info(f"[SERVICE] Analysis complete: {compliance_summary.overall_compliance}")
        
        return (tool_results, compliance_summary)

    def _create_empty_compliance_summary(self) -> ComplianceSummary:
        """Create an empty ComplianceSummary for error/edge cases."""
        return ComplianceSummary(
            overall_compliance=ComplianceLevel.UNKNOWN,
            compliant_count=0,
            non_compliant_count=0,
            partial_count=0,
            warning_count=0,
            unknown_count=0,
            total_evaluated=0,
            confidence_avg=0.0,
            mandatory_met=False,
            tool_results=[]
        )

    def _create_error_recommendation(self, file_path: str, error: str) -> Recommendation:
        """
        Create a NO_BID recommendation when critical error occurs.
        
        Args:
            file_path: Path to RFP file that failed
            error: Error message
            
        Returns:
            Recommendation with NO_BID and error details
        """
        logger.warning(f"[SERVICE] Creating error recommendation for {file_path}")
        
        return Recommendation(
            recommendation=RecommendationDecision.NO_BID,
            confidence_score=0,
            justification=f"Recommendation generation failed due to a system error: {error}. "
                          f"Manual review of the RFP document is required before making a bid decision. "
                          f"Please contact technical support if this error persists.",
            executive_summary=f"System error during processing. Manual review required.",
            risks=[
                RiskItem(
                    category=RiskCategory.TECHNICAL,
                    severity=RiskSeverity.HIGH,
                    description=f"System error during analysis: {error}",
                    source_tool="recommendation_service",
                    requirement_text=None
                )
            ],
            compliance_summary=self._create_empty_compliance_summary(),
            requires_human_review=True,
            review_reasons=["System error during processing", f"Error: {error}"],
            rfp_metadata=RFPMetadata(
                filename=os.path.basename(file_path) if file_path else "unknown",
                file_path=file_path or "unknown",
                processed_date=datetime.now(timezone.utc),
                word_count=0,
                requirement_count=0
            ),
            timestamp=datetime.now(timezone.utc)
        )

    def _create_no_requirements_recommendation(self, metadata: RFPMetadata) -> Recommendation:
        """
        Create a CONDITIONAL_BID recommendation when no requirements extracted.
        
        Args:
            metadata: RFP metadata from parsing
            
        Returns:
            Recommendation with CONDITIONAL_BID and explanation
        """
        logger.warning(f"[SERVICE] Creating no-requirements recommendation for {metadata.filename}")
        
        return Recommendation(
            recommendation=RecommendationDecision.CONDITIONAL_BID,
            confidence_score=30,
            justification="No requirements could be automatically extracted from the provided RFP document. "
                          "This may indicate the document format is not supported, the content is image-based, "
                          "or the requirements are not clearly structured. Manual review of the document is "
                          "essential before making a bid decision. Once requirements are manually identified, "
                          "the analysis can be re-run with structured input.",
            executive_summary="Unable to extract requirements automatically. Manual document review required before bid decision.",
            risks=[
                RiskItem(
                    category=RiskCategory.TECHNICAL,
                    severity=RiskSeverity.HIGH,
                    description="No requirements could be extracted from the document",
                    source_tool="requirement_processor",
                    requirement_text=None
                ),
                RiskItem(
                    category=RiskCategory.COMPLIANCE,
                    severity=RiskSeverity.MEDIUM,
                    description="Unable to verify compliance without extracted requirements",
                    source_tool="recommendation_service",
                    requirement_text=None
                )
            ],
            compliance_summary=self._create_empty_compliance_summary(),
            requires_human_review=True,
            review_reasons=[
                "No requirements extracted - manual review required",
                "Document may need manual parsing",
                "Compliance cannot be verified automatically"
            ],
            rfp_metadata=metadata,
            timestamp=datetime.now(timezone.utc)
        )

    def generate_recommendation(self, file_path: str) -> Recommendation:
        """
        Generate complete bid/no-bid recommendation for an RFP.
        
        Args:
            file_path: Path to RFP file
            
        Returns:
            Complete Recommendation object
        """
        logger.info(f"[SERVICE] Starting recommendation generation for {file_path}")
        start_time = time.time()
        
        try:
            # Step 1: Process RFP
            markdown_text, requirements, metadata = self.process_rfp(file_path)
            
            # Step 2: Handle no requirements case
            if not requirements:
                logger.warning("[SERVICE] No requirements extracted")
                return self._create_no_requirements_recommendation(metadata)
            
            # Step 3: Analyze requirements
            tool_results, compliance_summary = self.analyze_requirements(requirements)
            
            # Step 4: Extract risks
            risks = self._tool_executor.extract_risks_from_results(tool_results)
            logger.info(f"[SERVICE] Extracted {len(risks)} risks")
            
            # Step 4.5: Synthesize evidence (if LLM enabled)
            synthesis_report = None
            if LLM_AVAILABLE and self._llm_config and self._llm_config.enable_llm_synthesis:
                try:
                    logger.info("[SERVICE] Synthesizing evidence with LLM")
                    synthesis_report = self._evidence_synthesizer.synthesize_evidence(tool_results, requirements)
                    logger.info(f"[SERVICE] Synthesis: {synthesis_report.overall_assessment}")
                except Exception as synth_error:
                    logger.warning(f"[SERVICE] Evidence synthesis failed: {synth_error}")
                    synthesis_report = None
            
            # Step 5: Generate decision (with synthesis if available)
            decision = self._decision_engine.generate_decision(compliance_summary, risks, synthesis_report)
            logger.info(f"[SERVICE] Decision: {decision['recommendation']} (confidence: {decision['confidence_score']})")
            
            # Step 6: Generate justification (with synthesis if available)
            justification, executive_summary = self._justification_generator.generate(
                compliance_summary, decision, risks, synthesis_report
            )
            
            # Step 6.5: Generate Clarification Questions (Phase 6)
            try:
                clarification_questions = self._clarification_generator.generate(
                    compliance_summary, tool_results, decision, risks
                )
            except Exception as e:
                logger.error(f"[SERVICE] Clarification generation failed (non-blocking): {e}")
                clarification_questions = []  # Fallback to empty list

            # Step 7: Build Recommendation
            recommendation = Recommendation(
                recommendation=decision["recommendation"],
                confidence_score=decision["confidence_score"],
                justification=justification,
                executive_summary=executive_summary,
                risks=risks,
                compliance_summary=compliance_summary,
                requires_human_review=decision["requires_human_review"],
                review_reasons=decision["review_reasons"],
                clarification_questions=clarification_questions,
                rfp_metadata=metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Step 8: Phase 6 Orchestration (non-invasive coordination)
            # This applies reflection, ensures clarifications, and generates embedding
            # WITHOUT modifying Phase 5 logic
            try:
                # Pass synthesis report for enhanced reflection
                recommendation = self._phase6_orchestrator.orchestrate(recommendation, synthesis_report)
            except Exception as e:
                # Orchestration is optional - failure must not block response
                logger.error(f"[SERVICE] Phase 6 orchestration failed (non-blocking): {e}")
                # Continue with unenhanced recommendation
            
            # Step 9: Log completion
            elapsed = time.time() - start_time
            logger.info(f"[SERVICE] Recommendation complete in {elapsed:.2f}s: {recommendation.recommendation}")
            
            return recommendation
        
        except FileNotFoundError:
            # Re-raise file not found errors
            raise
        
        except ValueError as e:
            # Re-raise validation errors
            raise
        
        except Exception as e:
            # Handle unexpected errors gracefully
            logger.error(f"[SERVICE] Critical failure: {e}", exc_info=True)
            return self._create_error_recommendation(file_path, str(e))

    def _format_risks_table(self, risks: List[RiskItem]) -> str:
        """Format risks as markdown table."""
        if not risks:
            return "*No significant risks identified.*"
        
        lines = ["| Severity | Category | Description | Source |",
                 "|----------|----------|-------------|--------|"]
        
        severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        
        for risk in risks:
            emoji = severity_emoji.get(risk.severity, "•")
            lines.append(f"| {emoji} {risk.severity} | {risk.category} | {risk.description} | {risk.source_tool} |")
        
        return "\n".join(lines)

    def _format_review_reasons(self, review_reasons: List[str]) -> str:
        """Format review reasons as bullet list."""
        if not review_reasons:
            return ""
        
        lines = ["### Review Reasons", ""]
        for reason in review_reasons:
            lines.append(f"- {reason}")
        
        return "\n".join(lines)

    def _format_tool_results_detail(self, tool_results: List[ToolResultSummary]) -> str:
        """Format tool results as detailed list."""
        if not tool_results:
            return "*No detailed tool results available.*"
        
        lines = ["| Tool | Requirement | Status | Compliance | Confidence |",
                 "|------|-------------|--------|------------|------------|"]
        
        compliance_emoji = {
            "COMPLIANT": "✅",
            "PARTIAL": "◐",
            "WARNING": "⚠️",
            "NON_COMPLIANT": "❌",
            "UNKNOWN": "❓"
        }
        
        for tr in tool_results:
            emoji = compliance_emoji.get(tr.compliance_level, "•")
            # Truncate requirement for table
            req_short = tr.requirement[:40] + "..." if len(tr.requirement) > 40 else tr.requirement
            lines.append(f"| {tr.tool_name} | {req_short} | {tr.status} | {emoji} {tr.compliance_level} | {tr.confidence:.0%} |")
        
        return "\n".join(lines)

    def generate_recommendation_report(self, recommendation: Recommendation) -> str:
        """
        Generate a formatted markdown report from a Recommendation.
        
        Args:
            recommendation: Complete Recommendation object
            
        Returns:
            Formatted markdown string
        """
        logger.info("[SERVICE] Generating recommendation report")
        
        # Format risks table
        risks_table = self._format_risks_table(recommendation.risks)
        
        # Format review reasons
        review_reasons_text = self._format_review_reasons(recommendation.review_reasons)
        
        # Format tool results detail
        tool_results_detail = self._format_tool_results_detail(recommendation.compliance_summary.tool_results)
        
        # Build report
        report = f"""# RFP Bid Recommendation Report

**Generated:** {recommendation.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}
**Document:** {recommendation.rfp_metadata.filename}
**Word Count:** {recommendation.rfp_metadata.word_count:,}
**Requirements Analyzed:** {recommendation.rfp_metadata.requirement_count}

---

## Executive Summary

{recommendation.executive_summary}

---

## Recommendation

| Field | Value |
|-------|-------|
| **Decision** | **{recommendation.recommendation}** |
| **Confidence** | {recommendation.confidence_score}/100 |
| **Human Review Required** | {"Yes ⚠️" if recommendation.requires_human_review else "No ✓"} |

{review_reasons_text}

---

## Compliance Summary

| Metric | Count |
|--------|-------|
| ✅ Fully Compliant | {recommendation.compliance_summary.compliant_count} |
| ◐ Partially Compliant | {recommendation.compliance_summary.partial_count} |
| ❌ Non-Compliant | {recommendation.compliance_summary.non_compliant_count} |
| ⚠️ Warnings | {recommendation.compliance_summary.warning_count} |
| ❓ Unknown | {recommendation.compliance_summary.unknown_count} |
| **Total** | **{recommendation.compliance_summary.total_evaluated}** |

**Overall Compliance:** {recommendation.compliance_summary.overall_compliance}
**Average Confidence:** {recommendation.compliance_summary.confidence_avg:.0%}
**Mandatory Requirements Met:** {"Yes ✓" if recommendation.compliance_summary.mandatory_met else "No ❌"}

---

## Identified Risks

{risks_table}

---

## Detailed Justification

{recommendation.justification}

---

## Tool Results Detail

{tool_results_detail}

---

*Report generated by RFP Decision Support Agent v1.0*
"""
        
        logger.info(f"[SERVICE] Report generated: {len(report)} chars")
        return report
