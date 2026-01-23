"""
Justification Generator Service
Generates natural language justifications and executive summaries for bid decisions using LLM.
"""

from typing import List, Dict, Optional, Tuple
from loguru import logger

from src.app.models.recommendation import (
    RecommendationDecision,
    ComplianceSummary,
    RiskItem,
    ToolResultSummary
)
from src.app.utils.embeddings import get_openai_client
from src.app.services.decision_config import (
    JUSTIFICATION_MODEL,
    JUSTIFICATION_TEMPERATURE,
    MAX_RETRIES
)
from src.app.utils.retry import retry_with_backoff


# ============================================================================
# TEMPLATES & PROMPTS
# ============================================================================

FALLBACK_TEMPLATE = """
Based on automated compliance analysis:

**RECOMMENDATION: {recommendation}**
**CONFIDENCE: {confidence_score}/100**

**Summary:**
- {compliant_count} requirements fully met
- {partial_count} requirements partially met
- {non_compliant_count} requirements not met
- {warning_count} items flagged for attention
- {unknown_count} items could not be verified
- Mandatory requirements met: {mandatory_met}

**Key Risks:**
{risk_summary}

**Note:** This recommendation was generated using rule-based analysis due to justification generation failure. Human review is strongly advised.
"""

EXECUTIVE_FALLBACK = "{recommendation} recommended with {confidence_score}% confidence. {mandatory_status}. {risk_count} risks identified. Human review advised."

JUSTIFICATION_SYSTEM_PROMPT = """You are a senior pre-sales analyst at a technology consulting firm writing bid/no-bid recommendations for RFP responses.

ROLE: Objective analyst providing evidence-based recommendations
TONE: Professional, confident, balanced
AUDIENCE: Business development managers and executives

RULES:
1. Base ALL statements on the provided compliance data — never invent facts
2. Be specific — cite actual numbers and tool findings
3. Acknowledge uncertainties when compliance is UNKNOWN
4. For BID: Lead with strengths, address risks with mitigations
5. For NO_BID: Lead with blocking issues, acknowledge any positives briefly
6. For CONDITIONAL_BID: Clearly state conditions that must be resolved

OUTPUT FORMAT:
- 3-5 paragraphs
- ~200-300 words total
- No bullet points — use flowing prose
- No headers within the justification

STRUCTURE:
Paragraph 1: Clear recommendation statement with confidence level
Paragraph 2: Key strengths/evidence supporting the decision
Paragraph 3: Key concerns, risks, or gaps identified
Paragraph 4: (If CONDITIONAL_BID) Specific conditions to resolve
Paragraph 5: Closing recommendation with next steps"""

EXECUTIVE_SUMMARY_SYSTEM_PROMPT = """You are a senior pre-sales analyst writing a brief executive summary for busy decision-makers.

RULES:
1. Maximum 2-3 sentences
2. Lead with the recommendation and confidence
3. State the single most important factor
4. End with clear action item
5. No jargon — be direct

FORMAT: Plain text, no formatting, no bullet points"""

JUSTIFICATION_USER_PROMPT = """Analyze the following RFP compliance assessment and write a justification for the {recommendation} recommendation.

{context_prompt}

IMPORTANT REMINDERS:
- Confidence Score: {confidence_score}/100 ({confidence_text} confidence)
- Mandatory Requirements: {mandatory_text}
- This is a {recommendation} recommendation

Write the 3-5 paragraph justification now:"""

EXECUTIVE_SUMMARY_USER_PROMPT = """Based on this RFP compliance analysis, write a 2-3 sentence executive summary.

Recommendation: {recommendation}
Confidence: {confidence_score}/100
Mandatory Met: {mandatory_met}
Top Risk: {top_risk}

Compliance snapshot: {compliant_count} compliant, {non_compliant_count} non-compliant, {unknown_count} unknown out of {total} requirements.

Write the executive summary (2-3 sentences only):"""

CONTEXT_PROMPT_TEMPLATE = """## RFP Compliance Analysis Results

### Overall Assessment
- **Recommendation:** {recommendation}
- **Confidence Score:** {confidence_score}/100
- **Overall Compliance Level:** {overall_compliance}
- **Mandatory Requirements Met:** {mandatory_met}

### Compliance Breakdown
| Category | Count |
|----------|-------|
| Fully Compliant | {compliant_count} |
| Partially Compliant | {partial_count} |
| Non-Compliant | {non_compliant_count} |
| Warnings | {warning_count} |
| Unknown/Unverified | {unknown_count} |
| **Total Evaluated** | {total_evaluated} |

### Average Confidence: {confidence_avg:.0%}

### Tool-by-Tool Results
{tool_results_formatted}

### Identified Risks ({risk_count} total)
{risks_formatted}

### Decision Trace
{decision_trace_formatted}"""


# ============================================================================
# SERVICE CLASS
# ============================================================================

