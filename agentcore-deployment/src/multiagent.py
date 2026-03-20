import os
import sys
import asyncio
from bedrock_agentcore import BedrockAgentCoreApp

# Add runtime to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'runtime'))

# Import our TFS runtime
from config.env_loader import load_environment
from agents.master_agent import MasterAgent

# Load environment (with error handling)
try:
    load_environment()
except Exception as e:
    print(f"Warning: Could not load environment file: {e}")
    # Continue with default environment variables

# Integrate with Bedrock AgentCore
app = BedrockAgentCoreApp()
log = app.logger

# Initialize our TFS Master Agent
config = {
    "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
    "BEDROCK_MODEL_ID": os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0"),
    "KNOWLEDGE_BASE_ID": os.getenv("KNOWLEDGE_BASE_ID", "DZXTSW2YSL"),
    "S3_BUCKET": os.getenv("S3_BUCKET", "tfs-faq-poc"),
    "S3_OUTPUT_PREFIX": os.getenv("S3_OUTPUT_PREFIX", "tfs-form-filling-bucket/outputs/")
}
master_agent = MasterAgent(config)

@app.entrypoint
async def invoke(payload, context):
    """TFS AgentCore Runtime Entry Point"""
    session_id = getattr(context, 'session_id', '')
    user_id = payload.get("user_id", 'default-user')
    
    # Get input text from payload
    input_text = payload.get("prompt", "")
    if not input_text:
        input_text = payload.get("inputText", "")
    
    if not input_text:
        yield {"outputText": "No input provided", "sessionId": session_id, "attributes": {}}
        return
    
    try:
        # Process with our TFS Master Agent
        result = await master_agent.process_query(input_text)
        
        # Format response for AgentCore
        if isinstance(result, dict):
            response_text = result.get("outputText", str(result))
        else:
            response_text = str(result)
        
        yield response_text
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        log.error(error_msg)
        yield error_msg

if __name__ == "__main__":
    app.run()
