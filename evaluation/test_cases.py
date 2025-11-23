"""
Test cases for FactFlow agent evaluation.

This module contains predefined test cases with known outcomes
for evaluating agent performance.
"""

from typing import List, Dict, Any


def get_test_cases() -> List[Dict[str, Any]]:
    """
    Get a list of test cases for evaluation.
    
    Returns:
        List of test case dictionaries
    """
    return [
        {
            "name": "Bullish Divergence - Negative News, Stable Price",
            "query": "Assess Ethereum right now",
            "description": "Scenario where negative news exists but price remains stable",
            "expected_sentiment_range": (-8, -5),  # Negative sentiment
            "expected_price_change_range": (-2, 2),  # Stable price
            "expected_divergence_type": "bullish",
            "expected_recommendation": "HOLD or ACCUMULATE",
        },
        {
            "name": "Bearish Divergence - Positive News, Dropping Price",
            "query": "What's happening with Bitcoin?",
            "description": "Scenario where positive news exists but price is dropping",
            "expected_sentiment_range": (5, 8),  # Positive sentiment
            "expected_price_change_range": (-10, -5),  # Dropping price
            "expected_divergence_type": "bearish",
            "expected_recommendation": "SELL or HOLD",
        },
        {
            "name": "Confirmed Trend - Negative Sentiment, Negative Price",
            "query": "Analyze Solana",
            "description": "Scenario where sentiment and price align negatively",
            "expected_sentiment_range": (-8, -5),
            "expected_price_change_range": (-10, -5),
            "expected_divergence_type": "none",
            "expected_recommendation": "SELL or HOLD",
        },
        {
            "name": "Neutral Scenario",
            "query": "Check Cardano",
            "description": "Scenario with neutral sentiment and minimal price movement",
            "expected_sentiment_range": (-2, 2),
            "expected_price_change_range": (-2, 2),
            "expected_divergence_type": "none",
            "expected_recommendation": "HOLD",
        },
    ]

