# RFP Bid Agent

An autonomous AI agent for RFP (Request for Proposal) decision support and compliance mapping.

## Overview

This project develops an intelligent agent that:
- Analyzes RFP documents
- Extracts requirements and compliance criteria
- Maps company capabilities against RFP requirements
- Generates compliance and capability assessments
- Supports bid/no-bid decision making

## Features

- **RFP Parsing**: Automatic parsing of RFP documents (PDF, DOCX, etc.)
- **Requirement Extraction**: Intelligent extraction of technical and compliance requirements
- **Capability Mapping**: Maps company capabilities against extracted requirements
- **Compliance Analysis**: Identifies compliance gaps and recommendations
- **Report Generation**: Generates detailed assessment reports

## Project Structure

```
rfp-bid-agent/
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── main.py                      # Entry point
│
├── config/
│   └── settings.py              # Configuration management
│
├── data/
│   ├── knowledge_base/          # Company capability files
│   └── sample_rfps/             # Test RFP documents
│
├── src/
│   ├── __init__.py
│   ├── models/                  # Pydantic data models
│   ├── parsers/                 # RFP parsing
│   ├── extractors/              # Requirement extraction
│   ├── engine/                  # Reasoning engine
│   ├── agent/                   # Main agent logic
│   └── utils/                   # Helper functions
│
└── tests/
    └── test_*.py                # Unit tests
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rfp-bid-agent
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

```bash
python main.py
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/
```

## Configuration

See `.env.example` for all available configuration options.

## Contributing

[Add contribution guidelines here]

## License

[Add license information here]

## Authors

[Add author information here]
