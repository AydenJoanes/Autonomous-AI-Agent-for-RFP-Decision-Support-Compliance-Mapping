"""
Test Requirement Extraction on Sample RFPs
"""

import sys
import json
import os
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.services.parser.factory import DocumentParserFactory
from src.app.agent.tools.requirement_processor_tool import RequirementProcessorTool
from src.app.models.requirement import RequirementType

def main():
    logger.info("=" * 60)
    logger.info("TEST: REQUIREMENT EXTRACTION")
    logger.info("=" * 60)
    
    # Setup paths
    sample_dir = Path("data/sample_rfps")
    output_dir = Path("data/test_output")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Initialize tools
    parser_factory = DocumentParserFactory()
    processor = RequirementProcessorTool()
    
    # Find files
    files = list(sample_dir.glob("*.pdf")) + list(sample_dir.glob("*.docx"))
    
    # Filter for specific file
    target_file = "DataAnalyticsSolution.pdf"
    files = [f for f in files if f.name == target_file]
    
    if not files:
        logger.error(f"Target file {target_file} not found!")
        return

    logger.info(f"Processing target file: {target_file}")
    
    results_summary = []
    
    for file_path in files:
        logger.info(f"\nProcessing {file_path.name}...")
        
        try:
            # 1. Parse
            text = parser_factory.parse_with_fallback(str(file_path))
            word_count = len(text.split())
            logger.info(f"  Parsed {word_count} words")
            
            # Save parsed text
            parsed_path = output_dir / f"{file_path.stem}_parsed.md"
            parsed_path.write_text(text, encoding="utf-8")
            
            # 2. Process Requirements
            requirements = processor._run(text)
            req_count = len(requirements)
            logger.info(f"  Extracted {req_count} requirements")
            
            # Save requirements JSON
            req_data = [req.dict(exclude={'embedding'}) for req in requirements]
            for r in req_data:
                r['id'] = str(r['id'])
                
            req_path = output_dir / f"{file_path.stem}_requirements.json"
            with open(req_path, 'w', encoding='utf-8') as f:
                json.dump(req_data, f, indent=2)
                
            # Generate Report
            report_path = output_dir / f"{file_path.stem}_report.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"# Requirement Analysis Report\n\n")
                f.write(f"**File**: {file_path.name}\n")
                f.write(f"**Total Requirements**: {req_count}\n\n")
                f.write("| Type | Priority | Category | Requirement |\n")
                f.write("|---|---|---|---|\n")
                for req in requirements:
                    # Escape pipes in text to avoid breaking table
                    clean_text = req.text.replace("|", r"\|").replace("\n", " ")
                    f.write(f"| {req.type.value} | {req.priority} | {req.category} | {clean_text} |\n")
            
            logger.success(f"Report generated: {report_path}")

            # Stats
            type_counts = {}
            embed_count = sum(1 for r in requirements if r.embedding)
            
            for r in requirements:
                type_counts[r.type] = type_counts.get(r.type, 0) + 1
                
            results_summary.append({
                "filename": file_path.name,
                "words": word_count,
                "requirements": req_count,
                "embeddings": embed_count,
                "types": type_counts
            })
            
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            results_summary.append({
                "filename": file_path.name,
                "error": str(e)
            })
            
    # Final Summary (Preserving existing logic)

            
    # Final Summary
    logger.info("\n" + "=" * 60)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 60)
    
    total_reqs = 0
    total_files = 0
    
    print(f"{'Filename':<40} | {'Words':<10} | {'Reqs':<8} | {'Embeds':<8} | {'Top Type'}")
    print("-" * 100)
    
    for res in results_summary:
        if "error" in res:
            print(f"{res['filename']:<40} | ERROR: {res['error']}")
            continue
            
        total_files += 1
        total_reqs += res['requirements']
        
        top_type = max(res['types'].items(), key=lambda x: x[1])[0] if res['types'] else "NONE"
        print(f"{res['filename']:<40} | {res['words']:<10} | {res['requirements']:<8} | {res['embeddings']:<8} | {top_type}")
        
    logger.info("=" * 60)
    if total_files > 0:
        logger.success(f"Successfully processed {total_files}/{len(files)} files")
        logger.success(f"Total Requirements Extracted: {total_reqs}")
        if total_files > 0:
            logger.info(f"Average Requirements/RFP: {total_reqs/total_files:.1f}")
    else:
        logger.warning("No files processed successfully")

if __name__ == "__main__":
    main()
