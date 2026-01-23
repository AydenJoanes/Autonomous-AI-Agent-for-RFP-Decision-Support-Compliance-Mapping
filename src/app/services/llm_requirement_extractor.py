"""
LLM Requirement Extractor
Semantic requirement extraction using LLM instead of pattern matching.
"""

import json
from typing import List, Tuple, Dict, Any, Optional
from loguru import logger

from src.app.models.requirement import Requirement, RequirementType
from src.app.models.parser import RFPMetadata
from src.app.utils.llm_client import get_llm_client
from src.app.services.llm_config import get_llm_config


# System prompt for document understanding
EXTRACTION_SYSTEM_PROMPT = """You are an expert RFP analyst. Your task is to extract ONLY the MOST CRITICAL checkable capability requirements from an RFP document.

STRICT EXTRACTION RULES - BE VERY SELECTIVE:

ONLY EXTRACT REQUIREMENTS THAT:
1. Can be verified against a company database (certifications, tech stack, past projects)
2. Have a SPECIFIC, NAMED value (not generic descriptions)
3. Are vendor qualifications, NOT system features

WHAT TO EXTRACT (with specific named values only):
- Certifications: ISO 27001, SOC 2, HIPAA, GDPR, FedRAMP, PCI-DSS, CMMI (exact names only)
- Technologies: Azure, AWS, Python, Kubernetes, Docker, etc. (specific tech names only)
- Experience domains: Healthcare, Finance, Government (specific industries only)
- Timeline: Explicit deadlines or durations with numbers (e.g., "6 months", "by December 2026")
- Budget: Explicit dollar amounts only (e.g., "$500,000")
- Team size: Specific numbers (e.g., "minimum 10 developers")

WHAT TO ABSOLUTELY IGNORE (do NOT extract):
- System features: "The system must...", "The platform shall...", "must support analytics"
- Design requirements: "robust", "scalable", "transparent", "auditable"
- Data handling: "must validate data", "ensure data integrity", "normalize data"
- Methodology: "must be explainable", "must be reproducible", "must be versioned"  
- Process requirements: "submit electronically", "provide documentation"
- Generic statements: "demonstrate capability", "ensure compliance", "maintain security"
- Anything without a SPECIFIC NAMED VALUE that can be looked up

HARD LIMIT: Extract NO MORE than 15 requirements. Focus on the MOST CRITICAL ones.
If in doubt, DO NOT extract. It is better to miss a borderline requirement than to include noise.

EXAMPLES OF WHAT TO IGNORE:
- "The system must provide full transparency" → IGNORE (system feature, vague)
- "Cost calculations must be documented" → IGNORE (process requirement)
- "Vendors must demonstrate organizational maturity" → IGNORE (vague, not checkable)
- "Experience with compliance-aware systems" → IGNORE (too vague)

EXAMPLES OF WHAT TO EXTRACT:
- "ISO 27001 certification required" → EXTRACT: CERTIFICATION, "ISO 27001"
- "Must have Azure expertise" → EXTRACT: TECHNOLOGY, "Azure"
- "Prior healthcare analytics experience" → EXTRACT: EXPERIENCE, "Healthcare analytics"
- "Budget not to exceed $2M" → EXTRACT: BUDGET, "$2,000,000"
- "Complete within 12 months" → EXTRACT: TIMELINE, "12 months"

For each requirement provide:
1. type: CERTIFICATION, TECHNOLOGY, EXPERIENCE, TIMELINE, BUDGET, or TEAM
2. original_text: Exact text (max 100 chars)
3. extracted_value: The specific named value ONLY
4. is_mandatory: true/false
5. section_reference: Section name

Return JSON: {"requirements": [...]}. No explanation.
Maximum 15 requirements. Quality over quantity."""


