"""
Session management for FactFlow agent system.

This module implements session management using InMemorySessionService
to enable stateful, multi-turn conversations.
"""

from typing import Optional, Dict, Any
from google.adk.runners import InMemoryRunner, InMemorySessionService
from google.adk.agents import Agent
from google.adk.apps import App

from ..agents.sentiment_agents import create_factflow_agent


class FactFlowSessionManager:
    """
    Manages sessions for FactFlow agent interactions.
    
    This class wraps InMemorySessionService to provide session management
    for multi-turn conversations. Each session maintains conversation history
    and context across multiple user queries.
    
    Example:
        >>> manager = FactFlowSessionManager()
        >>> runner = manager.get_runner(session_id="user123")
        >>> response = await runner.run("Assess Ethereum right now")
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        """
        Initialize the session manager.
        
        Args:
            model_name: The Gemini model to use for agents
        """
        self.model_name = model_name
        self.agent = create_factflow_agent(model_name=model_name)
        # Wrap agent in App with explicit name to avoid app name mismatch warning
        self.app = App(
            name="factflow",
            root_agent=self.agent,
        )
        self.session_service = InMemorySessionService()
        self.runners: Dict[str, InMemoryRunner] = {}
    
    def get_runner(self, session_id: str) -> InMemoryRunner:
        """
        Get or create a runner for a specific session.
        
        Args:
            session_id: Unique identifier for the session
        
        Returns:
            InMemoryRunner configured for this session
        """
        if session_id not in self.runners:
            # InMemoryRunner is created with the app to avoid app name mismatch warning
            # Sessions are managed through the run() method, not the constructor
            self.runners[session_id] = InMemoryRunner(app=self.app)
        return self.runners[session_id]
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a session.
        
        Args:
            session_id: The session identifier
        
        Returns:
            Session state dictionary or None if session doesn't exist
        """
        if session_id in self.runners:
            # Access session state through the runner
            # Note: This is a simplified version - actual implementation
            # would access the session service's state storage
            return {"session_id": session_id, "exists": True}
        return None
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear a session's history.
        
        Args:
            session_id: The session identifier
        
        Returns:
            True if session was cleared, False if it didn't exist
        """
        if session_id in self.runners:
            del self.runners[session_id]
            return True
        return False

