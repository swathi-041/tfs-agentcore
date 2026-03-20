import os
import sys
import asyncio
from bedrock_agentcore import BedrockAgentCoreApp

# Add runtime to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'runtime'))

# Integrate with Bedrock AgentCore
app = BedrockAgentCoreApp()
log = app.logger

@app.entrypoint
async def invoke(payload, context):
    """Simple TFS AgentCore Runtime Entry Point"""
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
        # Simple response for testing
        yield f"Received: {input_text}"
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        log.error(error_msg)
        yield error_msg

if __name__ == "__main__":
    app.run()
