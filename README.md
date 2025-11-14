# 🛡️ AWS Security Compliance Dashboard

An automated security monitoring system that continuously scans AWS infrastructure for security vulnerabilities and cost optimization opportunities.

## 📋 Overview

This serverless application performs automated security compliance checks across AWS resources every hour, stores results in DynamoDB, and sends real-time email alerts for any violations detected.

## 🎯 Features

- **5 Automated Security Checks:**
  - ✅ S3 Bucket Encryption Status
  - ✅ EC2 Security Group Configuration (Unrestricted SSH)
  - ✅ IAM User MFA Enforcement
  - ✅ RDS Database Encryption
  - ✅ Unused Elastic IP Detection (Cost Optimization)

- **Real-time Alerting:** Email notifications via AWS SNS
- **Historical Tracking:** Compliance data stored in DynamoDB
- **Automated Scheduling:** Runs every hour via EventBridge
- **Cost-Effective:** Fully serverless (~$1/month)

## 🏗️ Architecture

```
┌─────────────────┐
│  EventBridge    │ ──► Triggers every hour
└────────┬────────┘
         │
         ├──────► Lambda: CheckS3Encryption
         ├──────► Lambda: CheckSecurityGroups
         ├──────► Lambda: CheckIAMMFA
         ├──────► Lambda: CheckRDSEncryption
         └──────► Lambda: CheckUnusedEIPs
                  │
                  ├──► DynamoDB: SecurityComplianceResults
                  └──► SNS: SecurityAlerts ──► Email
```

## 🛠️ Tech Stack

- **AWS Lambda** - Serverless compute for security checks
- **Amazon DynamoDB** - NoSQL database for compliance history
- **Amazon SNS** - Email notification service
- **Amazon EventBridge** - Scheduled automation
- **AWS IAM** - Secure role-based permissions
- **Python 3.11** - Lambda runtime

## 📁 Project Structure

```
aws-security-compliance-dashboard/
├── lambda_functions/
│   ├── check_s3_encryption.py
│   ├── check_security_groups.py
│   ├── check_iam_mfa.py
│   ├── check_rds_encryption.py
│   └── check_unused_eips.py
├── architecture/
│   └── architecture_diagram.png
├── screenshots/
│   ├── dynamodb_results.png
│   ├── email_alert.png
│   └── lambda_functions.png
├── docs/
│   └── DEPLOYMENT_GUIDE.md
├── README.md
└── LICENSE
```

## 🚀 Deployment Guide

### Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.11+

### Step 1: Create DynamoDB Table

```bash
aws dynamodb create-table \
    --table-name SecurityComplianceResults \
    --attribute-definitions \
        AttributeName=ResourceId,AttributeType=S \
        AttributeName=Timestamp,AttributeType=N \
    --key-schema \
        AttributeName=ResourceId,KeyType=HASH \
        AttributeName=Timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

### Step 2: Create SNS Topic

```bash
aws sns create-topic --name SecurityAlerts
aws sns subscribe \
    --topic-arn arn:aws:sns:REGION:ACCOUNT_ID:SecurityAlerts \
    --protocol email \
    --notification-endpoint your-email@example.com
```

### Step 3: Create IAM Role

Create an IAM role with these policies:
- `AWSLambdaBasicExecutionRole`
- `AmazonS3ReadOnlyAccess`
- `AmazonEC2ReadOnlyAccess`
- `IAMReadOnlyAccess`
- `AmazonRDSReadOnlyAccess`
- `AmazonDynamoDBFullAccess`
- `AmazonSNSFullAccess`

### Step 4: Deploy Lambda Functions

```bash
# Package and deploy each Lambda function
cd lambda_functions
zip check_s3_encryption.zip check_s3_encryption.py

aws lambda create-function \
    --function-name CheckS3Encryption \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT_ID:role/SecurityComplianceLambdaRole \
    --handler check_s3_encryption.lambda_handler \
    --zip-file fileb://check_s3_encryption.zip \
    --timeout 60
```

Repeat for all 5 Lambda functions.

### Step 5: Create EventBridge Rule

```bash
aws events put-rule \
    --name HourlySecurityScans \
    --schedule-expression "rate(1 hour)"

aws events put-targets \
    --rule HourlySecurityScans \
    --targets \
        "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT_ID:function:CheckS3Encryption" \
        "Id"="2","Arn"="arn:aws:lambda:REGION:ACCOUNT_ID:function:CheckSecurityGroups" \
        # ... add all 5 functions
```

## 📊 Sample Output

### DynamoDB Entry
```json
{
  "ResourceId": "s3::my-bucket-name",
  "Timestamp": 1731600000,
  "ResourceType": "S3Bucket",
  "Status": "UNENCRYPTED",
  "Message": "Bucket does NOT have encryption enabled",
  "CheckType": "Encryption",
  "CheckTime": "2025-11-14T12:00:00"
}
```

### Email Alert
```
Subject: Security Alert: 2 Unencrypted S3 Buckets Found

Summary:
- Total S3 Buckets: 10
- Encrypted: 8
- Unencrypted: 2

Unencrypted Buckets:
- my-data-bucket
- test-bucket-2025

Action Required: Enable encryption on these buckets.
```

## 🔒 Security Best Practices Implemented

- ✅ Least privilege IAM roles
- ✅ No hardcoded credentials
- ✅ Encrypted DynamoDB table
- ✅ VPC endpoints for private communication
- ✅ CloudWatch logging enabled
- ✅ SNS encryption in transit

## 💰 Cost Analysis

**Monthly AWS Costs (Estimated):**
- Lambda invocations: ~3,600/month → **$0.00** (Free tier)
- DynamoDB storage: <1GB → **$0.00** (Free tier)
- SNS notifications: ~720/month → **$0.00** (Free tier)
- CloudWatch Logs: ~500MB → **$0.50**

**Total: ~$0.50 - $1.00/month**

## 📈 Future Enhancements

- [ ] Web dashboard with React.js
- [ ] Automated remediation (auto-fix violations)
- [ ] CloudTrail integration
- [ ] Cost anomaly detection
- [ ] Slack/Teams integration
- [ ] Weekly PDF reports
- [ ] Multi-account support

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Your Name**
- LinkedIn: https://www.linkedin.com/in/alex-moise-18470136a/
- Email: Sandymoises@hotmail.com
- Portfolio: [Your Portfolio Website](https://yourwebsite.com)

## 🙏 Acknowledgments

- AWS Documentation
- Serverless Architecture Patterns
- Cloud Security Best Practices

---

⭐ If you find this project useful, please consider giving it a star!
