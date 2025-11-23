"""
API client wrappers for external services.

This module provides low-level API client functions that are used by the market tools.
"""

import requests
from typing import Dict, Any, Optional
import os


class CoinGeckoClient:
    """Client for CoinGecko API (free tier, no authentication required)."""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    @staticmethod
    def get_price(asset_id: str) -> Dict[str, Any]:
        """Get price data for a cryptocurrency."""
        url = f"{CoinGeckoClient.BASE_URL}/simple/price"
        params = {
            "ids": asset_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()


class AlphaVantageClient:
    """Client for Alpha Vantage API (optional, requires API key)."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    @staticmethod
    def get_news_sentiment(keywords: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get news sentiment data from Alpha Vantage.
        
        Args:
            keywords: Keywords to search for (e.g., "Ethereum", "Bitcoin")
            api_key: Alpha Vantage API key (optional, can be set via env var)
        
        Returns:
            Dictionary with sentiment data
        """
        api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "error": "Alpha Vantage API key not provided. Set ALPHA_VANTAGE_API_KEY environment variable.",
            }
        
        params = {
            "function": "NEWS_SENTIMENT",
            "keywords": keywords,
            "apikey": api_key,
        }
        
        try:
            response = requests.get(AlphaVantageClient.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "status": "error",
                "error": f"Alpha Vantage API error: {str(e)}",
            }

