# Phase 4 Implementation Documentation

## 1. Overview
The goal of Phase 4 is to build the Reasoning Engine for the RFP Agent. This involves implementing standardized compliance types, a suite of specialized reasoning tools, and a centralized strategy for aggregating their results into a final compliance assessment.

**Architecture:**
- **Models**: Standardized `ComplianceLevel` enum and `ToolResult` class.
- **Tools**: 6 specialized tools (LangChain compatible) for analyzing different aspects of an RFP.
- **Strategy**: A logic layer (`compliance_strategy.py`) to map tool outputs to compliance levels and aggregate them.
- **Integration**: A unified `tools` package exporting all components for the Agent Orchestrator (Phase 5).

## 2. ComplianceLevel Enum
Standardized assessment levels used across all tools.

| Level | Description |
|---|---|
| `COMPLIANT` | Fully meets the requirement. Positive evidence found. |
| `NON_COMPLIANT` | Explicitly fails the requirement. |
| `PARTIAL` | Partially meets the requirement, or meets it with significant caveats (e.g., lower proficiency). |
| `WARNING` | Meets requirements but risks exist (e.g., expiring certs, tight timeline, stale data). |
| `UNKNOWN` | Sufficient data not found to make a determination. |

**Code Example:**
```python
from src.app.models.compliance import ComplianceLevel
level = ComplianceLevel.COMPLIANT
```

## 3. ToolResult Standard Format
Every reasoning tool returns a JSON string representation of this Pydantic model.

| Field | Type | Description |
|---|---|---|
| `tool_name` | `str` | Name of the tool (e.g., "tech_validator"). |
| `requirement` | `str` | Original text being analyzed. |
| `status` | `str` | Tool-specific raw status (e.g., "AVAILABLE", "EXPIRED"). |
| `compliance_level` | `ComplianceLevel` | Standardized enum value. |
| `confidence` | `float` | 0.0 to 1.0 score indicating certainty. |
| `details` | `dict` | Evidence, metadata, contexts (e.g., `{"proficiency": "expert"}`). |
| `risks` | `List[str]` | Specific risks identified. |
| `message` | `str` | Human-readable explanation. |

## 4. Reasoning Tools Reference

### 1. Certification Checker
- **Class**: `CertificationCheckerTool`
- **Purpose**: Verifies company certifications against requirements.
- **Status Mappings**:
    - `VALID` → `COMPLIANT`
    - `EXPIRING_SOON` → `WARNING`
    - `EXPIRED` → `NON_COMPLIANT`
    - `PENDING` → `PARTIAL`
    - `NOT_FOUND` → `UNKNOWN`

### 2. Tech Validator
- **Class**: `TechValidatorTool`
- **Purpose**: Checks meaningful technical capability and proficiency.
- **Status Mappings**:
    - `AVAILABLE` (Expert/Advanced) → `COMPLIANT`
    - `AVAILABLE` (Intermediate/Beginner) → `PARTIAL`
    - `STALE` → `WARNING`
    - `NOT_IN_DATABASE` → `UNKNOWN`

### 3. Budget Analyzer
- **Class**: `BudgetAnalyzerTool`
- **Purpose**: Assesses financial feasibility.
- **Status Mappings**:
    - `ACCEPTABLE` / `LOW_END` → `COMPLIANT`
    - `HIGH_END` / `BELOW_MINIMUM` → `WARNING`
    - `EXCEEDS_MAXIMUM` → `NON_COMPLIANT`

### 4. Timeline Assessor
- **Class**: `TimelineAssessorTool`
- **Purpose**: Evaluates delivery timeline feasibility.
- **Status Mappings**:
    - `FEASIBLE` / `CONSERVATIVE` → `COMPLIANT`
    - `TIGHT` / `AGGRESSIVE` → `WARNING`
    - `UNREALISTIC` → `NON_COMPLIANT`
    - `NO_HISTORICAL_DATA` → `UNKNOWN`

### 5. Strategy Evaluator
- **Class**: `StrategyEvaluatorTool`
- **Purpose**: Checks alignment with strategic goals.
- **Status Mappings**:
    - `STRONG_ALIGNMENT` → `COMPLIANT`
    - `MODERATE_ALIGNMENT` → `PARTIAL`
    - `WEAK_ALIGNMENT` → `WARNING`
    - `MISALIGNMENT` → `NON_COMPLIANT`

### 6. Knowledge Query
- **Class**: `KnowledgeQueryTool`
- **Purpose**: Semantic search of past projects for evidence.
- **Handling**: Sets `compliance_level` directly based on project outcomes (Success vs Failure).
- **Fallback**: Returns `UNKNOWN` if no data.

## 5. Compliance Strategy
Located in `src/app/strategies/compliance_strategy.py`.

### Aggregation Logic (`aggregate_compliance`)
Determines the overall compliance for a requirement based on multiple tool results.

**Priority Rules:**
1. **Mandatory Failure**: If ANY mandatory tool returns `NON_COMPLIANT` → **`NON_COMPLIANT`**.
2. **Mandatory Unknown**: If ANY mandatory tool returns `UNKNOWN` → **`UNKNOWN`**.
3. **Explicit Failure**: If ANY tool is `NON_COMPLIANT` → **`NON_COMPLIANT`**.
4. **All Clear**: If ALL tools are `COMPLIANT` → **`COMPLIANT`**.
5. **Warnings**: If risks exist (`WARNING`) but no failures → **`WARNING`**.
6. **Partial**: Validation found `PARTIAL` evidence → **`PARTIAL`**.
7. **Unknown**: Default if insufficient data.

## 6. UNKNOWN Handling
`UNKNOWN` does NOT mean non-compliant. It means the system lacks specific data to verify.
- Agents should NOT disqualify based on `UNKNOWN` alone unless it's a critical mandatory requirement where "Silence is Rejection".
- Aggregation treats widespread `UNKNOWN` cautiously.

## 7. Integration Notes for Phase 5 (Orchestration)
Import tools from the central registry:

```python
from src.app.agent.tools import REASONING_TOOLS, TOOL_REGISTRY

# Initialize Agent
agent = create_react_agent(llm, tools=REASONING_TOOLS)
```

**Workflow:**
1. **Parser** extracts requirements.
2. **Orchestrator** selects relevant tools for each requirement.
3. **Tools** execute and return JSON `ToolResult`.
4. **Strategy** aggregates results.
5. **Generator** produces Bid/No-Bid recommendation.

## 8. Testing
- **Compliance Unit Tests**: `python scripts/test_compliance_strategy.py`
- **Integration Tests**: `python scripts/test_tools_integration.py`
