import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.app.database.connection import SessionLocal
from sqlalchemy import text

def check_embeddings():
    session = SessionLocal()
    try:
        print("Checking Project Portfolio Embeddings...")
        
        # Check total projects
        total = session.execute(text("SELECT COUNT(*) FROM project_portfolio")).scalar()
        print(f"Total projects: {total}")
        
        # Check projects with embeddings
        with_embeddings = session.execute(text("SELECT COUNT(*) FROM project_portfolio WHERE embedding IS NOT NULL")).scalar()
        print(f"Projects with embeddings: {with_embeddings}")
        
        # Check specific projects detail
        projects = session.execute(text("SELECT id, name, client_industry, CASE WHEN embedding IS NOT NULL THEN 'HAS_EMBEDDING' ELSE 'NO_EMBEDDING' END as status FROM project_portfolio")).fetchall()
        
        print("\nProject Details:")
        print(f"{'ID':<5} | {'Name':<50} | {'Industry':<20} | {'Status':<15}")
        print("-" * 100)
        for p in projects:
            status = p[3]
            # Handle potential None/null return in p[3] though query handles it
            print(f"{p[0]:<5} | {str(p[1])[:50]:<50} | {str(p[2])[:20]:<20} | {status:<15}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_embeddings()
