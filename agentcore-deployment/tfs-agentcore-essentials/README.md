# TFS AgentCore - Minimal Deployment Package

## 🚀 Quick Deployment

### For AWS Admins (One-Command Deployment)

```bash
# Clone this repository
git clone https://github.com/swathi-041/tfs-agentcore.git
cd tfs-agentcore/tfs-agentcore-essentials

# Install dependencies
pip install bedrock-agentcore strands-agents strands-agents-tools

# Deploy to AWS Bedrock AgentCore
agentcore deploy --agent tfsagentcore_v2
```

## 📁 What's Included

### Essential Files Only:
```
tfs-agentcore-essentials/
├── .bedrock_agentcore.yaml    # AgentCore configuration
├── pyproject.toml           # Dependencies
└── src/
    ├── main.py              # Entry point
    └── runtime/             # TFS multi-agent system
        ├── agents/          # Master, lease, payment, planner, Q&A agents
        ├── config/          # Environment configuration
        ├── engines/          # Payment engine, lease tools, MCP server
        └── tools/           # Form filling tools and templates
```

## 🔧 Pre-Configured Settings

- **AWS Account:** 392856836805
- **Region:** us-east-1
- **Agent Name:** tfsagentcore_v2
- **Execution Role:** arn:aws:iam::392856836805:role/TFS-AgentCore-Execution-Role
- **S3 Bucket:** s3://tfs-agentcore-runtime

## 🎯 Business Value

### TFS Multi-Agent System:
- **Master Agent:** Coordinates all other agents
- **Lease Agent:** Handles lease calculations and paperwork
- **Payment Agent:** Processes payment calculations
- **Planner Agent:** Manages workflow planning
- **Q&A Agent:** Answers FAQ questions

### Technical Features:
- **Strands Integration:** Advanced agent orchestration
- **MCP Support:** Model Context Protocol integration
- **Form Filling:** Automated lease-end document processing
- **Payment Processing:** Payment calculation and processing engine

## 📦 Dependencies

- `bedrock-agentcore`: AWS Bedrock AgentCore runtime
- `strands-agents`: Multi-agent orchestration framework
- `strands-agents-tools`: Agent tooling and utilities
- `boto3`: AWS SDK for Python
- `fastapi`: Web framework for API endpoints

## 🚨 Prerequisites

### AWS Requirements:
- **IAM Permissions:** Full IAM + Bedrock AgentCore access
- **Execution Role:** TFS-AgentCore-Execution-Role (pre-configured)
- **S3 Bucket:** tfs-agentcore-runtime (pre-configured)
- **Region:** us-east-1

### Required Permissions:
```json
{
    "Effect": "Allow",
    "Action": [
        "iam:PassRole",
        "iam:GetRole", 
        "iam:ListRoles",
        "bedrock-agentcore:*"
    ],
    "Resource": "*"
}
```

## 🎯 Expected Outcome

After successful deployment:
- **Agent Runtime:** Created and healthy
- **API Endpoint:** Available for testing
- **Health Check:** `GET /health` returns status
- **Invoke:** `POST /invoke` processes TFS requests

## 📞 Support

This is the minimal, production-ready package for TFS AgentCore deployment.
All configuration is pre-set - just clone, install, and deploy!

**For any issues, check CloudWatch logs under `/aws/bedrock/agentcore/`**
