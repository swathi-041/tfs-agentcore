# TFS AgentCore Deployment

## 🚀 Quick Deployment

### Option 1: AWS CloudShell (Recommended)
```bash
# Clone the repository
git clone https://github.com/swathi-041/tfs-agentcore.git
cd tfs-agentcore/agentcore-deployment

# Install dependencies
pip install bedrock-agentcore strands-agents strands-agents-tools

# Deploy to AWS Bedrock AgentCore
agentcore deploy --agent tfsagentcore_Agent
```

### Option 2: Local Development
```bash
# Clone and navigate
git clone https://github.com/swathi-041/tfs-agentcore.git
cd tfs-agentcore/agentcore-deployment

# Run locally
agentcore deploy --local
```

## 📁 Project Structure

```
agentcore-deployment/
├── .bedrock_agentcore.yaml    # AgentCore configuration
├── pyproject.toml           # Dependencies (bedrock-agentcore + strands)
├── src/
│   ├── main.py              # AgentCore entrypoint with TFS integration
│   └── runtime/             # Complete TFS multi-agent system
│       ├── agents/          # Master, lease, payment, planner, Q&A agents
│       ├── config/          # Environment configuration
│       ├── engines/          # Payment engine, lease tools, MCP server
│       └── tools/           # Form filling tools and templates
└── runtime.zip              # Pre-packaged deployment bundle
```

## 🔧 Configuration

### AWS Account & Region
- **Account:** 392856836805
- **Region:** us-east-1
- **Execution Role:** arn:aws:iam::392856836805:role/TFS-AgentCore-Execution-Role

### Required Permissions
Add these to your IAM policy:
```json
{
    "Effect": "Allow",
    "Action": [
        "bedrock-agentcore:CreateAgentRuntime",
        "bedrock-agentcore:UpdateAgentRuntime",
        "bedrock-agentcore:GetAgentRuntime",
        "bedrock-agentcore:InvokeAgentRuntime"
    ],
    "Resource": "*"
}
```

## 🎯 Features

- **Multi-Agent System:** Master agent coordinates lease, payment, planner, and Q&A agents
- **Strands Integration:** Uses strands-agents framework for enhanced capabilities
- **MCP Support:** Model Context Protocol integration for external services
- **Form Filling:** Automated lease-end document processing
- **Payment Processing:** Payment calculation and processing engine

## 📦 Dependencies

- `bedrock-agentcore`: AWS Bedrock AgentCore runtime
- `strands-agents`: Multi-agent orchestration framework
- `strands-agents-tools`: Agent tooling and utilities
- `boto3`: AWS SDK for Python
- `fastapi`: Web framework for API endpoints

## 🚨 Troubleshooting

### Windows CLI Issues
If you encounter `'NoneType' object has no attribute 'upper'` errors:
1. Use AWS CloudShell (Linux environment)
2. Or deploy via AWS Console manually

### Permission Issues
Ensure your IAM user/role has the required Bedrock AgentCore permissions listed above.

### Runtime Not Starting
Check the agent logs in AWS CloudWatch for detailed error messages.

## 📞 Support

For deployment issues, check the AWS Bedrock AgentCore documentation or use AWS CloudShell for a Linux deployment environment.
