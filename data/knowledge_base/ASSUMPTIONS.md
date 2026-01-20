# Assumptions Document - AstraNova Digital Solutions Knowledge Base

> **Purpose:** This document explains the assumptions and decisions made when creating the company knowledge base for the RFP Bid Decision Agent.

---

## 1. Company Profile Assumptions

### Core Data (Directly from Mock Profile)
The following values are taken **directly** from the provided mock company profile:
- **Company Name:** AstraNova Digital Solutions
- **Team Size:** 35 employees
- **Years of Experience:** 6 years
- **Delivery Regions:** North America, Europe, APAC
- **Budget Range:** $20,000 - $250,000 USD
- **Industries Served:** Healthcare, Finance, Retail, Public Sector

### Enhanced/Assumed Values
| Field | Value | Assumption Reasoning |
|-------|-------|---------------------|
| `delivery_regions` | Added "India" | Common for tech consulting firms to have offshore capabilities; mentioned APAC implies potential India presence |
| `current_utilization_percent` | 70% | Typical healthy utilization for consulting firms |
| `available_developers` | 10 (out of 35) | ~30% availability is reasonable given 70% utilization |
| `headquarters` | San Francisco, CA | Assumed US-based given "North America" as primary region |
| `currency` | USD | Standard for US-based tech firms |

---

## 2. Certifications Assumptions

### Directly from Mock Profile
| Certification | Status in Mock | Our Implementation |
|---------------|----------------|-------------------|
| ISO 27001 | "ISO 27001 compliant processes" | **Active** - Assumed formal certification |
| SOC 2 | "SOC 2 readiness" | **Ready** - Not yet formally certified |

### Additional Certifications Added
| Certification | Reasoning |
|---------------|-----------|
| **AWS Partner** | Mock mentions AWS (S3, Lambda, EC2) expertise - partnership is common for consulting firms with cloud expertise |
| **Microsoft Azure Partner** | Mock mentions Azure in cloud capabilities |
| **GDPR Compliance** | Mock states "GDPR-aware designs" - formalized as certification for EU client work |
| **ISO 9001** | Common quality management certification for software development firms |
| **HIPAA Readiness** | Mock serves Healthcare industry - HIPAA readiness is essential |

### Validity Date Assumptions
- Certifications typically valid for **3 years**
- Dates set between 2021-2025 to reflect realistic timelines
- Some certifications marked as "ready" (SOC 2, HIPAA) - internal processes complete but formal audit pending

---

## 3. Tech Stack Assumptions

### Directly from Mock Profile
All technologies listed in the mock are included with appropriate proficiency levels:

| Category | Technologies from Mock | Included |
|----------|----------------------|----------|
| Languages | Python, Java, SQL | ✅ All included |
| AI & ML | OpenAI APIs, spaCy, HuggingFace, LangChain, CrewAI | ✅ All included |
| Cloud & DevOps | AWS (S3, Lambda, EC2), Docker, GitHub Actions | ✅ All included |
| Databases | PostgreSQL, FAISS, Pinecone | ✅ All included |

### Proficiency Level Assumptions
| Proficiency | Definition | Assignment Criteria |
|-------------|------------|-------------------|
| **Expert** | 5+ years experience, multiple production deployments, can lead projects | Primary technologies: Python, SQL, PostgreSQL, spaCy |
| **Advanced** | 3-5 years, production experience, independent work | Secondary technologies: Java, HuggingFace, AWS |
| **Intermediate** | 1-3 years, guided production work | Newer technologies: CrewAI, GCP |
| **Beginner** | < 1 year, learning/POC stage | None in current stack |

### Additional Technologies Added
| Technology | Reasoning |
|------------|-----------|
| **Azure** | Mock mentions cloud-native architectures with Azure |
| **GCP (intermediate)** | Added for completeness, lower proficiency reflects focus on AWS/Azure |
| **MongoDB, Redis** | Common in modern tech stacks for document storage and caching |
| **Elasticsearch** | Standard for search functionality |
| **FastAPI, Django** | Python web frameworks implied by backend development |
| **React** | Frontend capability implied by full-stack development |

---

## 4. Strategic Preferences Assumptions

