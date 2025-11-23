"""
Memory Bank implementation for FactFlow.

This module implements long-term memory storage for the FactFlow agent system,
allowing it to remember historical analyses, user preferences, and patterns
across different sessions.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class MemoryBank:
    """
    Long-term memory storage for FactFlow agent system.
    
    This class implements a Memory Bank pattern that stores:
    - Historical analyses (sentiment scores, recommendations)
    - User preferences (favorite assets, alert thresholds)
    - Divergence patterns (historical cases of sentiment-reality gaps)
    
    The memory persists across sessions using JSON file storage.
    """
    
    def __init__(self, storage_path: str = "factflow_memory.json"):
        """
        Initialize the Memory Bank.
        
        Args:
            storage_path: Path to the JSON file for persistent storage
        """
        self.storage_path = Path(storage_path)
        self.memory: Dict[str, Any] = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load memory: {e}")
                return self._create_empty_memory()
        return self._create_empty_memory()
    
    def _create_empty_memory(self) -> Dict[str, Any]:
        """Create an empty memory structure."""
        return {
            "analyses": [],  # Historical analyses
            "user_preferences": {},  # User-specific preferences
            "divergence_patterns": [],  # Historical divergence cases
            "asset_tracking": {},  # Track assets over time
        }
    
    def _save_memory(self):
        """Save memory to disk."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save memory: {e}")
    
    def store_analysis(
        self,
        asset: str,
        sentiment_score: float,
        price_change: float,
        recommendation: str,
        divergence_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Store a completed analysis in memory.
        
        Args:
            asset: The asset that was analyzed
            sentiment_score: Sentiment score from -10 to +10
            price_change: 24h price change percentage
            recommendation: Final recommendation (BUY/SELL/HOLD/ACCUMULATE)
            divergence_type: Type of divergence detected (if any)
            user_id: Optional user identifier for personalization
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "asset": asset,
            "sentiment_score": sentiment_score,
            "price_change": price_change,
            "recommendation": recommendation,
            "divergence_type": divergence_type,
            "user_id": user_id,
        }
        
        self.memory["analyses"].append(analysis)
        
        # Update asset tracking
        if asset not in self.memory["asset_tracking"]:
            self.memory["asset_tracking"][asset] = {
                "first_analyzed": analysis["timestamp"],
                "analysis_count": 0,
                "last_analyzed": None,
            }
        
        self.memory["asset_tracking"][asset]["analysis_count"] += 1
        self.memory["asset_tracking"][asset]["last_analyzed"] = analysis["timestamp"]
        
        # Store divergence patterns if detected
        if divergence_type:
            self.memory["divergence_patterns"].append({
                "timestamp": analysis["timestamp"],
                "asset": asset,
                "divergence_type": divergence_type,
                "sentiment_score": sentiment_score,
                "price_change": price_change,
            })
        
        self._save_memory()
    
    def get_asset_history(self, asset: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get historical analyses for a specific asset.
        
        Args:
            asset: The asset name
            limit: Maximum number of analyses to return
        
        Returns:
            List of historical analyses, most recent first
        """
        asset_analyses = [
            a for a in self.memory["analyses"]
            if a["asset"].lower() == asset.lower()
        ]
        return sorted(asset_analyses, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_divergence_patterns(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get historical divergence patterns.
        
        Args:
            limit: Maximum number of patterns to return
        
        Returns:
            List of divergence patterns, most recent first
        """
        return sorted(
            self.memory["divergence_patterns"],
            key=lambda x: x["timestamp"],
            reverse=True,
        )[:limit]
    
    def set_user_preference(self, user_id: str, key: str, value: Any) -> None:
        """
        Store a user preference.
        
        Args:
            user_id: User identifier
            key: Preference key (e.g., "favorite_assets", "alert_threshold")
            value: Preference value
        """
        if user_id not in self.memory["user_preferences"]:
            self.memory["user_preferences"][user_id] = {}
        
        self.memory["user_preferences"][user_id][key] = value
        self._save_memory()
    
    def get_user_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Get a user preference.
        
        Args:
            user_id: User identifier
            key: Preference key
            default: Default value if preference doesn't exist
        
        Returns:
            Preference value or default
        """
        return self.memory["user_preferences"].get(user_id, {}).get(key, default)
    
    def get_context_summary(self, asset: Optional[str] = None) -> str:
        """
        Generate a context summary for the agent.
        
        This can be used for context engineering - providing relevant
        historical context to the agent without overwhelming it.
        
        Args:
            asset: Optional asset to focus the summary on
        
        Returns:
            Formatted context summary string
        """
        if asset:
            history = self.get_asset_history(asset, limit=5)
            if history:
                summary = f"Historical analysis for {asset}:\n"
                for analysis in history:
                    summary += f"- {analysis['timestamp']}: Sentiment {analysis['sentiment_score']}/10, "
                    summary += f"Price {analysis['price_change']:.2f}%, "
                    summary += f"Recommendation: {analysis['recommendation']}\n"
                return summary
        
        # General summary
        total_analyses = len(self.memory["analyses"])
        total_divergences = len(self.memory["divergence_patterns"])
        
        return (
            f"Memory Bank Summary: {total_analyses} total analyses, "
            f"{total_divergences} divergence patterns detected."
        )

