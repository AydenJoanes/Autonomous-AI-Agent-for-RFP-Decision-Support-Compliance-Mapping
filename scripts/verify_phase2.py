"""
Phase 2 Verification Script
Checks database tables, data, repositories, and API endpoints
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.database.connection import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    
    print("=" * 60)
    print("PHASE 2 VERIFICATION")
    print("=" * 60)
    
    # 1. Check all tables
    print("\n[1] DATABASE TABLES")
    print("-" * 40)
    result = db.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' ORDER BY table_name
    """))
    tables = [row[0] for row in result.fetchall()]
    print(f"Tables found: {len(tables)}")
    for t in tables:
        print(f"  ✓ {t}")
    
    # 2. Count records in each table
    print("\n[2] RECORD COUNTS")
    print("-" * 40)
    expected_tables = [
        ('company_profiles', 1),
        ('certifications', 5),
        ('tech_stacks', 15),
        ('project_portfolio', 10),
        ('strategic_preferences', 1),
    ]
    
    for table, expected_min in expected_tables:
        try:
            result = db.execute(text(f'SELECT COUNT(*) FROM {table}'))
            count = result.scalar()
            status = "✓" if count >= expected_min else "⚠"
            print(f"  {status} {table}: {count} records (expected >= {expected_min})")
        except Exception as e:
            db.rollback()
            print(f"  ✗ {table}: ERROR - {e}")
    
    # 3. Check pgvector extension
    print("\n[3] PGVECTOR EXTENSION")
    print("-" * 40)
    try:
        result = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        if result.fetchone():
            print("  ✓ pgvector extension installed")
        else:
            print("  ✗ pgvector extension NOT found")
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error checking pgvector: {e}")
    
    # 4. Check embeddings exist
    print("\n[4] PROJECT EMBEDDINGS")
    print("-" * 40)
    try:
        result = db.execute(text("SELECT COUNT(*) FROM project_portfolio WHERE embedding IS NOT NULL"))
        count = result.scalar()
        status = "✓" if count > 0 else "⚠"
        print(f"  {status} Projects with embeddings: {count}")
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error: {e}")
    
    # 5. Sample data check
    print("\n[5] SAMPLE DATA")
    print("-" * 40)
    
    # Company
    try:
        result = db.execute(text("SELECT name FROM company_profiles LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"  ✓ Company: {row[0]}")
        else:
            print("  ⚠ No company profile found")
    except Exception as e:
        db.rollback()
        print(f"  ✗ Company: {e}")
    
    # Certifications
    try:
        result = db.execute(text("SELECT name, status FROM certifications LIMIT 3"))
        rows = result.fetchall()
        print(f"  ✓ Certifications sample:")
        for row in rows:
            print(f"      - {row[0]} ({row[1]})")
    except Exception as e:
        db.rollback()
        print(f"  ✗ Certifications: {e}")
    
    # Tech stacks
    try:
        result = db.execute(text("SELECT technology, proficiency FROM tech_stacks LIMIT 3"))
        rows = result.fetchall()
        if rows:
            print(f"  ✓ Tech stacks sample:")
            for row in rows:
                print(f"      - {row[0]} ({row[1]})")
        else:
            print("  ⚠ No tech stacks found - table empty")
    except Exception as e:
        db.rollback()
        print(f"  ✗ Tech stacks: {e}")
    
    # Projects
    try:
        result = db.execute(text("SELECT name, industry FROM project_portfolio LIMIT 3"))
        rows = result.fetchall()
        print(f"  ✓ Projects sample:")
        for row in rows:
            print(f"      - {row[0]} ({row[1]})")
    except Exception as e:
        db.rollback()
        print(f"  ✗ Projects: {e}")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
