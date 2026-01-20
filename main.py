"""
RFP Bid Agent - Main Entry Point
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import Settings
from src.agent.rfp_agent import RFPAgent


def main():
    """Main entry point for the RFP Bid Agent."""
    
    # Load configuration
    settings = Settings()
    
    # Initialize agent
    agent = RFPAgent(settings=settings)
    
    # TODO: Implement main logic
    print("RFP Bid Agent initialized successfully")
    print(f"Debug mode: {settings.debug}")
    print(f"Log level: {settings.log_level}")


if __name__ == "__main__":
    main()
