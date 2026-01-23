## **Assignment Title**

**Autonomous AI Agent for RFP Decision Support & Compliance Mapping**

---

## **Assignment Overview**

Instead of generating RFPs or extracting basic entities, this assignment focuses on building an **AI agent that helps decide whether an organization should bid on an RFP** and **checks compliance against internal capabilities**.

The agent acts like a **pre-sales analyst**.

---

## **Core Idea**

When an RFP arrives, companies must quickly answer:

* Should we bid?  
* Are we compliant?  
* What are the risks?  
* What sections need human attention?

Your task is to build an **AI Agent that reads an RFP and produces a Bid/No-Bid recommendation with justification**.

---

## **Functional Requirements**

### **Task 1: Internal Capability Knowledge Base**

Create a structured **internal company profile** (mock data).

Example:

{"company\_name": "NextGen AI Solutions","expertise": \["AI", "NLP", "RPA", "Cloud"\],"certifications": \["ISO 27001", "SOC 2"\],"max\_budget\_capacity": 100000,"delivery\_regions": \["US", "Europe"\],"team\_size": 20 }

**Deliverable:**

* JSON or YAML capability profile  
* Explanation of assumptions

---

### **Task 2: RFP Requirement Decomposition**

Instead of simple entity extraction, decompose the RFP into **atomic requirements**:

Examples:

* Mandatory certifications  
* Required technologies  
* Budget constraints  
* Location constraints  
* Timeline constraints

**Output Format:**

\[{"requirement": "ISO 27001 certification","type": "mandatory"},{"requirement": "Project delivery within 3 months","type": "timeline"} \]  
---

### **Task 3: AI Agent Reasoning Engine**

Design an AI agent that:

1. Reads the decomposed RFP requirements  
2. Compares them against the internal capability profile  
3. Assigns:  
   * ✅ Fully Compliant  
   * ⚠️ Partially Compliant  
   * ❌ Non-Compliant

The agent must **reason**, not just match keywords.

**Deliverable:**

* Reasoning logic (prompt-based or rule-based)  
* Explanation of how the agent “decides”

---

### **Task 4: Bid / No-Bid Recommendation**

The agent must generate:

* Final recommendation: **Bid / No-Bid**  
* Confidence score (0–100)  
* Justification in natural language  
* Highlighted risk areas

**Sample Output:**

{"recommendation": "Bid","confidence\_score": 82,"risks": \["Tight delivery timeline"\],"justification": "The company meets all mandatory requirements and has prior experience in AI projects of similar scale." }  
---

### **Task 5: Autonomous Agent Behavior**

Add **agent autonomy** by implementing at least one of the following:

* The agent asks clarification questions if data is missing  
* The agent escalates high-risk requirements  
* The agent chooses whether to:  
  * Generate a compliance report  
  * Generate questions for the client  
  * Stop processing

---

## **Constraints**

* No UI required  
* Must work on **unstructured RFP text**  
* Code must be modular (agent, reasoning, output)

---

## **Bonus (Optional)**

Choose one:

* Multi-agent setup:  
  * Analyzer Agent  
  * Compliance Agent  
  * Risk Agent  
* Add memory so the agent learns from previous bid decisions  
* Explain decisions using **chain-of-thought style summaries**

