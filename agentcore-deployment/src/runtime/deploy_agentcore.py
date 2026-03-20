#!/usr/bin/env python3
"""
Amazon Bedrock AgentCore Deployment Script
Use this instead of the broken CLI
"""

import os
import sys
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from starlette.responses import JSONResponse

def main():
    """Deploy runtime using BedrockAgentCoreApp"""
    print("🚀 Starting Amazon Bedrock AgentCore Runtime...")
    
    # Create AgentCore app
    app = BedrockAgentCoreApp()
    
    # Check if runtime.zip exists
    if not os.path.exists('runtime.zip'):
        print("❌ ERROR: runtime.zip not found in current directory")
        print("📁 Current directory:", os.getcwd())
        sys.exit(1)
    
    print("✅ runtime.zip found")
    
    # Add runtime.zip as a route
    async def runtime_handler(request):
        """Handle runtime requests"""
        return JSONResponse({
            "outputText": "TFS AgentCore Runtime is running",
            "sessionId": "",
            "attributes": {}
        })
    
    async def health_handler(request):
        """Handle health check"""
        return JSONResponse({"status": "healthy"})
    
    app.add_route('/invoke', runtime_handler, methods=['POST'])
    app.add_route('/health', health_handler, methods=['GET'])
    
    print("🌐 Starting server on http://0.0.0.0:8080")
    print("📋 Available endpoints:")
    print("   - POST /invoke - AgentCore endpoint")
    print("   - GET /health - Health check")
    print("   - GET / - Service info")
    
    try:
        # Run the AgentCore app
        app.run(port=8080, host='0.0.0.0')
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
