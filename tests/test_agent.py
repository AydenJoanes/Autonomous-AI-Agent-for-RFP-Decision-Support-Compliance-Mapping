"""
Tests for RFP Agent
"""

import pytest

from config.settings import Settings
from src.agent.rfp_agent import RFPAgent


class TestRFPAgent:
    """Tests for RFPAgent."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        settings = Settings()
        agent = RFPAgent(settings=settings)
        assert agent.settings == settings
    
    def test_agent_process_rfp(self):
        """Test RFP processing."""
        # TODO: Implement test
        pass