### Industry Priority Assignment
| Industry | Priority | Reasoning |
|----------|----------|-----------|
| Healthcare | **High** | Listed first in mock, HIPAA readiness indicates focus |
| Finance | **High** | High-value projects, compliance expertise aligns well |
| Public Sector | **Medium** | Mentioned in mock, but typically longer sales cycles |
| Retail | **Medium** | Listed in mock, growing AI adoption market |
| Manufacturing | **Low** | Not mentioned in mock - limited expertise assumed |

### Bid Threshold Assumptions
| Threshold | Value | Reasoning |
|-----------|-------|-----------|
| Min Budget | $20,000 | Matches mock's minimum |
| Max Budget | $250,000 | Matches mock's maximum |
| Ideal Range | $50K-$150K | Sweet spot for mid-sized firm profitability |
| Max Team Allocation | 40% | Prevents over-commitment to single project |
| Min Profit Margin | 20% | Standard for consulting industry |

### Decision Weights
| Factor | Weight | Reasoning |
|--------|--------|-----------|
| Technical Fit | 30% | Most important - can we deliver? |
| Strategic Alignment | 25% | Does it match our goals? |
| Financial Viability | 20% | Is it profitable? |
| Timeline Feasibility | 15% | Can we deliver on time? |
| Risk Assessment | 10% | What could go wrong? |

---

## 5. Project Portfolio Assumptions

### Project Selection Criteria
- **15 projects** created to provide meaningful sample size
- All projects use technologies from the tech stack
- Budget range: $45,000 - $200,000 (within company capacity)
- Duration: 3-8 months (realistic enterprise project timelines)
- Industries: All 4 from mock profile represented

### Project Outcome Distribution
| Outcome | Count | Percentage | Reasoning |
|---------|-------|------------|-----------|
| Success | 14 | 93% | High success rate reflects competent firm |
| Partial Success | 1 | 7% | Realistic - not every project is perfect |
| Failure | 0 | 0% | Would indicate serious issues if present |

### Industry Distribution
| Industry | Projects | Reasoning |
|----------|----------|-----------|
| Finance | 6 | Primary focus area with compliance expertise |
| Healthcare | 3 | Growing focus area |
| Retail | 4 | Steady work in automation and analytics |
| Public Sector | 2 | Fewer but larger/stable contracts |

### Technology Usage Distribution
Most frequently used technologies across projects:
1. Python (15/15 projects) - Core language
2. PostgreSQL (14/15) - Primary database
3. AWS (10/15) - Primary cloud
4. FastAPI (8/15) - Preferred API framework
5. OpenAI APIs / LangChain (8/15) - AI projects

---

## 6. General Assumptions

### Business Context
- Company operates as a **consulting/services firm**, not a product company
- Primary engagement model is **project-based** work
- Clients are typically **mid-market to enterprise** sized organizations
- Company prefers **long-term partnerships** over one-off projects

### Operational Assumptions
- Team works in a **hybrid/remote** model
- Standard working hours aligned with **US timezone** primarily
- Uses **agile/scrum** methodologies for project delivery
- Has established **security and compliance** processes

### Data Freshness
- All data represents the company state as of **January 2026**
- Project portfolio includes projects from **2023-2024**
- Certifications have realistic validity periods

---

## 7. Limitations & Caveats

### What This Data Does NOT Include
- Actual client names (anonymized as industry + type)
- Real financial statements or revenue figures
- Specific employee names or org structure
- Proprietary methodologies or processes

### Known Simplifications
- Proficiency levels are simplified (4 tiers vs. continuous scale)
- Project outcomes are binary (success/partial) vs. nuanced metrics
- Certification scope is generalized

---

## 8. How This Data Will Be Used

The knowledge base will be used by the RFP Bid Decision Agent to:

1. **Check certification compliance** - Does the company have required certs?
2. **Validate technical capability** - Can we deliver the required technologies?
3. **Assess budget feasibility** - Is the project within our capacity?
4. **Evaluate strategic fit** - Does this align with our priorities?
5. **Find similar past projects** - Have we done this before?

---

*Last updated: 2026-01-20*
*Created by: RFP Bid Decision Agent Development Team*
