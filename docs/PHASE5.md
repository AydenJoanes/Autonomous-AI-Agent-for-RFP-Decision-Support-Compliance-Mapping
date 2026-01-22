# Phase 5: Recommendation Generator

## 1. Overview

### Objectives
- Build decision engine consuming Phase 4 tool outputs
- Generate Bid/No-Bid recommendations with confidence scores
- Provide natural language justifications
- Identify and highlight risks

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  RecommendationAgent                        │
│                         │                                   │
│                         ▼                                   │
│              RecommendationService                          │
│     ┌───────────┬───────────┬───────────┐                  │
│     ▼           ▼           ▼           ▼                  │
│ RFPParser  ToolExecutor  DecisionEngine  Justification     │
│     │           │           │           Generator          │
│     ▼           ▼           ▼                              │
│  Markdown   6 Tools    Confidence    LLM/Fallback          │
│             Results      Score                              │
└─────────────────────────────────────────────────────────────┘
```

## 2. Key Design Decisions

### RecommendationDecision Values
| Value | When Used |
|-------|-----------|
| `BID` | Confidence ≥75, no mandatory failures |
| `NO_BID` | Mandatory failed OR NON_COMPLIANT OR confidence <50 |
| `CONDITIONAL_BID` | Medium confidence (50-74), UNKNOWN-heavy, warnings |

### UNKNOWN Handling Policy
- UNKNOWN never auto-triggers NO_BID
- UNKNOWN on mandatory → CONDITIONAL_BID + human review
- UNKNOWN reduces confidence but doesn't force rejection

### Confidence Score
- Heuristic estimate, not probabilistic guarantee
- Configurable base scores and penalties
- Capped penalties prevent extreme collapse

## 3. Configuration

All constants in `src/app/services/decision_config.py`:

| Constant | Value | Purpose |
|----------|-------|---------|
| CONFIDENCE_BASE_SCORES[COMPLIANT] | 85 | Base for compliant |
| CONFIDENCE_BASE_SCORES[PARTIAL] | 60 | Base for partial |
| MANDATORY_MET_BONUS | 10 | Bonus when all mandatory met |
| MANDATORY_FAILED_PENALTY | 15 | Penalty for mandatory fail |
| MAX_PENALTY_CAP | 40 | Maximum total penalty |
| BID_CONFIDENCE_THRESHOLD | 75 | Min for BID |
| CONDITIONAL_CONFIDENCE_THRESHOLD | 50 | Min for CONDITIONAL |

## 4. Models

### RecommendationDecision
```python
class RecommendationDecision(str, Enum):
    BID = "BID"
    NO_BID = "NO_BID"
    CONDITIONAL_BID = "CONDITIONAL_BID"
```

### Recommendation
```python
class Recommendation(BaseModel):
    recommendation: RecommendationDecision
    confidence_score: int  # 0-100
    justification: str     # min 50 chars
    executive_summary: str # min 20 chars
    risks: List[RiskItem]
    compliance_summary: ComplianceSummary
    requires_human_review: bool
    review_reasons: List[str]
    rfp_metadata: RFPMetadata
    timestamp: datetime
```

## 5. Services

### DecisionEngine
- `calculate_confidence_score()` - Computes 0-100 score
- `determine_recommendation()` - Returns BID/NO_BID/CONDITIONAL
- `determine_human_review()` - Checks review triggers

### JustificationGenerator
- `generate()` - Produces (justification, summary) tuple
- Uses LLM with fallback templates

## 6. Decision Logic

### Confidence Formula
```
score = base_score 
      + mandatory_adjustment 
      + (confidence_avg - 0.7) * 20 
      - min(penalties, MAX_CAP)
```

### Decision Matrix
```
mandatory_failed? → NO_BID
overall = NON_COMPLIANT? → NO_BID
confidence ≥ 75 AND (COMPLIANT|PARTIAL)? → BID
confidence ≥ 50? → CONDITIONAL_BID
mandatory_unknown? → CONDITIONAL_BID
else → NO_BID
```

## 7. API Reference

### POST /api/v1/recommendation/analyze
**Request:**
```json
{"file_path": "/path/to/rfp.pdf"}
```
**Response:** Recommendation object

### GET /api/v1/recommendation/health
**Response:**
```json
{"status": "ok", "tools_available": 6, "service_ready": true}
```

## 8. Usage Examples

```python
from src.app.agent.recommendation_agent import RecommendationAgent

agent = RecommendationAgent()
recommendation, report = agent.run_with_report("path/to/rfp.pdf")

print(f"Decision: {recommendation.recommendation}")
print(f"Confidence: {recommendation.confidence_score}%")
```

## 9. Known Limitations

1. Single-tool routing per requirement
2. Heuristic confidence (not probabilistic)
3. LLM dependency for justifications
4. Embedding dimension must be 1536

## 10. Future Enhancements (Phase 6+)

- Multi-tool routing for complex requirements
- Autonomous behaviors and self-improvement
- Memory/learning from past decisions
