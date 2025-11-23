"""
Main entry point for FactFlow agent system.

This module provides a simple CLI interface for running the FactFlow agent.

Can be run from either:
- Parent directory: python -m factflow.main "query"
- Factflow directory: python main.py "query"
"""

import asyncio
import os
import sys
import warnings
from pathlib import Path
from contextlib import contextmanager
from io import StringIO
from dotenv import load_dotenv

# Add parent directory to path if running from factflow directory
# This allows imports to work in both cases
current_dir = Path(__file__).parent
if current_dir.name == "factflow":
    parent_dir = current_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

# Load environment variables
load_dotenv()

# Import after path manipulation
try:
    from factflow.agents.sentiment_agents import create_factflow_agent
    from factflow.session.session_manager import FactFlowSessionManager
    from factflow.session.memory_service import MemoryBank
    from factflow.observability.logging_config import setup_logging, get_logger
    from factflow.observability.tracing import TraceCollector
    from factflow.observability.metrics import MetricsCollector
except ImportError:
    # Fall back to relative imports if absolute imports fail
    from agents.sentiment_agents import create_factflow_agent
    from session.session_manager import FactFlowSessionManager
    from session.memory_service import MemoryBank
    from observability.logging_config import setup_logging, get_logger
    from observability.tracing import TraceCollector
    from observability.metrics import MetricsCollector


class FilteredStderr:
    """Custom stderr wrapper that filters out expected warning messages."""
    
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = StringIO()
    
    def write(self, text):
        """Write to stderr, filtering out expected warnings."""
        # Filter out the specific warning messages
        if "App name mismatch detected" in text:
            return
        if "there are non-text parts in the response" in text:
            return
        # Write everything else to original stderr
        self.original_stderr.write(text)
        self.original_stderr.flush()
    
    def flush(self):
        """Flush the original stderr."""
        self.original_stderr.flush()
    
    def __getattr__(self, name):
        """Delegate other attributes to original stderr."""
        return getattr(self.original_stderr, name)


@contextmanager
def suppress_expected_warnings():
    """Context manager to suppress expected warnings from Google ADK/GenAI libraries."""
    # Suppress app name mismatch warnings via warnings module
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*App name mismatch detected.*")
        warnings.filterwarnings("ignore", message=".*there are non-text parts in the response.*")
        # Also suppress at the logger level
        import logging
        adk_logger = logging.getLogger("google.adk.runners")
        genai_logger = logging.getLogger("google.genai.types")
        original_adk_level = adk_logger.level
        original_genai_level = genai_logger.level
        adk_logger.setLevel(logging.ERROR)
        genai_logger.setLevel(logging.ERROR)
        # Also filter stderr for print() statements
        original_stderr = sys.stderr
        filtered_stderr = FilteredStderr(original_stderr)
        sys.stderr = filtered_stderr
        try:
            yield
        finally:
            sys.stderr = original_stderr
            adk_logger.setLevel(original_adk_level)
            genai_logger.setLevel(original_genai_level)


async def main():
    """Main function to run FactFlow agent."""
    # Setup logging
    logger = setup_logging(log_level="INFO", log_file="logs/factflow.log")
    logger.info("Starting FactFlow agent system...")
    
    # Initialize components
    session_manager = FactFlowSessionManager()
    memory_bank = MemoryBank()
    trace_collector = TraceCollector(trace_file="logs/traces.json")
    metrics_collector = MetricsCollector(metrics_file="logs/metrics.json")
    
    # Get user query
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = input("Enter your query (e.g., 'Assess Ethereum right now'): ")
    
    # Get session ID (in production, this would come from user authentication)
    session_id = "default_session"
    
    # Start trace
    trace_id = trace_collector.start_trace(session_id, user_query)
    logger.info(f"Started trace: {trace_id}")
    
    try:
        # Get runner for this session
        runner = session_manager.get_runner(session_id)
        
        # Run the agent with session support
        # Use run_debug for prototyping (handles sessions automatically)
        # Suppress expected warnings from Google ADK/GenAI libraries
        logger.info(f"Processing query: {user_query}")
        with suppress_expected_warnings():
            response = await runner.run_debug(user_query)
        
        # Extract text from response (run_debug returns a list of response objects)
        # For SequentialAgent, we want only the final output (from the last agent - Judge Agent)
        response_text = ""
        if isinstance(response, list) and len(response) > 0:
            # Try to find the Judge Agent's output (starts with "## Sentiment-Reality Analysis")
            # If not found, use the last response item
            judge_output_found = False
            for item in reversed(response):  # Check from end to beginning
                if hasattr(item, 'content') and item.content:
                    if hasattr(item.content, 'parts') and item.content.parts:
                        item_text = ""
                        for part in item.content.parts:
                            # Skip function_call parts (they cause warnings but are normal)
                            if hasattr(part, 'text') and part.text:
                                item_text += part.text + "\n"
                            # Skip function_call and function_response parts
                            elif hasattr(part, 'function_call') or hasattr(part, 'function_response'):
                                continue
                        
                        # Check if this is the Judge Agent's output
                        if item_text.strip().startswith("## Sentiment-Reality Analysis"):
                            response_text = item_text
                            judge_output_found = True
                            break
                        elif not judge_output_found and item_text.strip():
                            # Use the last non-empty response as fallback
                            response_text = item_text
            
            # If we didn't find Judge output, use the last response
            if not response_text and len(response) > 0:
                last_item = response[-1]
                if hasattr(last_item, 'content') and last_item.content:
                    if hasattr(last_item.content, 'parts') and last_item.content.parts:
                        for part in last_item.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text + "\n"
        elif hasattr(response, 'content') and response.content:
            # Single response object - extract text from content parts to avoid function call warnings
            if hasattr(response.content, 'parts') and response.content.parts:
                for part in response.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text + "\n"
        elif hasattr(response, 'text'):
            # Only access .text if we're sure it won't trigger warnings
            # This is a fallback for simple response objects
            try:
                response_text = response.text
            except (AttributeError, Warning):
                response_text = str(response)
        else:
            response_text = str(response)
        
        # Clean up the response text
        response_text = response_text.strip()
        if not response_text:
            response_text = "Response received (check logs for details)"
        
        # End trace
        trace = trace_collector.end_trace(final_output=response_text)
        
        # Record metrics
        metrics_collector.record_query(success=True)
        
        # Store in memory bank (would extract structured data in production)
        # memory_bank.store_analysis(...)
        
        # Print response
        print("\n" + "="*80)
        print("FACTFLOW ANALYSIS")
        print("="*80)
        print(response_text)
        print()
        print("="*80)
        
        logger.info("Query processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        metrics_collector.record_error("query_processing", "main")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

