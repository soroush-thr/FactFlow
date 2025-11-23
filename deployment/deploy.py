"""
Deployment scripts for FactFlow agent system.

This module provides deployment functionality for Vertex AI Agent Engine
and other cloud-based runtimes.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def create_deployment_config(
    project_id: str,
    region: str = "us-central1",
    model_name: str = "gemini-2.5-flash-lite",
) -> Dict[str, Any]:
    """
    Create a deployment configuration for Vertex AI Agent Engine.
    
    Args:
        project_id: Google Cloud project ID
        region: Deployment region
        model_name: Gemini model to use
    
    Returns:
        Deployment configuration dictionary
    """
    config = {
        "project_id": project_id,
        "region": region,
        "agent": {
            "name": "factflow-agent",
            "model": model_name,
            "description": "FactFlow Sentiment-Reality Check Agent",
        },
        "environment": {
            "variables": {
                "GEMINI_API_KEY": "${GEMINI_API_KEY}",
                "LOG_LEVEL": "INFO",
            },
        },
        "scaling": {
            "min_instances": 1,
            "max_instances": 10,
        },
    }
    return config


def save_deployment_config(config: Dict[str, Any], file_path: str = "deployment/config.yaml"):
    """
    Save deployment configuration to YAML file.
    
    Args:
        config: Deployment configuration dictionary
        file_path: Path to save the configuration
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ Deployment configuration saved to {file_path}")


def deploy_to_agent_engine(
    config_path: str = "deployment/config.yaml",
    project_id: Optional[str] = None,
) -> None:
    """
    Deploy FactFlow agent to Vertex AI Agent Engine.
    
    This is a placeholder function. Actual deployment would use:
    - Google Cloud SDK (gcloud)
    - Vertex AI Agent Engine API
    - Cloud Run or similar runtime
    
    Args:
        config_path: Path to deployment configuration
        project_id: Optional project ID override
    """
    print("🚀 Deploying FactFlow agent to Vertex AI Agent Engine...")
    print("\n⚠️  This is a placeholder deployment function.")
    print("For actual deployment, you would:")
    print("1. Use gcloud CLI or Vertex AI API")
    print("2. Build and push container image")
    print("3. Deploy to Cloud Run or Agent Engine")
    print("4. Configure environment variables")
    print("5. Set up monitoring and logging")
    print("\nSee deployment/DEPLOYMENT.md for detailed instructions.")


def create_dockerfile(output_path: str = "Dockerfile") -> None:
    """
    Create a Dockerfile for FactFlow deployment.
    
    Args:
        output_path: Path to save the Dockerfile
    """
    dockerfile_content = """# FactFlow Agent Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "-m", "factflow.main"]
"""
    
    with open(output_path, "w") as f:
        f.write(dockerfile_content)
    
    print(f"✅ Dockerfile created at {output_path}")

