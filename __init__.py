"""
FactFlow - Sentiment-Reality Check Agent System

A multi-agent system that compares news sentiment with actual market price action
to identify market inefficiencies and provide data-driven trading recommendations.
"""

__version__ = "1.0.0"
__author__ = "FactFlow Team"

from .agents.sentiment_agents import create_factflow_agent
from .session.session_manager import FactFlowSessionManager
from .session.memory_service import MemoryBank

__all__ = [
    "create_factflow_agent",
    "FactFlowSessionManager",
    "MemoryBank",
]

