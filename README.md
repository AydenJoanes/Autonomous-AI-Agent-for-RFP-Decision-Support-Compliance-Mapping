# Autonomous AI Agent for RFP Decision Support & Compliance Mapping

An intelligent, autonomous AI agent designed to streamline the Request for Proposal (RFP) process. This system leverages Large Language Models (LLMs), Vector Search, and Agentic workflows to analyze RFP documents, extract requirements, map them to company capabilities, and provide data-driven bid/no-bid decisions.

**Crucially, this agent features a "Continuous Learning" loop (Phase 6), allowing it to record real-world outcomes, reflect on its decisions, and improve future recommendations via vector-based memory.**

![Status](https://img.shields.io/badge/Status-Development-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-teal)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-blue)
![pgvector](https://img.shields.io/badge/pgvector-Enabled-orange)

## 🚀 Key Features

*   **Intelligent RFP Parsing**:
    *   Unified parsing for **PDF** and **DOCX** files via `DocumentParserFactory`.
    *   Handles complex layouts, tables, and mixed content.
*   **Requirement Analysis Engine**:
    *   **Automated Extraction**: Identifies potential requirements using regex heuristics and NLP.
    *   **AI Classification**: Uses GPT-4o-mini to categorize requirements (Mandatory, Technical, Timeline, Budget) and assign priority scores (1-10).
*   **Knowledge Base Integration**:
    *   Vector-based retrieval of company capabilities (Tech Stack, Certifications, Project Portfolio) using `pgvector`.
    *   Strategic alignment checking against company preferences.
*   **Agentic Decision Support**:
    *   Calculates compliance scores and fit gaps.
    *   Provides actionable Bid/No-Bid recommendations with reasoning and confidence scores.
*   **Continuous Learning (Phase 6)**:
    *   **Outcome Recording**: Record real-world "Win/Loss" outcomes for recommendations.
    *   **Reflection Engine**: The agent reflects on its logic after a decision is finalized, identifying potential biases or missed risks.
    *   **Memory Embedding**: Decisions are embedded and stored to inform future similarity searches (RAG on past decisions).

## 🏗️ Architecture

The system follows a modular architecture:

1.  **Ingestion Layer**: `RFPParserTool` converts raw documents into clean Markdown.
2.  **Processing Layer**: `RequirementProcessorTool` transforms text into structured `Requirement` objects with metadata.
3.  **Knowledge Layer**: PostgreSQL + `pgvector` stores the Company Knowledge Base and historical RFP decisions (Memory).
4.  **Reasoning Layer**: The Agent Orchestrator plans execution, queries the KB, and synthesizes the final report.
5.  **Learning Layer (Phase 6)**: `Phase6Orchestrator` handles post-decision reflection and outcome recording to close the feedback loop.

## 📂 Project Structure

```bash
rfp-bid-agent/
├── config/                  # Configuration settings (Env vars)
├── data/                    # JSON source files for Knowledge Base
├── docs/                    # Project documentation (Phase details, etc.)
├── frontend/                # Simple HTML/JS frontend for testing
├── migrations/              # Alembic database migrations
├── scripts/                 # Utility scripts (DB setup, Data loading, verification)
│   ├── init_db.py           # Initializes DB tables
│   ├── load_knowledge_base.py # Loads company data into Vector DB
│   └── verify_high_confi.py # End-to-end verification script
├── src/
│   └── app/
│       ├── agent/           # Agent Logic & Tools
│       ├── api/
│       │   └── routes/      # FastAPI Routes (Health, Recommendation, Outcomes)
│       ├── database/        # SQLAlchemy Models & Connection logic
│       ├── models/          # Pydantic schema definitions
│       ├── services/        # Core services (RecommendationService, Phase6Orchestrator)
│       └── strategies/      # Compliance & Scoring strategies
├── tests/                   # Automated test suites
└── main.py                  # Application entry point
```

## 🛠️ Installation & Setup

### Prerequisites
*   Python 3.10 or higher
*   PostgreSQL 14+ (with `pgvector` extension installed)
*   OpenAI API Key

### 1. Clone & Install
```bash
git clone <repository-url>
cd rfp-bid-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Copy the template and update with your credentials:
```bash
cp .env.example .env
```
Ensure `.env` contains:
```ini
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/rfp_bid_db
OPENAI_API_KEY=sk-proj-...
EMBEDDING_MODEL=text-embedding-3-small
```

### 3. Database Initialization
Use the provided scripts to set up the schema and load the Knowledge Base:

```bash
# Initialize Schema (Tables & Indexes)
python scripts/setup_database.py

# Load Knowledge Base (JSONs -> DB + Embeddings)
python scripts/load_knowledge_base.py
```

## 📖 Usage

### Running the API
Start the FastAPI backend:
```bash
python main.py
```
*   **API Docs**: `http://localhost:8000/docs`
*   **Frontend**: `http://localhost:8000`
*   **Health Check**: `http://localhost:8000/api/v1/health`

### Key Endpoints

1.  **Analyze RFP**: `POST /api/v1/recommendation/analyze`
    *   Upload an RFP file (PDF/DOCX) to get a comprehensive Bid/No-Bid analysis.
2.  **Record Outcome**: `POST /api/v1/outcomes/record`
    *   Submit the real-world result (WON/LOST) for a past recommendation ID. This triggers the learning loop.

### Using the Tools (Programmatic)

```python
from src.app.services.recommendation_service import RecommendationService

service = RecommendationService()
# Run analysis on a file
result = await service.analyze_rfp_file("path/to/rfp.docx")
print(result.decision) # "BID" or "NO_BID"
```

## 🧪 Testing

Run the full test suite with `pytest`:
```bash
pytest tests/
```

## 🤝 Contributing
1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'feat: Add amazing feature'`).
4.  Push to the branch.
5.  Open a Pull Request.
