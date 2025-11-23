"""
Tracing implementation for FactFlow agent system.

This module implements trace collection to track the full execution flow
through sequential agents, enabling debugging and performance analysis.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class TraceCollector:
    """
    Collects execution traces for agent workflows.
    
    Traces capture the full execution flow through sequential agents,
    including tool calls, agent transitions, and timing information.
    """
    
    def __init__(self, trace_file: Optional[str] = None):
        """
        Initialize the trace collector.
        
        Args:
            trace_file: Optional file path to save traces (JSON format)
        """
        self.trace_file = trace_file
        self.traces: List[Dict[str, Any]] = []
        self.current_trace: Optional[Dict[str, Any]] = None
    
    def start_trace(self, session_id: str, user_query: str) -> str:
        """
        Start a new trace for a user query.
        
        Args:
            session_id: Session identifier
            user_query: User's query
        
        Returns:
            Trace ID
        """
        trace_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        self.current_trace = {
            "trace_id": trace_id,
            "session_id": session_id,
            "user_query": user_query,
            "start_time": datetime.now().isoformat(),
            "agents": [],
            "tool_calls": [],
            "errors": [],
        }
        
        return trace_id
    
    def log_agent_start(self, agent_name: str, input_data: Optional[Dict[str, Any]] = None):
        """Log when an agent starts execution."""
        if not self.current_trace:
            return
        
        agent_entry = {
            "agent_name": agent_name,
            "start_time": datetime.now().isoformat(),
            "input_data": input_data or {},
            "tool_calls": [],
        }
        self.current_trace["agents"].append(agent_entry)
    
    def log_agent_end(
        self,
        agent_name: str,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """Log when an agent completes execution."""
        if not self.current_trace or not self.current_trace["agents"]:
            return
        
        # Find the most recent agent entry
        agent_entry = None
        for entry in reversed(self.current_trace["agents"]):
            if entry["agent_name"] == agent_name and "end_time" not in entry:
                agent_entry = entry
                break
        
        if agent_entry:
            agent_entry["end_time"] = datetime.now().isoformat()
            agent_entry["output_data"] = output_data or {}
            if error:
                agent_entry["error"] = error
                self.current_trace["errors"].append({
                    "agent": agent_name,
                    "error": error,
                    "timestamp": datetime.now().isoformat(),
                })
    
    def log_tool_call(
        self,
        agent_name: str,
        tool_name: str,
        input_params: Dict[str, Any],
        output: Dict[str, Any],
        duration_ms: float,
    ):
        """Log a tool call."""
        if not self.current_trace:
            return
        
        tool_call = {
            "agent_name": agent_name,
            "tool_name": tool_name,
            "input_params": input_params,
            "output": output,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.current_trace["tool_calls"].append(tool_call)
        
        # Also add to the current agent's tool calls
        if self.current_trace["agents"]:
            current_agent = self.current_trace["agents"][-1]
            current_agent["tool_calls"].append(tool_call)
    
    def end_trace(self, final_output: Optional[str] = None) -> Dict[str, Any]:
        """
        End the current trace and save it.
        
        Args:
            final_output: Final output from the agent system
        
        Returns:
            Complete trace dictionary
        """
        if not self.current_trace:
            return {}
        
        self.current_trace["end_time"] = datetime.now().isoformat()
        self.current_trace["final_output"] = final_output
        
        # Calculate total duration
        start = datetime.fromisoformat(self.current_trace["start_time"])
        end = datetime.fromisoformat(self.current_trace["end_time"])
        self.current_trace["total_duration_ms"] = (end - start).total_seconds() * 1000
        
        # Save trace
        self.traces.append(self.current_trace.copy())
        
        # Save to file if specified
        if self.trace_file:
            self._save_traces()
        
        trace = self.current_trace.copy()
        self.current_trace = None
        return trace
    
    def _save_traces(self):
        """Save all traces to file."""
        if not self.trace_file:
            return
        
        try:
            with open(self.trace_file, "w") as f:
                json.dump(self.traces, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save traces: {e}")
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific trace by ID."""
        for trace in self.traces:
            if trace["trace_id"] == trace_id:
                return trace
        return None
    
    def get_recent_traces(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent traces."""
        return self.traces[-limit:] if self.traces else []

