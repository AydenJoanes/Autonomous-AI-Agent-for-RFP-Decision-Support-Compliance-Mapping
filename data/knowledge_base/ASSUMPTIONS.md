# Assumptions Document - AstraNova Digital Solutions Knowledge Base

> **Purpose:** This document explains the assumptions and decisions made when creating the company knowledge base for the RFP Bid Decision Agent. It makes all implicit judgments explicit to ensure transparent, defensible, and risk-aware bid decisions.

---

## 1. Company Profile Assumptions

### Core Data (Directly from Mock Profile)

The following values are taken **directly** from the provided mock company profile:

* **Company Name:** AstraNova Digital Solutions
* **Team Size:** 35 employees
* **Years of Experience:** 6 years
* **Delivery Regions:** North America, Europe, APAC
* **Budget Range:** $20,000 - $250,000 USD
* **Industries Served:** Healthcare, Finance, Retail, Public Sector

### Enhanced / Assumed Values

| Field                         | Value             | Assumption Reasoning                                                              |
| ----------------------------- | ----------------- | --------------------------------------------------------------------------------- |
| `delivery_regions`            | Added **India**   | APAC coverage and cost structure imply offshore or near-shore delivery capability |
| `current_utilization_percent` | 70%               | Typical healthy utilization for consulting firms                                  |
| `available_developers`        | 10 (out of 35)    | ~30% availability aligns with utilization assumption                              |
| `headquarters`                | San Francisco, CA | Assumed US-based due to North America being a primary market                      |
| `currency`                    | USD               | Standard for US-based consulting firms                                            |

---

## 2. Certifications Assumptions

### Directly from Mock Profile

| Certification | Status in Mock                  | Interpretation                        |
| ------------- | ------------------------------- | ------------------------------------- |
| ISO 27001     | “ISO 27001 compliant processes” | Treated as **active certification**   |
| SOC 2         | “SOC 2 readiness”               | **Ready**, not yet formally certified |

### Additional Certifications Added (Assumed)

| Certification           | Reasoning                                              |
| ----------------------- | ------------------------------------------------------ |
| AWS Partner             | Extensive AWS usage implies partner status             |
| Microsoft Azure Partner | Azure explicitly mentioned in cloud capabilities       |
| GDPR Compliance         | Required for EU clients; formalized compliance posture |
| ISO 9001                | Common quality standard for software consulting firms  |
| HIPAA Readiness         | Necessary for healthcare analytics and AI systems      |

### Validity Assumptions

* Certifications assumed valid for **3 years**
* Dates span **2021–2025** for realism
* “Ready” certifications indicate internal controls exist but audits may be pending

**Healthcare Caveat:**
Healthcare compliance reflects **analytics, automation, and decision-support systems**, not direct clinical systems, claims adjudication engines, or regulated medical devices.

---

## 3. Tech Stack Assumptions

### Directly from Mock Profile

All technologies listed in the mock profile are included:

| Category       | Technologies                                       |
| -------------- | -------------------------------------------------- |
| Languages      | Python, Java, SQL                                  |
| AI & ML        | OpenAI APIs, spaCy, HuggingFace, LangChain, CrewAI |
| Cloud & DevOps | AWS (S3, Lambda, EC2), Docker, GitHub Actions      |
| Databases      | PostgreSQL, FAISS, Pinecone                        |

### Proficiency Levels

| Level            | Definition                                |
| ---------------- | ----------------------------------------- |
| **Expert**       | 5+ years, multiple production deployments |
| **Advanced**     | 3–5 years, independent production work    |
| **Intermediate** | 1–3 years, guided production experience   |
| **Beginner**     | <1 year, experimentation only (not used)  |

### Additional Technologies (Assumed)

| Technology         | Reasoning                                |
| ------------------ | ---------------------------------------- |
| Azure              | Explicitly mentioned in mock             |
| GCP (Intermediate) | Limited exposure; not a primary platform |
| MongoDB, Redis     | Common supporting data stores            |
| Elasticsearch      | Search and analytics use cases           |
| FastAPI, Django    | Python backend development               |
| React              | Full-stack delivery capability           |

---

## 4. Strategic Preferences Assumptions

### Industry Priorities

| Industry      | Priority | Rationale                                                |
| ------------- | -------- | -------------------------------------------------------- |
| Healthcare    | High     | Strategic focus with compliance readiness                |
| Finance       | High     | High-value, compliance-aligned projects                  |
| Public Sector | Medium   | Strong technical fit, longer sales and compliance cycles |
| Retail        | Medium   | Steady analytics and automation demand                   |
| Manufacturing | Low      | Not a core focus area                                    |

**Public Sector Note:**
Government projects may require additional eligibility criteria, local presence, or long-term on-site commitments. Such cases should trigger **escalation or conditional bidding**, not automatic rejection.

### Bid Thresholds

| Parameter             | Value            |
| --------------------- | ---------------- |
| Minimum Budget        | $20,000          |
| Maximum Budget        | $250,000         |
| Ideal Budget Range    | $50,000–$150,000 |
| Max Team Allocation   | 40%              |
| Minimum Profit Margin | 20%              |

### Decision Weights

| Factor               | Weight |
| -------------------- | ------ |
| Technical Fit        | 30%    |
| Strategic Alignment  | 25%    |
| Financial Viability  | 20%    |
| Timeline Feasibility | 15%    |
| Risk Assessment      | 10%    |

---

## 5. Project Portfolio Assumptions

### Portfolio Construction

* **15 total projects** to support meaningful similarity search
* Budget range: **$45,000–$200,000**
* Duration: **3–8 months**
* All projects use technologies from the defined tech stack

### Outcome Distribution

| Outcome         | Count | Rationale                                          |
| --------------- | ----- | -------------------------------------------------- |
| Success         | 13    | Reflects strong delivery capability                |
| Partial Success | 2     | Acknowledges real-world complexity                 |
| Failure         | 0     | Failures omitted to avoid implying systemic issues |

### Industry Distribution

| Industry      | Projects |
| ------------- | -------- |
| Finance       | 6        |
| Healthcare    | 3        |
| Retail        | 4        |
| Public Sector | 2        |

### Common Technology Usage

1. Python (15/15)
2. PostgreSQL (14/15)
3. AWS (10/15)
4. FastAPI (8/15)
5. OpenAI APIs / LangChain (8/15)

---

## 6. General Assumptions

### Business Context

* Consulting and services firm (not product-led)
* Project-based engagement model
* Mid-market to enterprise clients
* Preference for long-term partnerships

### Operational Context

* Hybrid / remote delivery model
* US time zone as primary coordination window
* Agile / Scrum-based execution
* Mature security and compliance practices

### Data Freshness

* Snapshot as of **January 2026**
* Portfolio projects from **2023–2024**
* Certification dates reflect realistic renewal cycles

---

## 7. Limitations & Explicit Non-Coverage

### Not Included

* Real client names
* Financial statements
* Employee-level data
* Proprietary methodologies

### Explicit Non-Focus Areas

* Large-scale **training delivery**
* Instructional design or pedagogy-heavy work
* Logistics-driven programs requiring physical classroom operations

### Simplifications

* Discrete proficiency tiers
* Simplified project outcome metrics
* Generalized certification scopes

---

## 8. Intended Use by the RFP Agent

This knowledge base is used to:

1. Verify certification and compliance requirements
2. Assess technical and domain capability
3. Evaluate budget and resourcing feasibility
4. Check strategic alignment
5. Identify similar past work for confidence scoring

---

*Last updated: 2026-01-20*
*Owner: AstraNova RFP Decision Agent Team*
