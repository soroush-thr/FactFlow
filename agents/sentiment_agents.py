"""
Sentiment-Reality Check Agent System.

This module implements a multi-agent system that compares news sentiment
with actual market price action to identify market inefficiencies.

Architecture:
1. News Scout Agent - Analyzes news sentiment using Google Search
2. Market Analyst Agent - Fetches real-time market data
3. Judge Agent - Synthesizes findings and provides recommendations
"""

import os
from typing import List, Optional
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search, FunctionTool
from google.genai import types

from ..tools.market_tools import (
    get_crypto_price_data,
    get_stock_data,
    get_tradfi_context,
)


# Retry configuration for API calls
retry_config = types.HttpRetryOptions(
    attempts=3,  # Maximum retry attempts
    exp_base=2,  # Delay multiplier
    initial_delay=1,  # Initial delay before first retry (in seconds)
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)


def create_news_scout_agent(model_name: str = "gemini-2.5-flash-lite") -> LlmAgent:
    """
    Create the News Scout Agent.
    
    This agent uses Google Search to find recent news headlines and analyzes
    their sentiment using LLM reasoning.
    
    Args:
        model_name: The Gemini model to use (default: gemini-2.5-flash-lite)
    
    Returns:
        Configured News Scout Agent
    """
    return LlmAgent(
        name="NewsScoutAgent",
        model=Gemini(
            model=model_name,
            retry_options=retry_config,
        ),
        instruction="""You are a specialized news sentiment analyst. Your job is to:

1. Use the google_search tool to find the top 5 most relevant news headlines 
   about the given asset from the last 24 hours. Search for: "[asset name] latest news today"
   
2. Analyze the sentiment of these headlines and assign a sentiment score from -10 to +10:
   - -10 to -7: Very Negative (e.g., major scandal, regulatory crackdown)
   - -6 to -3: Negative (e.g., concerns, minor issues)
   - -2 to +2: Neutral (e.g., routine updates, no strong sentiment)
   - +3 to +6: Positive (e.g., partnerships, positive developments)
   - +7 to +10: Very Positive (e.g., major adoption, breakthrough news)

3. Identify the key themes and reasons for the sentiment score.

4. Provide your analysis in this format:
   - Sentiment Score: [number]/10
   - Key Themes: [list of main themes]
   - Reasoning: [brief explanation of why this score]

Be objective and focus on factual news sentiment, not your own opinions.""",
        tools=[google_search],
        output_key="news_sentiment",  # Store result in session state
    )


def create_market_analyst_agent(model_name: str = "gemini-2.5-flash-lite") -> LlmAgent:
    """
    Create the Market Analyst Agent.
    
    This agent fetches real-time market data (price, volume, market cap) and
    analyzes market indicators to understand actual price action.
    
    Args:
        model_name: The Gemini model to use (default: gemini-2.5-flash-lite)
    
    Returns:
        Configured Market Analyst Agent
    """
    # Create function tools from our market tools
    crypto_tool = FunctionTool(get_crypto_price_data)
    stock_tool = FunctionTool(get_stock_data)
    tradfi_tool = FunctionTool(get_tradfi_context)
    
    return LlmAgent(
        name="MarketAnalystAgent",
        model=Gemini(
            model=model_name,
            retry_options=retry_config,
        ),
        instruction="""You are a specialized market data analyst. Your job is to:

1. Determine if the asset is a cryptocurrency or stock based on the user's query.
   - Cryptocurrencies: bitcoin, ethereum, btc, eth, solana, cardano, etc.
   - Stocks: AAPL, GOOGL, MSFT, TSLA, etc. (ticker symbols)

2. Use the appropriate tool to fetch market data:
   - For crypto: Use get_crypto_price_data(asset_name)
   - For stocks: Use get_stock_data(symbol)
   - Optionally: Use get_tradfi_context() to check if movements follow broader markets

3. After calling the tools, analyze the market data and provide your complete analysis in a clear text summary. Include:
   - Current Price in USD
   - 24h Price Change percentage  
   - Volume Status (above average / average / below average)
   - Market Cap if available
   - Market Context if tradfi data was checked
   - Price Action Interpretation (significant/moderate/minimal movement)
   - Volume Analysis (spiking/normal/low)
   - Market Correlation (crypto-specific / following traditional markets / independent)

4. CRITICAL: After using tools, you MUST write a complete text summary as your final response. 
   Do not just call tools - you must analyze the tool results and write a summary. 
   Your final text response will be stored with key "market_data" for the next agent. 
   Even if tool calls fail, write a summary with whatever information you have.""",
        tools=[crypto_tool, stock_tool, tradfi_tool],
        output_key="market_data",  # Store result in session state
    )