def build_extraction_user_prompt(rfp_text: str, metadata: RFPMetadata, chunk_info: Optional[Dict] = None) -> str:
    """
    Build user prompt for extraction.
    
    Args:
        rfp_text: RFP text to analyze
        metadata: RFP metadata
        chunk_info: Optional chunk information for large documents
        
    Returns:
        Formatted user prompt
    """
    chunk_note = ""
    if chunk_info:
        chunk_note = f"\n(This is chunk {chunk_info['index'] + 1} of {chunk_info['total']} from the full document)"
    
    return f"""Analyze this RFP document and extract only the checkable capability requirements.

Document: {metadata.filename}
Total Pages: {metadata.page_count}{chunk_note}

--- BEGIN RFP TEXT ---
{rfp_text}
--- END RFP TEXT ---

Extract requirements as a JSON object with a "requirements" array following the specified format."""


class LLMRequirementExtractor:
    """Extract requirements using LLM semantic understanding."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.llm_client = get_llm_client()
        self.config = get_llm_config()
    
    def chunk_large_document(self, rfp_text: str) -> List[Tuple[str, Dict]]:
        """
        Split large documents into chunks for processing.
        
        Args:
            rfp_text: Full RFP text
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        # Count tokens
        token_count = self.llm_client.count_tokens(rfp_text, self.config.llm_extraction_model)
        
        logger.info(f"Document has {token_count} tokens (limit: {self.config.max_chunk_size_tokens})")
        
        # If under limit, return single chunk
        if token_count <= self.config.max_chunk_size_tokens:
            return [(rfp_text, {"index": 0, "total": 1, "section": "Full Document"})]
        
        logger.info("Document exceeds token limit, chunking...")
        
        # Split by sections (markdown headers)
        chunks = []
        current_chunk = []
        current_tokens = 0
        section_name = "Introduction"
        
        lines = rfp_text.split('\n')
        
        for line in lines:
            # Check if this is a header
            if line.startswith('#'):
                # If current chunk is large enough, save it
                if current_tokens > self.config.max_chunk_size_tokens * 0.8:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append((chunk_text, {"section": section_name}))
                    current_chunk = []
                    current_tokens = 0
                
                # Extract section name
                section_name = line.lstrip('#').strip()
            
            # Add line to current chunk
            line_tokens = self.llm_client.count_tokens(line, self.config.llm_extraction_model)
            current_chunk.append(line)
            current_tokens += line_tokens
            
            # If chunk is too large, split it
            if current_tokens > self.config.max_chunk_size_tokens:
                chunk_text = '\n'.join(current_chunk)
                chunks.append((chunk_text, {"section": section_name}))
                current_chunk = []
                current_tokens = 0
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append((chunk_text, {"section": section_name}))
        
        # Add chunk indices
        total_chunks = len(chunks)
        for i, (text, meta) in enumerate(chunks):
            meta["index"] = i
            meta["total"] = total_chunks
        
        logger.info(f"Split document into {total_chunks} chunks")
        
        return chunks

    def merge_chunk_extractions(self, chunk_results: List[List[Requirement]]) -> List[Requirement]:
        """
        Merge and deduplicate requirements from multiple chunks.
        
        Args:
            chunk_results: List of requirement lists from each chunk
            
        Returns:
            Deduplicated requirement list
        """
        if not chunk_results:
            return []
        
        # Flatten all requirements
        all_requirements = []
        for chunk_reqs in chunk_results:
            all_requirements.extend(chunk_reqs)
        
        if not all_requirements:
            return []
        
        logger.info(f"Merging {len(all_requirements)} requirements (before dedupe)")
        
        # Sort by length descending to prioritize longer/more specific descriptions
        # This helps with containment check
        all_requirements.sort(key=lambda r: len(r.extracted_value or ""), reverse=True)
        
        unique_reqs = []
        # Keep track of what we've seen (normalized)
        # Store as set of (type, normalized_value)
        seen_values = set()
        
        for req in all_requirements:
            if not req.extracted_value:
                continue
                
            norm_value = req.extracted_value.strip().lower()
            # Remove common prefixes/suffixes for better dup detection
            clean_value = norm_value.replace("compliance", "").replace("certification", "").replace("experience", "").strip()
            if not clean_value:
                clean_value = norm_value # Fallback if empty
                
            req_type = req.type.value
            
            # Check for exact Match or Containment using clean value
            # Since we sorted by length descending, "HIPAA Compliance" comes first.
            # "HIPAA" (shorter) comes later.
            # If we see "HIPAA Compliance" -> add to set.
            # If we see "HIPAA" -> checks if "hipaa" in "hipaa compliance" -> True -> Skip.
            
            is_dupe = False
            for seen_val, seen_type in seen_values:
                if seen_type == req_type:
                    # Check if current value is contained in an existing longer value
                    # OR if existing value is contained in current (shouldn't happen due to sort, but good safety)
                    if clean_value in seen_val or seen_val in clean_value:
                        logger.debug(f"Deduplicating '{norm_value}' (similar to '{seen_val}')")
                        is_dupe = True
                        break
            
            if not is_dupe:
                unique_reqs.append(req)
                seen_values.add((clean_value, req_type))
        
        logger.info(f"Merged {len(all_requirements)} requirements into {len(unique_reqs)} unique requirements")
        
        return unique_reqs
    
    def parse_llm_response(self, response: Dict[str, Any]) -> List[Requirement]:
        """
        Parse LLM response into Requirement objects.
        
        Args:
            response: Parsed JSON response from LLM
            
        Returns:
            List of Requirement objects
        """
        requirements = []
        
        # Extract requirements array
        req_list = response.get("requirements", [])
        
        for item in req_list:
            try:
                # Map type string to enum
                type_str = item.get("type", "").upper()
                try:
                    req_type = RequirementType[type_str]
                except KeyError:
                    logger.warning(f"Unknown requirement type: {type_str}, skipping")
                    continue
                
                # Create Requirement object
                req = Requirement(
                    type=req_type,
                    text=item.get("original_text", ""),
                    extracted_value=item.get("extracted_value", ""),
                    is_mandatory=item.get("is_mandatory", True),
                    source_section=item.get("section_reference", "Unknown"),
                    # Populate legacy fields for compatibility
                    category=type_str,
                    priority=10 if item.get("is_mandatory", True) else 5
                )
                
                requirements.append(req)
                
            except Exception as e:
                logger.warning(f"Failed to parse requirement: {item}. Error: {e}")
                continue
        
        return requirements
    
    def extract_requirements_with_llm(
        self,
        rfp_text: str,
        metadata: RFPMetadata
    ) -> List[Requirement]:
        """
        Extract requirements using LLM semantic understanding.
        
        Args:
            rfp_text: Full RFP text
            metadata: RFP metadata
            
        Returns:
            List of extracted requirements
            
        Raises:
            Exception: On LLM API error or parsing failure
        """
        logger.info(f"Extracting requirements from {metadata.filename} using LLM")
        
        # Check if document needs chunking
        chunks = self.chunk_large_document(rfp_text)
        
        # Extract from each chunk
        chunk_results = []
        
        for chunk_text, chunk_meta in chunks:
            try:
                # Build prompts
                user_prompt = build_extraction_user_prompt(chunk_text, metadata, chunk_meta)
                
                # Call LLM
                response = self.llm_client.call_llm_json(
                    system_prompt=EXTRACTION_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    model=self.config.llm_extraction_model,
                    temperature=self.config.extraction_temperature,
                    timeout=self.config.extraction_timeout
                )
                
                # Parse response
                requirements = self.parse_llm_response(response)
                chunk_results.append(requirements)
                
                logger.info(
                    f"Extracted {len(requirements)} requirements from chunk "
                    f"{chunk_meta['index'] + 1}/{chunk_meta['total']}"
                )
                
            except Exception as e:
                logger.error(f"Failed to extract from chunk {chunk_meta['index']}: {e}")
                # Continue with other chunks
                chunk_results.append([])
        
        # Merge results
        merged_requirements = self.merge_chunk_extractions(chunk_results)
        
        logger.info(f"Total extracted requirements: {len(merged_requirements)}")
        
        return merged_requirements
