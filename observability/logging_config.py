"""
Logging configuration for FactFlow agent system.

This module sets up structured logging for all agent actions, tool calls,
and API responses to enable debugging and monitoring.
"""

import logging
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional


class WarningFilter(logging.Filter):
    """Filter to suppress expected warnings from Google ADK/GenAI libraries."""
    
    def filter(self, record):
        """Filter out specific warning messages."""
        message = record.getMessage()
        # Filter app name mismatch warnings
        if "App name mismatch detected" in message:
            return False
        # Filter function call warnings
        if "there are non-text parts in the response" in message:
            return False
        return True


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
) -> logging.Logger:
    """
    Set up logging configuration for FactFlow.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path (if None, logs to console only)
        log_dir: Directory for log files (created if doesn't exist)
    
    Returns:
        Configured logger instance
    """
    # Create log directory if needed
    if log_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
    
    # Suppress specific warnings from Google ADK and GenAI libraries
    # These warnings are expected and don't indicate actual problems
    warnings.filterwarnings(
        "ignore",
        message=".*App name mismatch detected.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=".*there are non-text parts in the response.*",
        category=UserWarning,
    )
    
    # Also filter at the logging level for ADK runners and add custom filter
    adk_logger = logging.getLogger("google.adk.runners")
    adk_logger.setLevel(logging.ERROR)  # Only show errors, suppress warnings
    adk_logger.addFilter(WarningFilter())
    
    # Filter GenAI types warnings
    genai_logger = logging.getLogger("google.genai.types")
    genai_logger.setLevel(logging.ERROR)  # Only show errors, suppress warnings
    genai_logger.addFilter(WarningFilter())
    
    # Also add filter to root logger to catch any warnings
    root_logger = logging.getLogger()
    root_logger.addFilter(WarningFilter())
    
    # Create logger
    logger = logging.getLogger("factflow")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    logger.info("Logging configured successfully")
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Optional logger name (defaults to "factflow")
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"factflow.{name}")
    return logging.getLogger("factflow")


# Convenience function for agent-specific logging
def log_agent_action(
    agent_name: str,
    action: str,
    details: Optional[dict] = None,
    level: str = "INFO",
):
    """
    Log an agent action with structured details.
    
    Args:
        agent_name: Name of the agent
        action: Action being performed
        details: Optional dictionary with additional details
        level: Log level
    """
    logger = get_logger("agent")
    message = f"[{agent_name}] {action}"
    if details:
        message += f" | Details: {details}"
    
    getattr(logger, level.lower())(message)


def log_tool_call(
    tool_name: str,
    input_params: dict,
    output: dict,
    duration_ms: Optional[float] = None,
):
    """
    Log a tool call with input/output and timing.
    
    Args:
        tool_name: Name of the tool
        input_params: Input parameters
        output: Tool output
        duration_ms: Duration in milliseconds
    """
    logger = get_logger("tools")
    message = f"Tool: {tool_name} | Input: {input_params} | Output: {output}"
    if duration_ms:
        message += f" | Duration: {duration_ms:.2f}ms"
    logger.info(message)

