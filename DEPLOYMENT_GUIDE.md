# 📖 Deployment Guide - AWS Security Compliance Dashboard

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Step-by-Step Deployment](#step-by-step-deployment)
3. [Testing](#testing)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance](#maintenance)

---

## Prerequisites

### AWS Account Requirements
- Active AWS account
- IAM user with administrative permissions
- AWS CLI installed and configured

### Local Development
- Python 3.11 or higher
- Git installed
- Text editor (VS Code recommended)

---

## Step-by-Step Deployment

### Step 1: Create DynamoDB Table

**Via AWS Console:**
1. Navigate to DynamoDB service
2. Click "Create table"
3. Table name: `SecurityComplianceResults`
4. Partition key: `ResourceId` (String)
5. Sort key: `Timestamp` (Number)
6. Use default settings
7. Click "Create table"

**Via AWS CLI:**
```bash
aws dynamodb create-table \
    --table-name SecurityComplianceResults \
    --attribute-definitions \
        AttributeName=ResourceId,AttributeType=S \
        AttributeName=Timestamp,AttributeType=N \
    --key-schema \
        AttributeName=ResourceId,KeyType=HASH \
        AttributeName=Timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

---

### Step 2: Create SNS Topic for Alerts

**Via AWS Console:**
1. Navigate to SNS service
2. Click "Create topic"
3. Type: Standard
4. Name: `SecurityAlerts`
5. Click "Create topic"
6. Click "Create subscription"
7. Protocol: Email
8. Endpoint: your-email@example.com
9. Confirm subscription via email

**Via AWS CLI:**
```bash
# Create topic
aws sns create-topic --name SecurityAlerts --region us-east-1

# Subscribe email
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:SecurityAlerts \
    --protocol email \
    --notification-endpoint your-email@example.com
```

**Important:** Save your SNS Topic ARN - you'll need it for Lambda functions!

---

### Step 3: Create IAM Role for Lambda

**Via AWS Console:**
1. Navigate to IAM service
2. Click "Roles" → "Create role"
3. Trusted entity: AWS service → Lambda
4. Attach these policies:
   - `AWSLambdaBasicExecutionRole`
   - `AmazonS3ReadOnlyAccess`
   - `AmazonEC2ReadOnlyAccess`
   - `IAMReadOnlyAccess`
   - `AmazonRDSReadOnlyAccess`
   - `AmazonDynamoDBFullAccess`
   - `AmazonSNSFullAccess`
5. Role name: `SecurityComplianceLambdaRole`
6. Click "Create role"

---

### Step 4: Deploy Lambda Functions

For each of the 5 Lambda functions, follow these steps:

#### Function 1: CheckS3Encryption

**Via AWS Console:**
1. Navigate to Lambda service
2. Click "Create function"
3. Author from scratch
4. Function name: `CheckS3Encryption`
5. Runtime: Python 3.11
6. Execution role: Use existing role → `SecurityComplianceLambdaRole`
7. Click "Create function"
8. Copy code from `lambda_functions/check_s3_encryption.py`
9. **Important:** Update SNS ARN in line 13
10. Configuration → General → Edit → Timeout: 60 seconds
11. Click "Deploy"
12. Test the function

**Via AWS CLI:**
```bash
# Create deployment package
cd lambda_functions
zip check_s3_encryption.zip check_s3_encryption.py

# Create Lambda function
aws lambda create-function \
    --function-name CheckS3Encryption \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/SecurityComplianceLambdaRole \
    --handler check_s3_encryption.lambda_handler \
    --zip-file fileb://check_s3_encryption.zip \
    --timeout 60 \
    --region us-east-1
```

#### Repeat for Other Functions:
- `CheckSecurityGroups`
- `CheckIAMMFA`
- `CheckRDSEncryption`
- `CheckUnusedEIPs`

---

### Step 5: Create EventBridge Rule for Automation

**Via AWS Console:**
1. Navigate to EventBridge service
2. Click "Rules" → "Create rule"
3. Name: `HourlySecurityScans`
4. Rule type: Schedule
5. Schedule expression: `rate(1 hour)`
6. Click "Next"
7. Add all 5 Lambda functions as targets:
   - CheckS3Encryption
   - CheckSecurityGroups
   - CheckIAMMFA
   - CheckRDSEncryption
   - CheckUnusedEIPs
8. Click "Next" → "Next" → "Create rule"

**Via AWS CLI:**
```bash
# Create EventBridge rule
aws events put-rule \
    --name HourlySecurityScans \
    --schedule-expression "rate(1 hour)" \
    --state ENABLED \
    --region us-east-1

# Add Lambda permissions
for func in CheckS3Encryption CheckSecurityGroups CheckIAMMFA CheckRDSEncryption CheckUnusedEIPs
do
    aws lambda add-permission \
        --function-name $func \
        --statement-id AllowEventBridge \
        --action lambda:InvokeFunction \
        --principal events.amazonaws.com \
        --source-arn arn:aws:events:us-east-1:YOUR_ACCOUNT_ID:rule/HourlySecurityScans
done

# Add targets
aws events put-targets \
    --rule HourlySecurityScans \
    --targets \
        Id=1,Arn=arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:CheckS3Encryption \
        Id=2,Arn=arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:CheckSecurityGroups \
        Id=3,Arn=arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:CheckIAMMFA \
        Id=4,Arn=arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:CheckRDSEncryption \
        Id=5,Arn=arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:CheckUnusedEIPs
```

---

## Testing

### Manual Testing

**Test Individual Lambda Functions:**
1. Go to Lambda console
2. Select function
3. Click "Test" tab
4. Create test event (use default)
5. Click "Test"
6. Verify successful execution

**Verify DynamoDB:**
1. Go to DynamoDB console
2. Select `SecurityComplianceResults` table
3. Click "Explore table items"
4. Verify entries exist

**Check Email Alerts:**
- Look for emails from AWS Notifications
- Verify alert format and content

---

## Troubleshooting

### Common Issues

**Issue: Lambda Timeout**
- Solution: Increase timeout to 60 seconds in Configuration

**Issue: Access Denied Errors**
- Solution: Verify IAM role has all required permissions

**Issue: SNS Not Sending Emails**
- Solution: Confirm email subscription is "Confirmed" status

**Issue: DynamoDB Write Errors**
- Solution: Verify table name is exactly `SecurityComplianceResults`

**Issue: No Results in DynamoDB**
- Solution: Check CloudWatch Logs for errors

### Viewing Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/CheckS3Encryption --follow

# View recent errors
aws logs filter-log-events \
    --log-group-name /aws/lambda/CheckS3Encryption \
    --filter-pattern "ERROR"
```

---

## Maintenance

### Regular Tasks

**Weekly:**
- Review email alerts
- Check DynamoDB for trends
- Verify all Lambda functions executing

**Monthly:**
- Review CloudWatch metrics
- Optimize Lambda memory/timeout
- Clean old DynamoDB entries (optional)

**Quarterly:**
- Update Python runtime if needed
- Review IAM permissions
- Update documentation

### Cost Monitoring

Monitor costs in AWS Cost Explorer:
- Lambda invocations
- DynamoDB storage
- SNS notifications
- CloudWatch logs

Expected: $0.50 - $1.00/month

---

## Cleanup (If Needed)

To remove all resources:

```bash
# Delete EventBridge rule
aws events remove-targets --rule HourlySecurityScans --ids 1 2 3 4 5
aws events delete-rule --name HourlySecurityScans

# Delete Lambda functions
for func in CheckS3Encryption CheckSecurityGroups CheckIAMMFA CheckRDSEncryption CheckUnusedEIPs
do
    aws lambda delete-function --function-name $func
done

# Delete DynamoDB table
aws dynamodb delete-table --table-name SecurityComplianceResults

# Delete SNS topic
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:SecurityAlerts

# Delete IAM role
aws iam delete-role --role-name SecurityComplianceLambdaRole
```

---

## Support

For issues or questions:
- Check AWS CloudWatch Logs
- Review AWS documentation
- Open GitHub issue

---

**Last Updated:** November 2025
