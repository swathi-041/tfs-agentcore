# TFS AgentCore Runtime

Toyota Financial Services Multi-Agent System for Amazon Bedrock AgentCore deployment.

## 🏗️ Architecture

This unified runtime consolidates the original multi-service backend into a single AgentCore-compatible deployment:

```
runtime/
├── server.py              # FastAPI server with /invoke endpoint
├── requirements.txt       # Production dependencies
├── agents/               # Local agent modules
│   ├── master_agent.py   # Central orchestrator with Bedrock routing
│   ├── qna_agent.py      # Knowledge base Q&A with Bedrock KB
│   ├── planner_agent.py  # Complex workflow planning
│   ├── lease_agent.py    # Lease calculations with MCP tools
│   └── payment_agent.py  # Payment processing
├── tools/                # Shared utilities
│   └── form_fill_tool.py # PDF generation and S3 upload
└── config/               # Configuration
    └── env_loader.py     # Environment variable loading
```

## 🚀 Key Features

### ✅ Preserved Business Logic
- **Master Agent**: Single entrypoint with Bedrock intent classification
- **QnA Agent**: Bedrock Knowledge Base retrieval and answering
- **Planner Agent**: Multi-step workflow orchestration
- **Lease Agent**: MCP tool integration for calculations
- **Payment Agent**: Payment processing with NLP
- **Form Fill Tool**: PDF generation with S3 upload

### ✅ AgentCore Compatibility
- **/invoke endpoint**: Amazon Bedrock AgentCore compliant
- **Local Dispatch**: No inter-agent HTTP calls
- **Unified Runtime**: Single deployment package
- **Production Ready**: FastAPI with proper error handling

## 📦 Deployment

### Prerequisites
- Python 3.10+
- AWS CLI configured
- Bedrock model access
- S3 bucket for form outputs
- Bedrock Knowledge Base ID

### Quick Deploy
```bash
# 1. Package runtime
cd runtime
zip -r ../runtime.zip .

# 2. Upload to S3
aws s3 cp ../runtime.zip s3://your-deployment-bucket/

# 3. Create AgentCore runtime
aws bedrock-agent create-agent-runtime \
    --runtime-name tfs-agentcore-runtime \
    --environment S3Bucket=your-deployment-bucket,S3Key=runtime.zip
```

### Environment Variables
```bash
# Required
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
KNOWLEDGE_BASE_ID=your-knowledge-base-id

# Optional
S3_BUCKET=tfs-faq-poc
S3_OUTPUT_PREFIX=tfs-form-filling-bucket/outputs/
```

## 🔧 Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
export KNOWLEDGE_BASE_ID=your-knowledge-base-id

# Start server
python server.py --port 8080

# Test endpoints
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"inputText": "What are my lease options?"}'
```

## 📡 API Endpoints

### AgentCore Invoke (Primary)
```
POST /invoke
{
  "inputText": "User query",
  "sessionId": "optional-session-id",
  "attributes": {}
}
```

### Health Check
```
GET /health
```

### Legacy Compatibility
```
POST /query
{
  "query": "User query"
}
```

## 🧪 Example Queries

### QnA (Knowledge Base)
```
"What are my lease-end options?"
"What are the mileage charges for excess wear?"
```

### Lease Calculations
```
"Calculate buyout for LSE-12345 with 40000 miles"
"Exchange my lease LSE-12345, condition good, 35000 miles"
"Get lease details for LSE-12345"
```

### Form Generation
```
"Generate odometer statement with Name: John Doe VIN: 1HGBH41JXMN109186 Account number: ACC-12345 Make: Toyota Model: Camry Body type: Sedan Year: 2022 Miles: 36000 Date: 03/17/2026 Address: 123 Main Street, New York, NY 10001 confirm_signature: true"
```

### Payment Processing
```
"Process payment for lease LSE-12345, amount $450"
"Get payment history for LSE-12345"
"Show member info for john.doe@email.com"
```

### Complex Workflows
```
"What is TFS and calculate buyout for LSE-12345 with 40000 miles"
"What are my lease options and explain exchange process for LSE-12345"
```

## 🔐 Security & Permissions

### Required IAM Permissions
- `bedrock:InvokeModel` for Claude/Nova models
- `bedrock-agent:Retrieve` for knowledge base
- `s3:GetObject/PutObject` for form uploads
- `logs:*` for CloudWatch logging
- `iam:PassRole` for runtime execution

### SCP Considerations
Ensure organization policies allow:
- Bedrock model access
- S3 bucket operations  
- IAM role passing
- CloudWatch logging

## 📊 Monitoring

### CloudWatch Metrics
- Request latency and error rates
- Bedrock model invocation counts
- S3 upload success rates
- Agent routing distribution

### Logging
- Runtime logs: `/aws/bedrock/agent-runtime/tfs-agentcore-runtime`
- Request/response logging
- Error tracking and debugging

## 🔄 Migration Notes

### From Multi-Service to Unified Runtime
- **Removed**: Inter-agent HTTP calls (localhost:8000-8008)
- **Replaced**: Local Python imports and function calls
- **Preserved**: All business logic and Bedrock integrations
- **Enhanced**: Single deployment package and AgentCore compatibility

### Configuration Changes
- Environment variables loaded from root `.env`
- No need for multiple service URLs
- Unified health check and monitoring

## 🛠️ Development

### Adding New Agents
1. Create agent class in `agents/`
2. Import in `master_agent.py`
3. Add to routing logic in `classify_query_with_bedrock()`
4. Update `planner_agent.py` AVAILABLE_AGENTS

### Extending Tools
1. Add tool to `tools/` directory
2. Import in relevant agent
3. Follow existing error handling patterns

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Load testing
python tests/load_test.py

# Integration tests
python tests/integration_test.py
```

## 📞 Support

For technical support:
1. Check CloudWatch logs for errors
2. Verify IAM permissions and SCP policies
3. Validate environment variables
4. Review DEPLOYMENT_CHECKLIST.md

## 📄 License

Proprietary to Toyota Financial Services.
