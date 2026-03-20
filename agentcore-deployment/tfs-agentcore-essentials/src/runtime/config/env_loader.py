"""
Environment configuration loader for TFS AgentCore runtime
"""
import os
import pathlib
from dotenv import load_dotenv, dotenv_values


def load_environment():
    """
    Load environment variables from .env file with proper path resolution
    """
    # Get the runtime directory (this file's parent's parent)
    runtime_dir = pathlib.Path(__file__).resolve().parents[1]
    root_env_path = runtime_dir.parent / ".env"
    
    # Load root .env if it exists
    if root_env_path.exists():
        load_dotenv(root_env_path.as_posix(), override=True)
        print(f"Loaded environment from: {root_env_path}")
    else:
        print(f"Warning: root .env not found at {root_env_path}")
    
    # Also load from dotenv_values for fallback
    _file_env = dotenv_values(root_env_path.as_posix())
    
    # Required environment variables
    required_vars = ["AWS_REGION", "BEDROCK_MODEL_ID", "KNOWLEDGE_BASE_ID"]
    missing_vars = []
    
    for var in required_vars:
        value = _file_env.get(var) or os.getenv(var)
        if not value:
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Return configuration dictionary
    config = {
        "AWS_REGION": _file_env.get("AWS_REGION") or os.getenv("AWS_REGION"),
        "BEDROCK_MODEL_ID": _file_env.get("BEDROCK_MODEL_ID") or os.getenv("BEDROCK_MODEL_ID"),
        "KNOWLEDGE_BASE_ID": _file_env.get("KNOWLEDGE_BASE_ID") or os.getenv("KNOWLEDGE_BASE_ID"),
        "S3_BUCKET": _file_env.get("S3_BUCKET", "tfs-faq-poc"),
        "S3_OUTPUT_PREFIX": _file_env.get("S3_OUTPUT_PREFIX", "tfs-form-filling-bucket/outputs/")
    }
    
    return config
