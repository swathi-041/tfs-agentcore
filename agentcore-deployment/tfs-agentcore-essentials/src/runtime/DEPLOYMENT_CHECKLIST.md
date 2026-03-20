# TFS AgentCore Runtime Deployment Checklist

## 📋 Pre-Deployment Checklist

### ✅ Runtime Package Preparation
- [ ] Create runtime.zip from runtime/ directory
- [ ] Verify requirements.txt is included
- [ ] Verify server.py is included with /invoke endpoint
- [ ] Verify all agent modules are included
- [ ] Verify config/env_loader.py is included
- [ ] Verify tools/form_fill_tool.py is included
- [ ] Verify __init__.py files are present in all packages
- [ ] Exclude .git, node_modules, venv, frontend directories
- [ ] Test runtime locally: `python runtime/server.py --port 8080`

### ✅ AWS Environment Setup
- [ ] AWS Region configured (default: us-east-1)
- [ ] S3 bucket created for form outputs (default: tfs-faq-poc)
- [ ] Bedrock Knowledge Base ID available
- [ ] Bedrock Model ID available (e.g., anthropic.claude-3-sonnet-20240229-v1:0)
- [ ] AWS credentials configured for deployment

### ✅ Environment Variables
Create .env file with:
```
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
KNOWLEDGE_BASE_ID=your-knowledge-base-id
S3_BUCKET=tfs-faq-poc
S3_OUTPUT_PREFIX=tfs-form-filling-bucket/outputs/
```

## 🚀 Deployment Steps

### 1. Package Runtime
```bash
cd runtime
zip -r ../runtime.zip .
cd ..
```

### 2. Upload to S3
```bash
aws s3 cp runtime.zip s3://your-deployment-bucket/runtime.zip
```

### 3. Create AgentCore Runtime
```bash
aws bedrock-agent create-agent-runtime \
    --runtime-name tfs-agentcore-runtime \
    --runtime-arn arn:aws:bedrock:us-east-1:123456789012:runtime/your-runtime-id \
    --environment S3Bucket=your-deployment-bucket,S3Key=runtime.zip
```

### 4. Test Deployment
```bash
aws bedrock-agent invoke-agent \
    --agent-id your-agent-id \
    --agent-alias-id your-alias-id \
    --input-text "What are my lease options?"
```

## 🔐 Required IAM Permissions

### For Runtime Deployment
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:CreateAgentRuntime",
                "bedrock:UpdateAgentRuntime",
                "bedrock:GetAgentRuntime",
                "bedrock:DeleteAgentRuntime"
            ],
            "Resource": "arn:aws:bedrock:*:*:runtime/tfs-agentcore-runtime"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-deployment-bucket/runtime.zip",
                "arn:aws:s3:::tfs-faq-poc/tfs-form-filling-bucket/outputs/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-deployment-bucket",
                "arn:aws:s3:::tfs-faq-poc"
            ]
        }
    ]
}
```

### For Runtime Execution
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeAgent"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agent:Retrieve"
            ],
            "Resource": "arn:aws:bedrock:us-east-1:123456789012:knowledge-base/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": "arn:aws:iam::*:role/tfs-agentcore-runtime-role"
        }
    ]
}
```

## 🚫 Possible SCP Blockers

### Service Control Policies That May Block Deployment

1. **Bedrock Access Restrictions**
   ```json
   {
       "Effect": "Deny",
       "Action": [
           "bedrock:*"
       ],
       "Resource": "*"
   }
   ```

2. **S3 Access Restrictions**
   ```json
   {
       "Effect": "Deny", 
       "Action": [
           "s3:GetObject",
           "s3:PutObject"
       ],
       "Resource": "arn:aws:s3:::*/*"
   }
   ```

3. **IAM PassRole Restrictions**
   ```json
   {
       "Effect": "Deny",
       "Action": [
           "iam:PassRole"
       ],
       "Resource": "*"
   }
   ```

4. **CloudWatch Logs Restrictions**
   ```json
   {
       "Effect": "Deny",
       "Action": [
           "logs:*"
       ],
       "Resource": "*"
   }
   ```

### Required SCP Allowances
Ensure your organization's SCPs allow:

1. ✅ `bedrock:CreateAgentRuntime`
2. ✅ `bedrock:InvokeModel`
3. ✅ `bedrock-agent:Retrieve`
4. ✅ `s3:GetObject` and `s3:PutObject`
5. ✅ `iam:PassRole`
6. ✅ `logs:*` operations

## 🔍 Post-Deployment Verification

### Health Checks
```bash
# Test health endpoint
curl https://your-runtime-endpoint/health

# Expected response
{
    "status": "healthy",
    "service": "tfs-agentcore-runtime", 
    "version": "1.0.0"
}
```

### Functional Tests
```bash
# Test QnA functionality
aws bedrock-agent invoke-agent \
    --agent-id your-agent-id \
    --input-text "What are my lease options?"

# Test lease calculation
aws bedrock-agent invoke-agent \
    --agent-id your-agent-id \
    --input-text "Calculate buyout for LSE-12345 with 40000 miles"

# Test form fill
aws bedrock-agent invoke-agent \
    --agent-id your-agent-id \
    --input-text "Generate odometer statement with Name: John Doe VIN: 1HGBH41JXMN109186..."

# Test payment processing
aws bedrock-agent invoke-agent \
    --agent-id your-agent-id \
    --input-text "Process payment for lease LSE-12345"
```

### Monitoring Setup
- [ ] Configure CloudWatch Logs for runtime
- [ ] Set up CloudWatch Alarms for errors
- [ ] Monitor S3 bucket for form outputs
- [ ] Set up Bedrock usage monitoring

## 📞 Troubleshooting

### Common Issues
1. **Runtime fails to start**: Check IAM permissions and environment variables
2. **Bedrock model access denied**: Verify model availability and IAM permissions
3. **S3 upload failures**: Check bucket permissions and CORS settings
4. **Knowledge base not accessible**: Verify KB ID and retrieval permissions

### Log Locations
- Runtime logs: CloudWatch Logs `/aws/bedrock/agent-runtime/tfs-agentcore-runtime`
- S3 access logs: CloudTrail data events
- Bedrock usage: CloudWatch Bedrock metrics

## 🔄 Maintenance

### Updates
1. Update runtime.zip with new code
2. Upload to S3 bucket
3. Update AgentCore runtime configuration
4. Test with invoke-agent commands

### Scaling
- Monitor concurrent request limits
- Adjust runtime memory/CPU as needed
- Consider multiple runtime instances for high load
