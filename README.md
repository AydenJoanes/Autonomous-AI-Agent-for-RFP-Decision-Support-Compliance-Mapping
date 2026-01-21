# Autonomous AI Agent for RFP Decision Support & Compliance Mapping

An intelligent, autonomous AI agent designed to streamline the Request for Proposal (RFP) process. This system leverages Large Language Models (LLMs), Vector Search, and Agentic workflows to analyze RFP documents, extract requirements, map them to company capabilities, and provide data-driven bid/no-bid decisions.

![Status](https://img.shields.io/badge/Status-Development-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-teal)

## 🚀 Key Features

*   **Intelligent RFP Parsing**:
    *   Unified parsing for **PDF** and **DOCX** files via `DocumentParserFactory`.
    *   Handles complex layouts, tables, and mixed content.
*   **Requirement Analysis Engine**:
    *   **Automated Extraction**: Identifies potential requirements using regex heuristics and NLP.
    *   **AI Classification**: Uses GPT-4o-mini to categorize requirements (Mandatory, Technical, Timeline, Budget) and assign priority scores (1-10).
    *   **Semantic Understanding**: Generates 1536-dimensional embeddings (OpenAI `text-embedding-3-small`) for deep semantic search.
*   **Knowledge Base Integration**:
    *   Vector-based retrieval of company capabilities (Tech Stack, Certifications, Project Portfolio).
    *   Strategic alignment checking against company preferences.
*   **Agentic Decision Support**:
    *   Calculates compliance scores and fit gaps.
    *   Provides actionable Bid/No-Bid recommendations with reasoning.

## 🏗️ Architecture

The system follows a modular architecture:

1.  **Ingestion Layer**: `RFPParserTool` converts raw documents into clean Markdown.
2.  **Processing Layer**: `RequirementProcessorTool` transforms text into structured `Requirement` objects with metadata and embeddings.
3.  **Knowledge Layer**: PostgreSQL + `pgvector` stores the Company Knowledge Base (Projects, Certs, Tech) and historical RFP data.
4.  **Reasoning Layer**: The Agent Orchestrator (LangGraph/LangChain) plans execution, queries the KB, and synthesizes the final report.

## 📂 Project Structure

```bash
rfp-bid-agent/
├── config/                  # Configuration settings (Env vars)
├── data/
│   └── knowledge_base/      # JSON source files for Company capabilities
├── scripts/                 # Utility scripts (DB setup, Data loading, verification)
├── src/
│   └── app/
│       ├── agent/           # Agent Logic & Tools
│       │   └── tools/       # RFPParserTool, RequirementProcessorTool
│       ├── api/             # FastAPI Routes (Health, etc.)
│       ├── database/        # SQLAlchemy Models & Connection logic
│       ├── models/          # Pydantic schema definitions
│       ├── services/        # Core services (e.g., DocumentParserFactory)
│       └── utils/           # Shared utilities (Embeddings, Logging)
├── tests/                   # Automated test suites
└── main.py                  # Application entry point
```

## 🛠️ Installation & Setup

### Prerequisites
*   Python 3.10 or higher
*   PostgreSQL 14+ (with `pgvector` extension support)
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

### 4. Verification
Run the verification scripts to ensure everything is working:

```bash
# Verify Phase 2 (DB & Data)
python scripts/verify_phase2.py

# Check Agent Tools
python tests/test_rfp_tools.py
```

## 📖 Usage

### Running the API
Start the FastAPI backend:
```bash
python main.py
```
Health check available at: `http://localhost:8000/health`

### Using the Tools (Programmatic)
You can import and use the tools directly in your scripts:

```python
from src.app.agent.tools.rfp_parser_tool import RFPParserTool
from src.app.agent.tools.requirement_processor_tool import RequirementProcessorTool

# 1. Parse an RFP
parser = RFPParserTool()
text = parser._run("path/to/rfp.pdf")

# 2. Process Requirements
processor = RequirementProcessorTool()
requirements = processor._run(text)

print(f"Found {len(requirements)} requirements")
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

## 📄 License
[Add License Information]
