"""
Agent evaluation framework for FactFlow.

This module implements LLM-as-a-Judge evaluation to assess the quality
of agent recommendations and sentiment analysis.
"""

from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

retry_config = types.HttpRetryOptions(
    attempts=3,  # Maximum retry attempts
    exp_base=2,  # Delay multiplier
    initial_delay=1,  # Initial delay before first retry (in seconds)
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)


def create_evaluation_agent(model_name: str = "gemini-2.5-flash-lite") -> LlmAgent:
    """
    Create an evaluation agent using LLM-as-a-Judge pattern.
    
    This agent evaluates the quality of FactFlow recommendations by
    assessing sentiment analysis accuracy, divergence detection correctness,
    and recommendation reasoning quality.
    
    Args:
        model_name: The Gemini model to use
    
    Returns:
        Configured evaluation agent
    """
    return LlmAgent(
        name="EvaluationAgent",
        model=Gemini(
            model=model_name,
            retry_options=retry_config,
        ),
        instruction="""You are an expert evaluator for market analysis agents.
Your job is to evaluate the quality of sentiment-reality analysis recommendations.

You will receive:
1. The original user query
2. The agent's sentiment analysis
3. The agent's market data analysis
4. The agent's final recommendation

Evaluate the agent's performance on these criteria:

**1. Sentiment Analysis Accuracy (0-10 points)**
- Did the agent correctly identify the sentiment of the news?
- Is the sentiment score (-10 to +10) reasonable given the news?
- Are the key themes accurately identified?

**2. Divergence Detection Correctness (0-10 points)**
- Did the agent correctly identify if there's a divergence between sentiment and price?
- Is the divergence type (bullish/bearish/none) correctly identified?
- Is the reasoning sound?

**3. Recommendation Quality (0-10 points)**
- Is the recommendation (BUY/SELL/HOLD/ACCUMULATE) appropriate given the analysis?
- Is the reasoning clear and well-justified?
- Does it align with the divergence detection?

**4. Tool Usage Correctness (0-10 points)**
- Were the right tools called?
- Were tool outputs correctly interpreted?
- Was market data properly analyzed?

Provide your evaluation in this format:

## Evaluation Results

**Overall Score: [0-40 points]**

**Breakdown:**
- Sentiment Analysis Accuracy: [0-10] - [brief explanation]
- Divergence Detection: [0-10] - [brief explanation]
- Recommendation Quality: [0-10] - [brief explanation]
- Tool Usage: [0-10] - [brief explanation]

**Strengths:**
[List what the agent did well]

**Areas for Improvement:**
[List specific areas that could be improved]

**Final Verdict:**
[Overall assessment and any critical issues]

Be objective, thorough, and constructive in your evaluation.""",
    )


class FactFlowEvaluator:
    """
    Evaluator for FactFlow agent system.
    
    Uses LLM-as-a-Judge pattern to evaluate agent performance on test cases.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        """Initialize the evaluator."""
        self.evaluation_agent = create_evaluation_agent(model_name)
        self.test_cases: List[Dict[str, Any]] = []
        self.evaluation_results: List[Dict[str, Any]] = []
    
    def add_test_case(
        self,
        query: str,
        expected_sentiment_range: tuple,
        expected_divergence_type: Optional[str] = None,
        expected_recommendation: Optional[str] = None,
        ground_truth: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a test case for evaluation.
        
        Args:
            query: User query to test
            expected_sentiment_range: Expected sentiment score range (min, max)
            expected_divergence_type: Expected divergence type (if any)
            expected_recommendation: Expected recommendation
            ground_truth: Optional ground truth data for comparison
        """
        self.test_cases.append({
            "query": query,
            "expected_sentiment_range": expected_sentiment_range,
            "expected_divergence_type": expected_divergence_type,
            "expected_recommendation": expected_recommendation,
            "ground_truth": ground_truth or {},
        })
    
    async def evaluate_agent_response(
        self,
        query: str,
        agent_response: Dict[str, Any],
        test_case: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate an agent's response using LLM-as-a-Judge.
        
        Args:
            query: Original user query
            agent_response: Agent's response containing sentiment, market data, and recommendation
            test_case: Optional test case with expected values
        
        Returns:
            Evaluation results dictionary
        """
        from google.adk.runners import InMemoryRunner
        
        # Prepare evaluation prompt
        evaluation_prompt = f"""Evaluate this agent response:

**User Query:** {query}

**Agent Response:**
- Sentiment Analysis: {agent_response.get('news_sentiment', 'N/A')}
- Market Data: {agent_response.get('market_data', 'N/A')}
- Final Recommendation: {agent_response.get('final_recommendation', 'N/A')}

"""
        
        if test_case:
            evaluation_prompt += f"""
**Expected Values:**
- Sentiment Range: {test_case.get('expected_sentiment_range', 'N/A')}
- Expected Divergence: {test_case.get('expected_divergence_type', 'N/A')}
- Expected Recommendation: {test_case.get('expected_recommendation', 'N/A')}

"""
        
        # Run evaluation
        runner = InMemoryRunner(agent=self.evaluation_agent)
        evaluation_result = await runner.run(evaluation_prompt)
        
        result = {
            "query": query,
            "agent_response": agent_response,
            "evaluation": evaluation_result.text,
            "test_case": test_case,
        }
        
        self.evaluation_results.append(result)
        return result
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get a summary of all evaluations."""
        if not self.evaluation_results:
            return {"message": "No evaluations performed yet"}
        
        # Extract scores from evaluations (would need parsing in production)
        total_evaluations = len(self.evaluation_results)
        
        return {
            "total_evaluations": total_evaluations,
            "evaluation_results": self.evaluation_results,
        }

