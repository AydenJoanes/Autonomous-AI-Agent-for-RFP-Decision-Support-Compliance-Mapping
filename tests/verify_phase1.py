import sys
from app.core.settings import settings
from app.core.exceptions import RFPNotFoundException
# Import logger AFTER settings to ensure config is loaded
from app.core.logging_config import app_logger

def verify_setup():
    print("=== Phase 1 Verification ===")
    
    # 1. Verify Settings
    print("\n[Settings Verification]")
    print(f"Environment: {settings.ENV}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"Retain Logs: {settings.LOG_RETENTION_DAYS} days")
    # Mask API Key for display
    masked_key = f"{settings.OPENAI_API_KEY[:6]}...{settings.OPENAI_API_KEY[-4:]}" if len(settings.OPENAI_API_KEY) > 10 else "***"
    print(f"OpenAI Key: {masked_key}")
    
    if settings.DATABASE_URL:
        print("Database URL: [Present]")
    else:
        print("Database URL: [MISSING] (FAIL)")
        sys.exit(1)

    # 2. Verify Logging
    print("\n[Logging Verification]")
    app_logger.info("This is a generic INFO log test.")
    app_logger.debug("This is a generically DEBUG log test.")
    app_logger.error("This is a generic ERROR log test.")
    
    # Test Agent Log binding
    agent_logger = app_logger.bind(type="agent")
    agent_logger.info("This is a test log from the AGENT context.")
    
    print("Logs generated. Check 'logs/' directory for 'app.log', 'errors.log', and 'agent.log'.")

    # 3. Verify Exceptions
    print("\n[Exception Verification]")
    try:
        raise RFPNotFoundException("Test exception: RFP not found")
    except RFPNotFoundException as e:
        print(f"Caught expected exception: {e}")
        app_logger.error(f"Caught verified exception: {e}")

    print("\n=== Verification Complete. Phase 1 Success! ===")

if __name__ == "__main__":
    verify_setup()
