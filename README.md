# AWS Security Compliance Dashboard

A personal project that automatically monitors AWS infrastructure for security issues and sends email alerts.

## What This Project Does

This system runs every hour and checks my AWS account for:
- ✅ S3 buckets without encryption
- ✅ Security groups with unrestricted SSH access
- ✅ IAM users without MFA enabled
- ✅ RDS databases without encryption
- ✅ Unused Elastic IPs (to save money)

When it finds a problem, it sends me an email alert and saves the results to a database.

## Why I Built This

I wanted to learn AWS and build something practical. Manual security checks take time and it's easy to miss things, so I automated the process using AWS serverless services.

## Technologies Used

- **AWS Lambda** - Runs the security checks (Python 3.11)
- **Amazon DynamoDB** - Stores the scan results
- **Amazon SNS** - Sends email alerts
- **Amazon EventBridge** - Triggers the scans every hour
- **AWS IAM** - Manages permissions securely

## How It Works

```
Every hour → EventBridge triggers → 5 Lambda functions run
                                    ↓
                    Check S3, Security Groups, IAM, RDS, Elastic IPs
                                    ↓
                    Save results to DynamoDB + Send email alerts
```

## Project Files

- `lambda_functions/` - Contains 5 Python scripts for security checks
- `DEPLOYMENT_GUIDE.md` - Step-by-step instructions to set this up

## Setup Instructions

If you want to try this yourself, see the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete setup instructions.

**Quick overview:**
1. Create a DynamoDB table
2. Create an SNS topic for email alerts
3. Create an IAM role with necessary permissions
4. Deploy the 5 Lambda functions
5. Set up EventBridge to run them hourly

## What I Learned

- How to use AWS Lambda and write serverless functions
- Working with DynamoDB for storing data
- Setting up automated workflows with EventBridge
- AWS security best practices (IAM roles, encryption)
- Python programming with the Boto3 SDK
- Cost optimization in AWS (this runs for less than $1/month!)

## Sample Output

When the system finds an issue, I get an email like:

```
Subject: Security Alert: 2 Unencrypted S3 Buckets Found

Summary:
- Total S3 Buckets: 5
- Encrypted: 3
- Unencrypted: 2

Unencrypted Buckets:
- my-test-bucket
- backup-bucket-2025

Action Required: Enable encryption on these buckets.
```

## Costs

This project runs on AWS and costs approximately **$0.50-$1.00 per month** because:
- Lambda has a free tier (1 million requests/month)
- DynamoDB has a free tier (25GB storage)
- SNS has a free tier (1,000 emails/month)
- EventBridge is very cheap for scheduled rules

## Improvements I Want to Make

- [ ] Add a web dashboard to visualize the data
- [ ] Check for more security issues (CloudTrail, public EC2 instances)
- [ ] Add automatic fixes for simple violations
- [ ] Send alerts to Slack instead of email

## Contact

Feel free to reach out if you have questions about this project!

- **Email:** sandymoises@hotmail.com
- **LinkedIn:** https://www.linkedin.com/in/alex-moise-18470136a/

---

⭐ If you found this project interesting, please give it a star!
