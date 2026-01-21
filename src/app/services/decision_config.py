"""
Decision Engine Configuration Module
Centralized constants for recommendation logic and confidence scoring.
"""

from src.app.models.compliance import ComplianceLevel

# ============================================================================
# CONFIDENCE BASE SCORES
# ============================================================================

CONFIDENCE_BASE_SCORES = {
    ComplianceLevel.COMPLIANT: 85,
    ComplianceLevel.PARTIAL: 60,
    ComplianceLevel.WARNING: 50,
    ComplianceLevel.UNKNOWN: 40,
    ComplianceLevel.NON_COMPLIANT: 20,
}

# ============================================================================
# ADJUSTMENT CONSTANTS
# ============================================================================

# Mandatory requirement adjustments
MANDATORY_MET_BONUS = 10
MANDATORY_FAILED_PENALTY = 15

# Confidence average adjustments
CONFIDENCE_AVG_MULTIPLIER = 20
CONFIDENCE_AVG_BASELINE = 0.7

# ============================================================================
# PENALTY CONSTANTS
# ============================================================================

NON_COMPLIANT_PENALTY = 5
WARNING_PENALTY = 2
UNKNOWN_PENALTY = 3
MAX_PENALTY_CAP = 40

# ============================================================================
# THRESHOLD CONSTANTS
# ============================================================================

# Decision thresholds
BID_CONFIDENCE_THRESHOLD = 75
CONDITIONAL_CONFIDENCE_THRESHOLD = 50
UNKNOWN_HEAVY_THRESHOLD = 0.5  # >50% unknown triggers CONDITIONAL

# ============================================================================
# HUMAN REVIEW CONSTANTS
# ============================================================================

BORDERLINE_CONFIDENCE_LOW = 40
BORDERLINE_CONFIDENCE_HIGH = 60
HIGH_RISK_COUNT_THRESHOLD = 2

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

JUSTIFICATION_MODEL = "gpt-4o-mini"
JUSTIFICATION_TEMPERATURE = 0.3
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0
