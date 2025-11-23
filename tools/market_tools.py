"""
Market data tools for FactFlow agent system.

This module provides custom function tools for fetching market data from various APIs.
All tools follow ADK best practices: type hints, docstrings, and structured returns.
"""

import requests
from typing import Dict, Any, Optional
import yfinance as yf
from datetime import datetime, timedelta


def get_crypto_price_data(asset: str) -> Dict[str, Any]:
    """
    Fetch real-time cryptocurrency market data from CoinGecko API.
    
    This tool retrieves current price, 24h price change, volume, and market cap
    for a given cryptocurrency. CoinGecko free tier doesn't require an API key.
    
    Args:
        asset: The cryptocurrency symbol or name (e.g., "ethereum", "bitcoin", "eth")
               Case-insensitive. Supports both full names and symbols.
    
    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - asset: The asset name (normalized)
        - current_price: Current price in USD
        - price_change_24h: 24-hour price change percentage
        - volume_24h: 24-hour trading volume in USD
        - market_cap: Market capitalization in USD
        - last_updated: Timestamp of the data
        - error: Error message if status is "error"
    
    Example:
        >>> result = get_crypto_price_data("ethereum")
        >>> print(result["current_price"])
        2500.50
    """
    try:
        # Normalize asset name (common mappings)
        asset_lower = asset.lower().strip()
        asset_mapping = {
            "eth": "ethereum",
            "btc": "bitcoin",
            "bnb": "binancecoin",
            "sol": "solana",
            "ada": "cardano",
            "dot": "polkadot",
            "matic": "matic-network",
            "avax": "avalanche-2",
        }
        
        asset_id = asset_mapping.get(asset_lower, asset_lower)
        
        # CoinGecko API endpoint (free tier, no key required)
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": asset_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if asset_id not in data:
            return {
                "status": "error",
                "error": f"Asset '{asset}' not found. Please check the asset name.",
                "asset": asset,
            }
        
        asset_data = data[asset_id]
        
        return {
            "status": "success",
            "asset": asset_id,
            "current_price": asset_data.get("usd", 0),
            "price_change_24h": asset_data.get("usd_24h_change", 0),
            "volume_24h": asset_data.get("usd_24h_vol", 0),
            "market_cap": asset_data.get("usd_market_cap", 0),
            "last_updated": datetime.now().isoformat(),
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "asset": asset,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "asset": asset,
        }


def get_stock_data(symbol: str) -> Dict[str, Any]:
    """
    Fetch real-time stock market data using yfinance library.
    
    This tool retrieves current price, 24h price change, volume, and market cap
    for a given stock symbol.
    
    Args:
        symbol: The stock ticker symbol (e.g., "AAPL", "GOOGL", "MSFT")
                Case-insensitive.
    
    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - symbol: The stock symbol (normalized)
        - current_price: Current price in USD
        - price_change_24h: 24-hour price change percentage
        - volume: Trading volume
        - market_cap: Market capitalization in USD
        - last_updated: Timestamp of the data
        - error: Error message if status is "error"
    
    Example:
        >>> result = get_stock_data("AAPL")
        >>> print(result["current_price"])
        175.50
    """
    try:
        symbol_upper = symbol.upper().strip()
        ticker = yf.Ticker(symbol_upper)
        
        # Get current info
        info = ticker.info
        
        # Get recent price data (last 2 days to calculate 24h change)
        hist = ticker.history(period="2d", interval="1h")
        
        if hist.empty:
            return {
                "status": "error",
                "error": f"Stock symbol '{symbol}' not found or no data available.",
                "symbol": symbol_upper,
            }
        
        current_price = hist["Close"].iloc[-1]
        previous_price = hist["Close"].iloc[0] if len(hist) > 1 else current_price
        price_change_24h = ((current_price - previous_price) / previous_price) * 100 if previous_price > 0 else 0
        
        # Get volume (most recent)
        volume = hist["Volume"].iloc[-1] if "Volume" in hist.columns else 0
        
        # Market cap from info if available
        market_cap = info.get("marketCap", 0)
        
        return {
            "status": "success",
            "symbol": symbol_upper,
            "current_price": float(current_price),
            "price_change_24h": float(price_change_24h),
            "volume": float(volume),
            "market_cap": float(market_cap) if market_cap else 0,
            "last_updated": datetime.now().isoformat(),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error fetching stock data: {str(e)}",
            "symbol": symbol,
        }


def get_tradfi_context() -> Dict[str, Any]:
    """
    Fetch traditional finance (TradFi) market context.
    
    This tool retrieves S&P 500 and NASDAQ data to check if crypto movements
    are following traditional market trends. This helps distinguish crypto-specific
    news from broader market movements.
    
    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - sp500_change: S&P 500 24h change percentage
        - nasdaq_change: NASDAQ 24h change percentage
        - correlation_indicator: "positive", "negative", or "divergent"
        - last_updated: Timestamp of the data
        - error: Error message if status is "error"
    
    Example:
        >>> result = get_tradfi_context()
        >>> print(result["sp500_change"])
        -0.5
    """
    try:
        # Get S&P 500 data
        sp500 = yf.Ticker("^GSPC")
        nasdaq = yf.Ticker("^IXIC")
        
        # Get last 2 days of data
        sp500_hist = sp500.history(period="2d", interval="1h")
        nasdaq_hist = nasdaq.history(period="2d", interval="1h")
        
        if sp500_hist.empty or nasdaq_hist.empty:
            return {
                "status": "error",
                "error": "Unable to fetch TradFi market data.",
            }
        
        # Calculate 24h changes
        sp500_current = sp500_hist["Close"].iloc[-1]
        sp500_previous = sp500_hist["Close"].iloc[0] if len(sp500_hist) > 1 else sp500_current
        sp500_change = ((sp500_current - sp500_previous) / sp500_previous) * 100 if sp500_previous > 0 else 0
        
        nasdaq_current = nasdaq_hist["Close"].iloc[-1]
        nasdaq_previous = nasdaq_hist["Close"].iloc[0] if len(nasdaq_hist) > 1 else nasdaq_current
        nasdaq_change = ((nasdaq_current - nasdaq_previous) / nasdaq_previous) * 100 if nasdaq_previous > 0 else 0
        
        # Determine correlation indicator
        if (sp500_change > 0 and nasdaq_change > 0) or (sp500_change < 0 and nasdaq_change < 0):
            correlation = "positive"
        elif abs(sp500_change) < 0.1 and abs(nasdaq_change) < 0.1:
            correlation = "neutral"
        else:
            correlation = "divergent"
        
        return {
            "status": "success",
            "sp500_change": float(sp500_change),
            "nasdaq_change": float(nasdaq_change),
            "correlation_indicator": correlation,
            "last_updated": datetime.now().isoformat(),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error fetching TradFi context: {str(e)}",
        }

