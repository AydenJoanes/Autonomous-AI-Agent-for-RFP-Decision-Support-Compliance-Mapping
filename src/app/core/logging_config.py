import sys
import os
from loguru import logger
from app.core.settings import settings

def setup_logging():
    """
    Configures the application logging using Loguru.
    Removes default handlers and adds structured sinks for different log types.
    """
    # Create logs directory if it doesn't exist
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    # Remove default handler
    logger.remove()

    # --- Console Sink ---
    # Colored output for development, structured for production could be added here
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # --- File Sinks ---

    # 1. Main Application Log
    logger.add(
        os.path.join(settings.LOG_DIR, "app.log"),
        level=settings.LOG_LEVEL,
        rotation="50 MB",
        retention=f"{settings.LOG_RETENTION_DAYS} days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression="zip"
    )

    # 2. Agent Reasoning Log (Filtered)
    # This filter assumes agent-related logs will carry 'extra={"type": "agent"}' or similar bound context
    # For now, we'll route ALL logs to app.log, and we can define a specific filter if we use `logger.bind(type="agent")`
    logger.add(
        os.path.join(settings.LOG_DIR, "agent.log"),
        filter=lambda record: "agent" in record["extra"].get("type", "").lower(),
        level="DEBUG", # Capture detailed agent steps
        rotation="50 MB",
        retention=f"{settings.LOG_RETENTION_DAYS} days",
        format="{time:YYYY-MM-DD HH:mm:ss} | AGENT | {message}",
        compression="zip"
    )

    # 3. Error Log (Errors only)
    logger.add(
        os.path.join(settings.LOG_DIR, "errors.log"),
        level="ERROR",
        rotation="50 MB",
        retention=f"{settings.LOG_RETENTION_DAYS} days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=True, # Show variable values in traceback (be careful with secrets, but helpful in dev)
        compression="zip"
    )

    logger.info(f"Logging initialized. Level: {settings.LOG_LEVEL}, Env: {settings.ENV}")

    return logger

# Initialize logging on import
app_logger = setup_logging()
