# Phase 3: RFP Analysis Tools & Requirement Processing

## 1. Embedding Strategy
*   **Model**: `text-embedding-3-small` (OpenAI)
*   **Dimension**: 1536
*   **Usage**: Used pervasively for **ALL** semantic vector operations:
    1.  **RFP Requirements**: Every extracted requirement is embedded to allow semantic matching.
    2.  **Knowledge Base**: Company projects, certifications, and technologies are embedded using the same model.
*   **Rationale**: Consistency is critical for dot-product/cosine similarity searches. Using the same model ensures the vector space is aligned. `text-embedding-3-small` was chosen for its balance of performance, cost, and high dimensionality (1536) which captures semantic nuance better than older `ada-002` models.

## 2. Requirement Types
The system classifies extracted text into specific types to drive downstream logic.

| Type | Description | Examples |
| :--- | :--- | :--- |
| **MANDATORY** | Non-negotiable eligibility or legal criteria. Failures here often mean "No-Bid". | - "Bidder must have ISO 27001 certification."<br>- "Solution must be hosted in India."<br>- "Vendor must have 5 years of experience." |
| **TECHNICAL** | Specific technology stack, features, or architectural needs. | - "The system must support Python 3.10."<br>- "Database must be PostgreSQL."<br>- "Must support SAML 2.0 SSO." |
| **PREFERRED** | Desirable but not critical features. Used for scoring but not disqualification. | - "Experience with Government clients is preferred."<br>- "Nice to have mobile app support." |
| **TIMELINE** | Constraints related to time, schedules, or deadlines. | - "Project must be completed within 6 months."<br>- "Go-live required by Jan 1st." |
| **BUDGET** | Financial constraints or pricing requirements. | - "Total budget cap is $500k."<br>- "Pricing must be submitted in separate envelope." |
| **OTHER** | Catch-all for items that don't fit above (e.g., formatting instructions). | - "Submit 3 hard copies." |

### Disambiguation
*   **TECHNICAL vs MANDATORY**: If a technical requirement is phrased as a "must" ("Must use AWS"), it is structurally `MANDATORY` but semantically `TECHNICAL`. The system generally classifies these as `TECHNICAL` if they describe *what* to build, and `MANDATORY` if they verify *who* the bidder is (qualifications). However, strong "must" language often pushes classification to `MANDATORY` or high-priority `TECHNICAL`.

## 3. Tool Workflow

### RFP Parser Tool
**Responsibility**: Convert raw binary files (PDF/DOCX) into clean, human-readable Markdown text.
*   **Input**: File path (string).
*   **Output**: Markdown string.
*   **Process**:
    1.  Detects file extension.
    2.  Selects appropriate parser from `DocumentParserFactory`.
    3.  Cleans extracted text (removes excessive whitespace).

### Requirement Processor Tool
**Responsibility**: Turn unstructured text into structured data.
*   **Input**: Markdown text.
*   **Output**: List of `Requirement` objects.
*   **Process**:
    1.  **Extract**: Uses regex heuristics (`shall`, `must`, `required`) to identify candidate sentences.
    2.  **Classify**: Sends candidates to LLM (GPT-4o-mini) to categorize, assign priority (1-10), and filter noise.
    3.  **Embed**: Generates 1536-dim vectors for each valid requirement using `generate_batch_embeddings`.

## 4. Parser Fallback Chain
To ensure robustness, the system uses a fallback strategy (implemented in `DocumentParserFactory`):

1.  **Primary**: **Docling** (Planned/Optional) - Offers SOTA layout analysis and table extraction.
2.  **Fallback PDF**: **PyPDF** - Used currently as the robust default. Fast and reliable for text, though weak on complex tables.
3.  **Fallback DOCX**: **python-docx** - Native handler for Word documents. Preserves some structure but flattens complex formats.
*   **Strategy**: If the primary parser fails or raises an exception, the factory catches the error and automatically attempts the next parser in the chain, ensuring the agent doesn't crash on a single malformed page.
