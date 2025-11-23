"""
Metrics collection for FactFlow agent system.

This module implements metrics collection to track system performance,
sentiment analysis accuracy, and divergence detection rates.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class MetricsCollector:
    """
    Collects metrics for the FactFlow agent system.
    
    Tracks:
    - Sentiment score distribution
    - Divergence detection rate
    - Tool call latency
    - Agent execution times
    - Error rates
    """
    
    def __init__(self, metrics_file: Optional[str] = None):
        """
        Initialize the metrics collector.
        
        Args:
            metrics_file: Optional file path to save metrics (JSON format)
        """
        self.metrics_file = metrics_file
        self.metrics: Dict[str, Any] = {
            "sentiment_scores": [],
            "divergence_detections": [],
            "tool_call_latencies": defaultdict(list),
            "agent_execution_times": defaultdict(list),
            "error_counts": defaultdict(int),
            "total_queries": 0,
            "successful_queries": 0,
        }
    
    def record_sentiment_score(self, score: float, asset: Optional[str] = None):
        """Record a sentiment score."""
        self.metrics["sentiment_scores"].append({
            "score": score,
            "asset": asset,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_metrics()
    
    def record_divergence(
        self,
        divergence_type: str,
        sentiment_score: float,
        price_change: float,
        asset: Optional[str] = None,
    ):
        """Record a divergence detection."""
        self.metrics["divergence_detections"].append({
            "divergence_type": divergence_type,
            "sentiment_score": sentiment_score,
            "price_change": price_change,
            "asset": asset,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_metrics()
    
    def record_tool_call(self, tool_name: str, duration_ms: float):
        """Record tool call latency."""
        self.metrics["tool_call_latencies"][tool_name].append(duration_ms)
        self._save_metrics()
    
    def record_agent_execution(self, agent_name: str, duration_ms: float):
        """Record agent execution time."""
        self.metrics["agent_execution_times"][agent_name].append(duration_ms)
        self._save_metrics()
    
    def record_error(self, error_type: str, agent_name: Optional[str] = None):
        """Record an error occurrence."""
        key = f"{agent_name}:{error_type}" if agent_name else error_type
        self.metrics["error_counts"][key] += 1
        self._save_metrics()
    
    def record_query(self, success: bool = True):
        """Record a query execution."""
        self.metrics["total_queries"] += 1
        if success:
            self.metrics["successful_queries"] += 1
        self._save_metrics()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of collected metrics."""
        summary = {
            "total_queries": self.metrics["total_queries"],
            "successful_queries": self.metrics["successful_queries"],
            "success_rate": (
                self.metrics["successful_queries"] / self.metrics["total_queries"]
                if self.metrics["total_queries"] > 0
                else 0
            ),
        }
        
        # Sentiment score statistics
        if self.metrics["sentiment_scores"]:
            scores = [m["score"] for m in self.metrics["sentiment_scores"]]
            summary["sentiment_stats"] = {
                "count": len(scores),
                "mean": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
            }
        
        # Divergence detection rate
        if self.metrics["divergence_detections"]:
            summary["divergence_detection_rate"] = (
                len(self.metrics["divergence_detections"]) / self.metrics["total_queries"]
                if self.metrics["total_queries"] > 0
                else 0
            )
        
        # Average tool call latencies
        summary["avg_tool_latencies"] = {}
        for tool_name, latencies in self.metrics["tool_call_latencies"].items():
            if latencies:
                summary["avg_tool_latencies"][tool_name] = sum(latencies) / len(latencies)
        
        # Average agent execution times
        summary["avg_agent_times"] = {}
        for agent_name, times in self.metrics["agent_execution_times"].items():
            if times:
                summary["avg_agent_times"][agent_name] = sum(times) / len(times)
        
        # Error counts
        summary["error_counts"] = dict(self.metrics["error_counts"])
        
        return summary
    
    def _save_metrics(self):
        """Save metrics to file."""
        if not self.metrics_file:
            return
        
        try:
            # Convert defaultdict to regular dict for JSON serialization
            metrics_to_save = {
                **self.metrics,
                "tool_call_latencies": dict(self.metrics["tool_call_latencies"]),
                "agent_execution_times": dict(self.metrics["agent_execution_times"]),
                "error_counts": dict(self.metrics["error_counts"]),
            }
            
            with open(self.metrics_file, "w") as f:
                json.dump(metrics_to_save, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save metrics: {e}")