def create_judge_agent(model_name: str = "gemini-2.5-flash-lite") -> LlmAgent:
    """
    Create the Judge Agent.
    
    This agent synthesizes the news sentiment and market data to identify
    divergences and provide Buy/Sell/Hold recommendations.
    
    Args:
        model_name: The Gemini model to use (default: gemini-2.5-flash-lite)
    
    Returns:
        Configured Judge Agent
    """
    return LlmAgent(
        name="JudgeAgent",
        model=Gemini(
            model=model_name,
            retry_options=retry_config,
        ),
        instruction="""You are a market intelligence judge. Your job is to synthesize
information from the News Scout and Market Analyst agents to identify market inefficiencies.

You will receive:
- {news_sentiment}: The sentiment analysis from the News Scout Agent

You should also have access to market data from the Market Analyst Agent. Use it if available.

IMPORTANT: 
- Always use {news_sentiment} which should be available
- Check if market data is available from the previous agent's output
- If market data is available, use both sentiment and market data for your analysis
- If market data is NOT available, proceed with just {news_sentiment} and note in your analysis that market data was unavailable - you can still provide a recommendation based on sentiment alone

Your task:

1. Compare the sentiment score with the actual price action:
   - If sentiment is very negative (-8 to -10) but price is stable/flat: This is a BULLISH DIVERGENCE
   - If sentiment is very positive (+8 to +10) but price is dropping: This is a BEARISH DIVERGENCE
   - If sentiment and price align: This is CONFIRMED TREND

2. Identify the type of divergence:
   - Bullish Divergence: Market is ignoring bad news (strong holder confidence)
   - Bearish Divergence: Market is ignoring good news (weak fundamentals or selling pressure)
   - Confirmed Trend: Sentiment and price are aligned

3. Provide a clear recommendation:
   - BUY: When there's a bullish divergence or strong positive alignment
   - SELL: When there's a bearish divergence or strong negative alignment
   - HOLD: When signals are mixed or unclear
   - ACCUMULATE: When there's a bullish divergence (buy gradually)

4. Format your final output as:
   ## Sentiment-Reality Analysis

   **Sentiment Score:** [score]/10
   **Price Action:** [24h change]%
   **Divergence Type:** [Bullish/Bearish/None]
   
   **Analysis:**
   [Your detailed analysis explaining the divergence or alignment]
   
   **Recommendation:** [BUY/SELL/HOLD/ACCUMULATE]
   
   **Reasoning:**
   [Clear explanation of why this recommendation makes sense]

Be objective, data-driven, and focus on the gap between sentiment and reality.""",
        output_key="final_recommendation",  # Store final result
    )


def create_factflow_agent(
    model_name: str = "gemini-2.5-flash-lite",
    use_sequential: bool = True,
) -> SequentialAgent:
    """
    Create the complete FactFlow agent system.
    
    This function creates a sequential multi-agent system that orchestrates
    the News Scout, Market Analyst, and Judge agents.
    
    Args:
        model_name: The Gemini model to use for all agents
        use_sequential: If True, use SequentialAgent (guaranteed order).
                       If False, use LLM-based coordinator (more flexible but less predictable)
    
    Returns:
        Configured FactFlow agent system
    """
    # Create individual agents
    news_scout = create_news_scout_agent(model_name)
    market_analyst = create_market_analyst_agent(model_name)
    judge = create_judge_agent(model_name)
    
    if use_sequential:
        # Use SequentialAgent for guaranteed execution order
        return SequentialAgent(
            name="FactFlowAgent",
            sub_agents=[news_scout, market_analyst, judge],
        )
    else:
        # Alternative: Use LLM-based coordinator (less predictable but more flexible)
        # This is shown for educational purposes but SequentialAgent is recommended
        from google.adk.agents import LlmAgent as CoordinatorAgent
        from google.adk.tools import AgentTool
        
        coordinator = CoordinatorAgent(
            name="FactFlowCoordinator",
            model=Gemini(
                model=model_name,
                retry_options=retry_config,
            ),
            instruction="""You are the FactFlow coordinator. Your job is to orchestrate
the analysis workflow:

1. First, call NewsScoutAgent to analyze news sentiment
2. Then, call MarketAnalystAgent to get market data
3. Finally, call JudgeAgent to synthesize and provide recommendations

Present the final recommendation clearly to the user.""",
            tools=[
                AgentTool(news_scout),
                AgentTool(market_analyst),
                AgentTool(judge),
            ],
        )
        return coordinator


# Convenience aliases for easier imports
NewsScoutAgent = create_news_scout_agent
MarketAnalystAgent = create_market_analyst_agent
JudgeAgent = create_judge_agent

