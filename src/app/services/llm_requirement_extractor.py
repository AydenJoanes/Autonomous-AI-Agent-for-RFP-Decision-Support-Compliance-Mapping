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
EXTRACTION_SYSTEM_PROMPT = """You are an expert RFP analyst. Your task is to extract ONLY the checkable capability requirements from an RFP document.

WHAT TO EXTRACT:
- Certification requirements: Specific certifications the vendor must hold (ISO 27001, SOC 2, HIPAA, etc.)
- Technology requirements: Specific technologies the vendor must have expertise in (Azure, AWS, Python, etc.)
- Experience requirements: Domain or project experience the vendor must demonstrate (healthcare, public sector, etc.)
- Timeline constraints: Project duration limits or deadlines
- Budget constraints: Explicit budget amounts or ranges (only when dollar amounts are stated)
- Team requirements: Minimum team size, specific roles required
- Geographic requirements: Location, delivery region, or on-site requirements

WHAT TO IGNORE:
- Delivery scope: Descriptions of what the system should do or what the vendor should build
- Procedural instructions: How to submit proposals, formatting requirements, deadlines for questions
- Evaluation criteria: How proposals will be scored or compared
- Background context: Organizational history, current challenges, project rationale
- Reservation of rights: Legal disclaimers, right to reject proposals
- System functionality: Features the delivered system should have (these are delivery scope, not vendor capability)

CRITICAL DISTINCTION:
- "The vendor must have ISO 27001 certification" → EXTRACT (certification requirement)
- "The system must support ISO 27001-aligned security practices" → EXTRACT (certification requirement implied)
- "The system must calculate cost growth metrics" → IGNORE (delivery scope, not budget)
- "Budget: $500,000" → EXTRACT (budget constraint)
- "The vendor shall implement cost analytics" → IGNORE (delivery scope)

For each requirement, provide:
1. type: One of CERTIFICATION, TECHNOLOGY, EXPERIENCE, TIMELINE, BUDGET, TEAM, GEOGRAPHIC
2. original_text: The exact text from the RFP (keep under 200 characters)
3. extracted_value: The specific checkable value (e.g., "ISO 27001", "Azure", "5 years", "$500,000")
4. is_mandatory: true if required, false if preferred/optional
5. section_reference: Which section of the RFP this came from

Respond with a JSON object containing a "requirements" array. No preamble, no explanation."""


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
        
        # Group by extracted value for deduplication
        value_groups: Dict[str, List[Requirement]] = {}
        
        for req in all_requirements:
            key = f"{req.type.value}:{req.extracted_value}"
            if key not in value_groups:
                value_groups[key] = []
            value_groups[key].append(req)
        
        # For each group, keep the most complete requirement
        merged = []
        for key, group in value_groups.items():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Keep the one with longest original_text (most context)
                best = max(group, key=lambda r: len(r.text))
                merged.append(best)
                logger.debug(f"Deduplicated {len(group)} instances of: {best.extracted_value}")
        
        logger.info(f"Merged {len(all_requirements)} requirements into {len(merged)} unique requirements")
        
        return merged
    
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
