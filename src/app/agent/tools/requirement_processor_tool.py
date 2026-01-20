"""
Requirement Processor Tool - Extracts, classifies, and processes requirements
"""

import json
import re
import time
from typing import List, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from loguru import logger

from src.app.models.requirement import Requirement, RequirementType
from src.app.utils.embeddings import generate_batch_embeddings
from src.app.utils.embeddings import get_openai_client # Reuse client if needed directly
from config.settings import settings

class RequirementProcessorInput(BaseModel):
    rfp_markdown: str = Field(..., description="The full Markdown text of the RFP")

class RequirementProcessorTool(BaseTool):
    name: str = "requirement_processor"
    description: str = "Extracts, classifies, and generates embeddings for all requirements from RFP markdown text"
    args_schema: Type[BaseModel] = RequirementProcessorInput

    def _run(self, rfp_markdown: str) -> List[Requirement]:
        """Execute the tool."""
        logger.info("[TOOL] Requirement Processor started")
        
        results = []
        
        try:
            # Step 1: Extract raw requirements
            raw_requirements = self._extract_raw_requirements_regex(rfp_markdown)
            if not raw_requirements:
                logger.warning("[EXTRACT] No requirements found via regex")
                return []
                
            logger.info(f"[EXTRACT] Found {len(raw_requirements)} raw requirements")
            
            # Step 2: Classify requirements (LLM)
            classified_data = self._classify_requirements_llm(raw_requirements)
            logger.info(f"[CLASSIFY] Classified {len(classified_data)} requirements")
            
            # Step 3: Validating objects first to filter valid texts
            valid_requirements = []
            texts_to_embed = []
            
            for item in classified_data:
                try:
                    # Basic validation and creation
                    req = Requirement(
                        text=item.get("text", ""),
                        type=item.get("type", RequirementType.OTHER),
                        category=item.get("category", "general"),
                        priority=item.get("priority", 5),
                        confidence=item.get("confidence", 0.0),
                        metadata=item.get("metadata", {})
                    )
                    valid_requirements.append(req)
                    texts_to_embed.append(req.text)
                except Exception as e:
                    logger.warning(f"Skipping invalid requirement: {e}")
            
            if not valid_requirements:
                return []

            # Step 4: Generate embeddings (Batch)
            logger.info("[EMBED] Starting embedding generation")
            try:
                embeddings = generate_batch_embeddings(texts_to_embed)
                
                # Attach embeddings
                for req, emb in zip(valid_requirements, embeddings):
                    req.embedding = emb
                    
                logger.info(f"[EMBED] Generated {len(embeddings)} embeddings")
            except Exception as e:
                logger.error(f"[EMBED] Failed: {e}")
                # Continue without embeddings if failed
            
            logger.info(f"[TOOL] Requirement Processor complete: {len(valid_requirements)} requirements")
            return valid_requirements

        except Exception as e:
            logger.error(f"[TOOL] Critical failure in requirement processor: {e}")
            return [] # Graceful degradation

    def _extract_raw_requirements_regex(self, text: str) -> List[str]:
        """
        Extract potential requirement sentences using regex heuristics.
        Focuses on 'shall', 'must', 'will', 'required', etc.
        """
        # Split into sentences (simple approach) or lines
        # Using lines for markdown usually safer for lists
        lines = text.split('\n')
        candidates = []
        
        patterns = [
            r"\b(shall|must|will|required|requirement|expect|deliverable)\b",
            r"(?:certificat|complian|security|priva)",
            r"(?:budget|cost|pric|timeline|schedule|deadline)",
            r"(?:python|java|sql|cloud|aws|azure)"
        ]
        
        combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)
        
        for line in lines:
            line = line.strip()
            # Basic filter: distinct line, reasonable length, contains keywords
            if len(line) > 10 and combined_pattern.search(line):
                # Remove bullets
                clean_line = re.sub(r"^[\*\-\d\.]+\s*", "", line)
                candidates.append(clean_line)
                
        return candidates

    def _classify_requirements_llm(self, raw_reqs: List[str]) -> List[Dict[str, Any]]:
        """
        Classify raw requirements using OpenAI.
        """
        logger.info("[CLASSIFY] Starting LLM classification")
        
        # Batching for LLM to avoid context limits if too many
        batch_size = 20 # Conservative for output JSON size
        all_classified = []
        
        from src.app.utils.embeddings import get_openai_client
        client = get_openai_client() # Reuse client
        
        for i in range(0, len(raw_reqs), batch_size):
            batch = raw_reqs[i:i+batch_size]
            prompt = self._build_classification_prompt(batch)
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a precise RFP analyst. Classify the following requirements into structured JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    
                    content = response.choices[0].message.content
                    data = json.loads(content)
                    
                    if "requirements" in data:
                        all_classified.extend(data["requirements"])
                    break # Success
                    
                except Exception as e:
                    logger.warning(f"[CLASSIFY] Batch {i} failed (attempt {attempt+1}): {e}")
                    if attempt == max_retries - 1:
                        logger.error("[CLASSIFY] Batch failed permanently, skipping")
                    time.sleep(1)
        
        return all_classified

    def _build_classification_prompt(self, reqs: List[str]) -> str:
        req_list = json.dumps(reqs, indent=2)
        return f"""
Analyze the following list of potential RFP requirements.
For each item, determine if it is a genuine requirement. If yes, classify it.

Input:
{req_list}

Output format (JSON):
{{
  "requirements": [
    {{
      "text": "original text",
      "type": "MANDATORY|TECHNICAL|PREFERRED|TIMELINE|BUDGET|OTHER",
      "category": "string (e.g. security, backend, legal)",
      "priority": int (1-10, 10=critical),
      "confidence": float (0.0-1.0),
      "metadata": {{ "reason": "brief explanation" }}
    }}
  ]
}}
Only include valid requirements. Ignore headers or noise.
"""
