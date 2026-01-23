
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from src.app.database.connection import SessionLocal
from src.app.database.repositories.cert_repository import CertificationRepository
from src.app.database.repositories.strategic_preferences_repository import StrategicPreferencesRepository
from sqlalchemy import text

def update_data():
    session = SessionLocal()
    cert_repo = CertificationRepository(session)
    strat_repo = StrategicPreferencesRepository(session)

    try:
        print("Starting data updates...")

        # 1. Update Expired Certifications
        certs_to_update = {
            "ISO 27001": "2028-03-14",
            "GDPR Compliance": "2029-01-09",
            "ISO 9001": "2027-06-19",
            "AWS Partner Network": "2028-08-31",
            "Microsoft Azure Partnership": "2028-01-14"
        }

        print("\nUpdating Certifications:")
        for name, new_date in certs_to_update.items():
            # Try exact match first
            cert = cert_repo.get_by_name(name)
            
            # If not found, try fuzzy/partial match via SQL
            if not cert:
                 # Attempt to find by partial name
                result = session.execute(
                    text("SELECT id, name FROM certifications WHERE name ILIKE :name"), 
                    {"name": f"%{name}%"}
                ).fetchone()
                if result:
                    print(f"  Found '{name}' as '{result[1]}'")
                    cert = {"id": result[0], "name": result[1]}

            if cert:
                # Update using raw SQL to be safe if repo lacks update specific method
                session.execute(
                    text("UPDATE certifications SET valid_until = :date, status = 'active' WHERE id = :id"),
                    {"date": new_date, "id": cert['id']}
                )
                print(f"  Updated '{cert['name']}' valid_until to {new_date}")
            else:
                print(f"  WARNING: Could not find certification '{name}'")
        
        # 2. Add Long-Term Engagement Policy
        print("\nAdding Strategic Policy:")
        policy_key = "long_term_engagement_policy"
        existing = strat_repo.get_by_value(policy_key)
        
        if not existing:
            # We add it as a 'policy' type or 'project_type' depending on schema usage.
            # Based on repo, it looks for preference_type.
            # Let's check schema.py logic or just insert as 'policy'
            
            # Inserting as 'policy' type
            strat_repo.add_preference({
                "preference_type": "policy",
                "value": policy_key,
                "priority": 10,
                "notes": "Engagements over 24 months require executive approval"
            })
            print(f"  Added policy: {policy_key}")
        else:
             print(f"  Policy '{policy_key}' already exists.")

        session.commit()
        print("\nData updates completed successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error updating data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    update_data()
