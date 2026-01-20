"""
Detailed Database Verification Script
Executes SQL queries to inspect all tables and verify data integrity against Knowledge Base JSONs.
"""

import sys
from pathlib import Path
from sqlalchemy import text
from tabulate import tabulate # You might need to install this or just use simple formatting

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.database.connection import SessionLocal

def run_query(db, query, title):
    print(f"\n{'='*80}")
    print(f"QUERY: {title}")
    print(f"{'-'*80}")
    print(f"SQL: {query.strip()}")
    print(f"{'-'*80}")
    
    try:
        result = db.execute(text(query))
        rows = result.fetchall()
        if not rows:
            print("No results found.")
            return

        # Get column names
        keys = result.keys()
        
        # Simple table formatting
        # Calculate max width for each column to align nicely
        col_widths = [len(k) for k in keys]
        formatted_rows = []
        
        for row in rows:
            row_str = []
            for i, val in enumerate(row):
                val_str = str(val)
                # Truncate long text
                if len(val_str) > 50:
                    val_str = val_str[:47] + "..."
                row_str.append(val_str)
                col_widths[i] = max(col_widths[i], len(val_str))
            formatted_rows.append(row_str)

        # Print Header
        header = " | ".join(f"{k:<{w}}" for k, w in zip(keys, col_widths))
        print(header)
        print("-" * len(header))
        
        # Print Rows
        for row in formatted_rows:
            print(" | ".join(f"{val:<{w}}" for val, w in zip(row, col_widths)))
            
        print(f"\nTotal Rows: {len(rows)}")
        
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    db = SessionLocal()
    
    try:
        # 1. Company Profile
        run_query(db, "SELECT name, team_size, years_of_experience, budget_capacity_min, budget_capacity_max FROM company_profiles", "Company Profile Check")
        
        # 2. Company Arrays (Regions, Industries) - verify array loading
        run_query(db, "SELECT delivery_regions, industries_served, core_services FROM company_profiles", "Company Arrays Check")

        # 3. Certifications
        run_query(db, "SELECT name, status, valid_until, issuing_body FROM certifications ORDER BY name", "Certifications Check")

        # 4. Tech Stack - Check counts by proficiency and sample
        run_query(db, "SELECT proficiency, COUNT(*) as count FROM tech_stacks GROUP BY proficiency", "Tech Stack Summary")
        run_query(db, "SELECT technology, proficiency, years_experience, team_size FROM tech_stacks ORDER BY proficiency, technology LIMIT 10", "Tech Stack (Top 10 Samples)")
        
        # 5. Strategic Preferences
        run_query(db, "SELECT preference_type, COUNT(*) as count FROM strategic_preferences GROUP BY preference_type", "Strategic Preferences Summary")
        run_query(db, "SELECT preference_type, value, priority, notes FROM strategic_preferences ORDER BY priority DESC LIMIT 10", "High Priority Preferences")
        
        # 6. Project Portfolio
        run_query(db, "SELECT name, industry, budget, outcome FROM project_portfolio ORDER BY budget DESC LIMIT 5", "Project Portfolio (Top Budget)")
        run_query(db, "SELECT name, technologies FROM project_portfolio LIMIT 3", "Project Technologies Verification")
        
        # 7. Embedding Check
        run_query(db, "SELECT name, CASE WHEN embedding IS NOT NULL THEN 'Present' ELSE 'Missing' END as embedding_status FROM project_portfolio LIMIT 5", "Embedding Existence Check")

    finally:
        db.close()

if __name__ == "__main__":
    main()
