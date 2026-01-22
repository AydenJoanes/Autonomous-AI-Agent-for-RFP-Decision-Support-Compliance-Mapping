import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.database.connection import engine
from sqlalchemy import text

def verify_db():
    print("[-] Connecting to Database...")
    try:
        with engine.connect() as conn:
            # Query per Phase 6 requirements
            query = text("""
                SELECT
                  decision,
                  confidence_score,
                  reflection_notes,
                  clarification_questions,
                  embedding,
                  calibration_metrics
                FROM recommendations
                ORDER BY created_at DESC
                LIMIT 1;
            """)
            
            result = conn.execute(query).fetchone()
            
            if not result:
                print("[FAIL] No records found in recommendations table")
                return

            rec, conf, refl, clarif, emb, calib = result
            
            print(f"[-] Record found: {rec} (Confidence: {conf})")
            
            # Assertions
            if refl is not None:
                print("[PASS] reflection_notes is NOT NULL")
                # print(f"    Content: {json.dumps(refl)[:100]}...")
            else:
                print("[FAIL] reflection_notes IS NULL")

            if clarif is None or isinstance(clarif, (list, dict)):
                print(f"[PASS] clarification_questions is valid type: {type(clarif)}")
            else:
                print(f"[FAIL] clarification_questions invalid type: {type(clarif)}")
                
            if emb is not None:
                 print("[PASS] embedding is NOT NULL")
            else:
                 print("[WARN] embedding IS NULL (Optional but expected if enabled)")
                 
            if calib is None:
                print("[PASS] calibration_metrics IS NULL")
            else:
                print(f"[FAIL] calibration_metrics IS NOT NULL: {calib}")

    except Exception as e:
        print(f"[ERROR] Database verification failed: {e}")

if __name__ == "__main__":
    verify_db()