class JustificationGenerator:
    """Service to generate natural language justifications for bid decisions."""

    def __init__(self):
        """Initialize with OpenAI client and configuration."""
        self._client = get_openai_client()
        self._model = JUSTIFICATION_MODEL
        self._temperature = JUSTIFICATION_TEMPERATURE
        self._max_retries = MAX_RETRIES
        
        logger.info(f"[JUSTIFICATION] Initialized with model={self._model}, temp={self._temperature}")

    def _format_tool_results(self, tool_results: List[ToolResultSummary]) -> str:
        """Format detailed tool results for the prompt."""
        if not tool_results:
            return "No detailed tool results available."
        
        lines = []
        for tr in tool_results:
            emoji = {
                "COMPLIANT": "✓",
                "PARTIAL": "◐",
                "WARNING": "⚠",
                "NON_COMPLIANT": "✗",
                "UNKNOWN": "?"
            }.get(tr.compliance_level, "•")
            
            lines.append(f"{emoji} [{tr.tool_name}] {tr.status} (confidence: {tr.confidence:.0%})")
            lines.append(f"   Requirement: {tr.requirement}")
        
        return "\n".join(lines)

    def _format_risks(self, risks: List[RiskItem]) -> str:
        """Format risks for the prompt."""
        if not risks:
            return "No significant risks identified."
        
        lines = []
        for risk in risks:
            severity_indicator = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk.severity, "•")
            lines.append(f"{severity_indicator} [{risk.severity}] {risk.description}")
            lines.append(f"   Source: {risk.source_tool} | Category: {risk.category}")
        
        return "\n".join(lines)

    def _format_decision_trace(self, decision: Dict) -> str:
        """Format decision trace for transparency."""
        trace = decision.get("decision_trace", [])
        if not trace:
            return "Decision trace not available."
        
        return "\n".join(f"{i+1}. {step}" for i, step in enumerate(trace))

    def _build_context_prompt(
        self,
        compliance_summary: ComplianceSummary,
        decision: Dict,
        risks: List[RiskItem]
    ) -> str:
        """Build the comprehensive context prompt for the LLM."""
        return CONTEXT_PROMPT_TEMPLATE.format(
            recommendation=decision["recommendation"],
            confidence_score=decision["confidence_score"],
            overall_compliance=compliance_summary.overall_compliance,
            mandatory_met="Yes" if compliance_summary.mandatory_met else "No",
            compliant_count=compliance_summary.compliant_count,
            partial_count=compliance_summary.partial_count,
            non_compliant_count=compliance_summary.non_compliant_count,
            warning_count=compliance_summary.warning_count,
            unknown_count=compliance_summary.unknown_count,
            total_evaluated=compliance_summary.total_evaluated,
            confidence_avg=compliance_summary.confidence_avg,
            tool_results_formatted=self._format_tool_results(compliance_summary.tool_results),
            risk_count=len(risks),
            risks_formatted=self._format_risks(risks),
            decision_trace_formatted=self._format_decision_trace(decision)
        )

    def _generate_with_retry(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Execute LLM call with retry logic."""
        
        def _call():
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=self._temperature,
                max_tokens=500,  # Limit output length
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        
        try:
            result = retry_with_backoff(_call, max_retries=self._max_retries)
            logger.debug(f"[JUSTIFICATION] LLM response received: {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"[JUSTIFICATION] LLM call failed after retries: {e}")
            return None

    def _generate_fallback_justification(
        self,
        context_prompt: str,
        recommendation: RecommendationDecision,
        confidence_score: int
    ) -> str:
        """Generate template-based fallback justification."""
        # Note: In a real scenario we might parse context_prompt to fill these accurately
        # For robustness, we will try to extract what we can or use defaults
        # But since the caller has the raw data, maybe passing data is better? 
        # The interface specified passes context_prompt.
        # We'll use placeholders as strictly defined in the prompt which implies using the raw text might not be easy.
        # However, the USER prompt implementation instructions specific FALLBACK_TEMPLATE uses format keys.
        # We need to provide those keys.
        
        # We'll default to "N/A" as requested in the instructions if parsing is hard
        # But actually, the method signature in the instructions only takes (context_prompt, recommendation, confidence_score)
        # So we can't easily access the counts unless we parse them or change the signature.
        # The instructions say: "# Parse counts from context_prompt or use defaults"
        
        return FALLBACK_TEMPLATE.format(
            recommendation=recommendation,
            confidence_score=confidence_score,
            compliant_count="[See Summary]",
            partial_count="[See Summary]",
            non_compliant_count="[See Summary]",
            warning_count="[See Summary]",
            unknown_count="[See Summary]",
            mandatory_met="[See Summary]",
            risk_summary="Risk details unavailable due to generation failure."
        )

    def _generate_fallback_summary(
        self,
        recommendation: RecommendationDecision,
        confidence_score: int,
        compliance_summary: ComplianceSummary,
        risks: List[RiskItem]
    ) -> str:
        """Generate template-based fallback executive summary."""
        mandatory_status = "All mandatory requirements met" if compliance_summary.mandatory_met else "Some mandatory requirements not met"
        risk_count = len(risks)
        
        return EXECUTIVE_FALLBACK.format(
            recommendation=recommendation,
            confidence_score=confidence_score,
            mandatory_status=mandatory_status,
            risk_count=risk_count
        )

    def generate_justification(
        self,
        context_prompt: str,
        recommendation: RecommendationDecision,
        confidence_score: int,
        mandatory_met: bool
    ) -> str:
        """Generate distinct justification narrative."""
        # Calculate dynamic text
        conf = confidence_score
        confidence_text = "HIGH" if conf >= 75 else "MODERATE" if conf >= 50 else "LOW"
        mandatory_text = "ALL MET ✓" if mandatory_met else "NOT ALL MET ✗"
        
        # Build user prompt
        user_prompt = JUSTIFICATION_USER_PROMPT.format(
            recommendation=recommendation,
            context_prompt=context_prompt,
            confidence_score=confidence_score,
            confidence_text=confidence_text,
            mandatory_text=mandatory_text
        )
        
        # Generate with LLM
        result = self._generate_with_retry(JUSTIFICATION_SYSTEM_PROMPT, user_prompt)
        
        if result and len(result) >= 50:
            logger.info(f"[JUSTIFICATION] Generated justification: {len(result)} chars")
            return result
        
        # Fallback
        logger.warning("[JUSTIFICATION] Using fallback template for justification")
        return self._generate_fallback_justification(context_prompt, recommendation, confidence_score)

    def generate_executive_summary(
        self,
        context_prompt: str,
        recommendation: RecommendationDecision,
        confidence_score: int,
        compliance_summary: ComplianceSummary,
        risks: List[RiskItem]
    ) -> str:
        """Generate brief executive summary."""
        # Get top risk
        top_risk = risks[0].description if risks else "No significant risks"
        
        # Build user prompt
        user_prompt = EXECUTIVE_SUMMARY_USER_PROMPT.format(
            recommendation=recommendation,
            confidence_score=confidence_score,
            mandatory_met="Yes" if compliance_summary.mandatory_met else "No",
            top_risk=top_risk,
            compliant_count=compliance_summary.compliant_count,
            non_compliant_count=compliance_summary.non_compliant_count,
            unknown_count=compliance_summary.unknown_count,
            total=compliance_summary.total_evaluated
        )
        
        # Generate with LLM
        result = self._generate_with_retry(EXECUTIVE_SUMMARY_SYSTEM_PROMPT, user_prompt)
        
        if result and len(result) >= 20:
            logger.info(f"[JUSTIFICATION] Generated executive summary: {len(result)} chars")
            return result
        
        # Fallback
        logger.warning("[JUSTIFICATION] Using fallback template for executive summary")
        return self._generate_fallback_summary(recommendation, confidence_score, compliance_summary, risks)

    def generate(
        self, 
        compliance_summary: ComplianceSummary, 
        decision: Dict, 
        risks: List[RiskItem],
        synthesis_report=None  # Optional synthesis report from LLM
    ) -> Tuple[str, str]:
        """
        Generate justification and executive summary.
        
        Args:
            compliance_summary: Aggregated compliance data
            decision: Decision dictionary from DecisionEngine
            risks: List of identified risks
            synthesis_report: Optional synthesis report from evidence synthesizer
            
        Returns:
            Tuple of (justification_text, executive_summary_text)
        """
        logger.info("[JUSTIFICATION] Starting justification generation")
        
        # Extract context
        recommendation = decision.get("recommendation")
        confidence_score = decision.get("confidence_score", 0)
        trace = decision.get("decision_trace", [])
        
        # Build context prompt
        context_prompt = self._build_context_prompt(compliance_summary, decision, risks)
        
        # Append synthesis findings if available
        if synthesis_report:
            synthesis_section = f"""

### Evidence Synthesis
**Overall Assessment:** {synthesis_report.overall_assessment}

**Key Strengths:**
{chr(10).join(f"- {s}" for s in synthesis_report.key_strengths)}

**Key Gaps:**
{chr(10).join(f"- {g}" for g in synthesis_report.key_gaps)}

**Conflicts Identified:**
{chr(10).join(f"- {c}" for c in synthesis_report.conflicts_identified) if synthesis_report.conflicts_identified else "None"}

**Recommended Mitigations:**
{chr(10).join(f"- {m}" for m in synthesis_report.recommended_mitigations)}
"""
            context_prompt += synthesis_section
        
        # Generate Justification
        justification = self.generate_justification(
            context_prompt, recommendation, confidence_score, compliance_summary.mandatory_met
        )
        
        # Generate Executive Summary
        executive_summary = self.generate_executive_summary(
            context_prompt, recommendation, confidence_score, compliance_summary, risks
        )
        
        logger.info(f"[JUSTIFICATION] Complete: justification={len(justification)} chars, summary={len(executive_summary)} chars")
        return justification, executive_summary

