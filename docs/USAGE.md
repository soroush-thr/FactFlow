# FactFlow Usage Guide

This guide explains how to use the FactFlow agent system for sentiment-reality analysis.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Advanced Features](#advanced-features)
3. [Examples](#examples)
4. [Best Practices](#best-practices)
5. [API Reference](#api-reference)

## Basic Usage

### Command Line Interface

The simplest way to use FactFlow is through the command line:

```bash
# Single query
python -m factflow.main "Assess Ethereum right now"

# Interactive mode
python -m factflow.main
```

### Python API

For programmatic usage:

```python
import asyncio
from factflow import create_factflow_agent, FactFlowSessionManager

async def analyze_asset():
    # Create session manager
    session_manager = FactFlowSessionManager()
    
    # Get runner for a session
    runner = session_manager.get_runner(session_id="user123")
    
    # Run query
    response = await runner.run("Assess Ethereum right now")
    
    # Print result
    print(response.text)
    
    return response

# Run
result = asyncio.run(analyze_asset())
```

### Jupyter Notebook

See `notebooks/factflow_demo.ipynb` for a complete interactive example.

## Advanced Features

### Session Management

FactFlow supports multi-turn conversations through session management:

```python
from factflow.session.session_manager import FactFlowSessionManager

session_manager = FactFlowSessionManager()
runner = session_manager.get_runner(session_id="user123")

# First query
response1 = await runner.run("Assess Ethereum")

# Follow-up query (agent remembers context)
response2 = await runner.run("What about Bitcoin?")
```

### Memory Bank

Store and retrieve historical analyses:

```python
from factflow.session.memory_service import MemoryBank

memory = MemoryBank()

# Store an analysis
memory.store_analysis(
    asset="ethereum",
    sentiment_score=-8.0,
    price_change=-0.5,
    recommendation="HOLD",
    divergence_type="bullish",
)

# Get asset history
history = memory.get_asset_history("ethereum", limit=10)
print(history)

# Get divergence patterns
patterns = memory.get_divergence_patterns(limit=20)
print(patterns)
```

### Observability

Enable logging, tracing, and metrics:

```python
from factflow.observability import (
    setup_logging,
    TraceCollector,
    MetricsCollector,
)

# Setup logging
logger = setup_logging(log_level="INFO", log_file="logs/factflow.log")

# Create trace collector
trace_collector = TraceCollector(trace_file="logs/traces.json")

# Start trace
trace_id = trace_collector.start_trace("session123", "Assess Ethereum")

# ... run agent ...

# End trace
trace = trace_collector.end_trace(final_output="...")

# Metrics
metrics = MetricsCollector(metrics_file="logs/metrics.json")
metrics.record_sentiment_score(-8.0, asset="ethereum")
metrics.record_divergence("bullish", -8.0, -0.5, "ethereum")

# Get summary
summary = metrics.get_summary()
print(summary)
```

### Agent Evaluation

Evaluate agent performance using LLM-as-a-Judge:

```python
from factflow.evaluation import FactFlowEvaluator

evaluator = FactFlowEvaluator()

# Add test case
evaluator.add_test_case(
    query="Assess Ethereum right now",
    expected_sentiment_range=(-8, -5),
    expected_divergence_type="bullish",
    expected_recommendation="HOLD",
)

# Evaluate agent response
result = await evaluator.evaluate_agent_response(
    query="Assess Ethereum right now",
    agent_response={
        "news_sentiment": -8.0,
        "market_data": {"price_change": -0.5},
        "final_recommendation": "HOLD",
    },
)

print(result["evaluation"])
```

## Examples

### Example 1: Basic Asset Analysis

```python
import asyncio
from factflow import FactFlowSessionManager

async def analyze_crypto():
    session_manager = FactFlowSessionManager()
    runner = session_manager.get_runner("demo")
    
    queries = [
        "Assess Ethereum right now",
        "What's happening with Bitcoin?",
        "Analyze Solana",
    ]
    
    for query in queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        response = await runner.run(query)
        print(response.text)

asyncio.run(analyze_crypto())
```

### Example 2: Stock Analysis

```python
import asyncio
from factflow import FactFlowSessionManager

async def analyze_stocks():
    session_manager = FactFlowSessionManager()
    runner = session_manager.get_runner("stocks")
    
    stocks = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    
    for stock in stocks:
        query = f"Analyze {stock} stock"
        response = await runner.run(query)
        print(f"\n{stock} Analysis:")
        print(response.text)

asyncio.run(analyze_stocks())
```

### Example 3: Batch Analysis with Memory

```python
import asyncio
from factflow import FactFlowSessionManager
from factflow.session.memory_service import MemoryBank

async def batch_analysis():
    session_manager = FactFlowSessionManager()
    memory = MemoryBank()
    
    assets = ["ethereum", "bitcoin", "solana"]
    
    for asset in assets:
        runner = session_manager.get_runner(f"batch_{asset}")
        query = f"Assess {asset} right now"
        response = await runner.run(query)
        
        # Store in memory (would extract structured data in production)
        # memory.store_analysis(...)
        
        print(f"\n{asset.upper()} Analysis:")
        print(response.text)
        
        # Get historical context
        history = memory.get_asset_history(asset, limit=5)
        if history:
            print(f"\nPrevious analyses: {len(history)}")

asyncio.run(batch_analysis())
```

### Example 4: Custom Agent Configuration

```python
from factflow.agents.sentiment_agents import create_factflow_agent

# Create agent with custom model
agent = create_factflow_agent(model_name="gemini-1.5-pro")

# Use with custom runner
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(agent=agent)
response = await runner.run("Assess Ethereum right now")
print(response.text)
```

## Best Practices

### 1. Query Formulation

**Good queries:**
- "Assess Ethereum right now"
- "What's happening with Bitcoin?"
- "Analyze Solana market sentiment"

**Avoid:**
- "ETH" (use full name "Ethereum")
- "Tell me everything" (too vague)
- Multiple assets in one query (process separately)

### 2. Session Management

- Use unique session IDs for different users
- Reuse sessions for follow-up questions
- Clear sessions when starting new conversations

### 3. Error Handling

```python
try:
    response = await runner.run(query)
    print(response.text)
except Exception as e:
    logger.error(f"Error processing query: {e}")
    # Handle error appropriately
```

### 4. Rate Limiting

- Don't make too many requests in quick succession
- Use the Memory Bank to cache results
- Implement delays between batch operations

### 5. Monitoring

- Enable logging for production use
- Monitor metrics for performance
- Review traces for debugging

## API Reference

### Main Classes

#### `FactFlowSessionManager`

Manages agent sessions for multi-turn conversations.

```python
session_manager = FactFlowSessionManager(model_name="gemini-2.5-flash-lite")
runner = session_manager.get_runner(session_id="user123")
response = await runner.run("Query here")
```

#### `MemoryBank`

Stores and retrieves historical analyses.

```python
memory = MemoryBank(storage_path="memory.json")
memory.store_analysis(asset, sentiment_score, price_change, recommendation)
history = memory.get_asset_history(asset, limit=10)
```

#### `TraceCollector`

Collects execution traces for debugging.

```python
collector = TraceCollector(trace_file="traces.json")
trace_id = collector.start_trace(session_id, query)
# ... run agent ...
trace = collector.end_trace(final_output)
```

#### `MetricsCollector`

Collects performance metrics.

```python
metrics = MetricsCollector(metrics_file="metrics.json")
metrics.record_sentiment_score(score, asset)
metrics.record_divergence(divergence_type, sentiment, price_change)
summary = metrics.get_summary()
```

### Tool Functions

#### `get_crypto_price_data(asset: str) -> dict`

Fetches cryptocurrency market data from CoinGecko.

```python
from factflow.tools.market_tools import get_crypto_price_data

result = get_crypto_price_data("ethereum")
# Returns: {"status": "success", "current_price": 2500.50, ...}
```

#### `get_stock_data(symbol: str) -> dict`

Fetches stock market data using yfinance.

```python
from factflow.tools.market_tools import get_stock_data

result = get_stock_data("AAPL")
# Returns: {"status": "success", "current_price": 175.50, ...}
```

#### `get_tradfi_context() -> dict`

Fetches traditional finance market context (S&P 500, NASDAQ).

```python
from factflow.tools.market_tools import get_tradfi_context

result = get_tradfi_context()
# Returns: {"sp500_change": -0.5, "nasdaq_change": -0.3, ...}
```

## Next Steps

- Review the demo notebook: `notebooks/factflow_demo.ipynb`
- Check out the evaluation framework: `evaluation/evaluator.py`
- Read the submission guide: [SUBMISSION.md](SUBMISSION.md)

