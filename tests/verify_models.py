import sys
import json
from pydantic import ValidationError
from app.models.company import CompanyProfile
from app.models.project import Project
from app.models.requirement import Requirement, RequirementType
from app.models.recommendation import Recommendation

def verify_models():
    print("=== Step 6: Model Verification ===")
    
    # 1. CompanyProfile Validation
    print("\n[CompanyProfile]")
    try:
        company = CompanyProfile(
            name="Acme Corp",
            overview="Tech solutions",
            years_of_experience=5,
            team_size=10,
            delivery_regions=["US"],
            budget_capacity={"min": 1000, "max": 5000, "currency": "USD"},
            industries_served=["Finance"],
            core_services=["AI"]
        )
        print("✅ Valid CompanyProfile created")
        
        # Test Invalid Budget
        try:
            CompanyProfile(
                name="Bad Corp",
                overview="Bad",
                years_of_experience=1,
                team_size=1,
                delivery_regions=["US"],
                budget_capacity={"min": 5000, "max": 1000, "currency": "USD"}, # Invalid
                industries_served=["Finance"],
                core_services=["AI"]
            )
            print("❌ Failed to catch invalid budget range")
            sys.exit(1)
        except ValidationError:
            print("✅ Caught invalid budget range")

    except Exception as e:
        print(f"❌ Error in CompanyProfile: {e}")
        sys.exit(1)

    # 2. Project Validation
    print("\n[Project]")
    try:
        project = Project(
            id="proj_1",
            name="Test Project",
            industry="Tech",
            client_sector="Private",
            technologies=["Python", "FastAPI"],
            budget=50000.0,
            duration_months=6,
            team_size=4,
            outcome="Success",
            description="A test project",
            year=2024,
            embedding=[0.1, 0.2, 0.3]
        )
        print("✅ Valid Project created")

        # Test Invalid Duration
        try:
            project_invalid = project.model_copy()
            project_invalid.duration_months = 40 # > 36
            Project(**project_invalid.model_dump())
            print("❌ Failed to catch invalid duration")
            sys.exit(1)
        except ValidationError:
            print("✅ Caught invalid duration")

    except Exception as e:
        print(f"❌ Error in Project: {e}")
        sys.exit(1)

    # 3. Requirement Validation
    print("\n[Requirement]")
    try:
        req = Requirement(
            id="req_1",
            text="Must use Python",
            type=RequirementType.MANDATORY,
            category="Technical",
            priority="High",
            embedding=[0.5, 0.5]
        )
        print("✅ Valid Requirement created")
        
        # Test Invalid Enum
        try:
            req_data = req.model_dump()
            req_data['type'] = "INVALID_TYPE"
            Requirement(**req_data)
            print("❌ Failed to catch invalid enum")
            sys.exit(1)
        except ValidationError:
            print("✅ Caught invalid requirement type enum")

    except Exception as e:
        print(f"❌ Error in Requirement: {e}")
        sys.exit(1)

    # 4. Recommendation Validation
    print("\n[Recommendation]")
    try:
        rec = Recommendation(
            decision="BID",
            confidence_score=85,
            justification="Strong fit",
            risks=["Tight timeline"],
            requirements_met=["Python"],
            requirements_failed=[],
            clarification_questions=[],
            reasoning_steps=["Step 1", "Step 2"]
        )
        print("✅ Valid Recommendation created")
        
        # Test Lowercase Decision
        try:
            rec_data = rec.model_dump()
            rec_data['decision'] = "bid" # Lowercase
            Recommendation(**rec_data)
            print("❌ Failed to catch lowercase decision")
            sys.exit(1)
        except ValidationError:
            print("✅ Caught lowercase decision")

    except Exception as e:
        print(f"❌ Error in Recommendation: {e}")
        sys.exit(1)

    print("\n=== All Models Verified Successfully ===")

if __name__ == "__main__":
    verify_models()
