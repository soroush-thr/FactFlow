"""
Deployment scripts for FactFlow agent system.

This module provides deployment functionality for Vertex AI Agent Engine
and other cloud-based runtimes.
"""

import os
import sys
import subprocess
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


def validate_environment() -> bool:
    """
    Validate deployment environment.
    
    Returns:
        True if environment is valid, False otherwise
    """
    print("🔍 Validating deployment environment...")
    
    # Check for GEMINI_API_KEY
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ GEMINI_API_KEY not set or invalid")
        print("   Set it in .env file or environment: export GEMINI_API_KEY=your_key")
        return False
    print("✅ GEMINI_API_KEY found")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, found {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check required packages
    required_packages = ["google.adk", "google.generativeai", "yaml"]
    missing = []
    for package in required_packages:
        try:
            if package == "google.adk":
                __import__("google.adk")
            elif package == "google.generativeai":
                __import__("google.generativeai")
            elif package == "yaml":
                __import__("yaml")
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    print("✅ Required packages installed")
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print("✅ Logs directory ready")
    
    return True


def deploy_to_agent_engine(
    config_path: str = "deployment/config.yaml",
    project_id: Optional[str] = None,
    test_query: Optional[str] = None,
) -> None:
    """
    Minimal deployment for FactFlow agent.
    
    Validates environment and provides deployment options.
    
    Args:
        config_path: Path to deployment configuration
        project_id: Optional project ID override
        test_query: Optional test query to run after deployment
    """
    print("🚀 Minimal FactFlow Deployment\n")
    
    # Validate environment
    if not validate_environment():
        print("\n❌ Deployment validation failed. Fix issues above and try again.")
        sys.exit(1)
    
    print("\n✅ Environment validated successfully!")
    
    # Create deployment config if it doesn't exist
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"\n📝 Creating deployment config...")
        if project_id:
            config = create_deployment_config(project_id=project_id)
        else:
            # Use default config
            config = create_deployment_config(project_id="your-project-id")
        save_deployment_config(config, config_path)
    else:
        print(f"✅ Config exists: {config_path}")
    
    print("\n🎯 Deployment ready! Options:")
    print("\n1. Run locally:")
    print("   python -m factflow.main \"Your query here\"")
    
    print("\n2. Test deployment:")
    if test_query:
        print(f"   Testing with query: '{test_query}'")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "factflow.main", test_query],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=False,
                text=True
            )
            if result.returncode == 0:
                print("   ✅ Test completed successfully")
            else:
                print(f"   ⚠️  Test completed with exit code {result.returncode}")
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    else:
        print("   python -m factflow.deployment.deploy --test \"Assess Ethereum right now\"")
    
    print("\n3. Docker deployment:")
    # Check if Dockerfile exists and is valid
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        print("   📝 Creating Dockerfile...")
        create_dockerfile("Dockerfile")
    else:
        # Validate Dockerfile doesn't reference non-existent web server
        dockerfile_content = dockerfile_path.read_text()
        if "gunicorn" in dockerfile_content or "app:app" in dockerfile_content:
            print("   ⚠️  Dockerfile references web server (gunicorn/app:app) but this is a CLI app")
            print("   📝 Updating Dockerfile for CLI usage...")
            create_dockerfile("Dockerfile")
        else:
            print("   ✅ Dockerfile exists and looks valid")
    
    print("   Build: docker build -t factflow-agent .")
    print("   Run:   docker run -e GEMINI_API_KEY=$GEMINI_API_KEY factflow-agent \"Your query\"")
    
    print("\n✅ Minimal deployment complete!")


def create_dockerfile(output_path: str = "Dockerfile") -> None:
    """
    Create a Dockerfile for FactFlow CLI deployment.
    
    Args:
        output_path: Path to save the Dockerfile
    """
    dockerfile_content = """# FactFlow Agent Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY factflow/requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY factflow/ ./factflow/
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the CLI application (query passed as CMD argument)
ENTRYPOINT ["python", "-m", "factflow.main"]
"""
    
    with open(output_path, "w") as f:
        f.write(dockerfile_content)
    
    print(f"✅ Dockerfile created at {output_path}")


def main():
    """CLI entry point for deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy FactFlow agent")
    parser.add_argument(
        "--config",
        default="deployment/config.yaml",
        help="Path to deployment config"
    )
    parser.add_argument(
        "--project-id",
        help="Google Cloud project ID"
    )
    parser.add_argument(
        "--test",
        help="Test query to run after deployment"
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create deployment config file"
    )
    
    args = parser.parse_args()
    
    if args.create_config:
        project_id = args.project_id or "your-project-id"
        config = create_deployment_config(project_id=project_id)
        save_deployment_config(config, args.config)
    else:
        deploy_to_agent_engine(
            config_path=args.config,
            project_id=args.project_id,
            test_query=args.test
        )


if __name__ == "__main__":
    main()

