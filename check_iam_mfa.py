import json
import boto3
import time
from datetime import datetime

def lambda_handler(event, context):
    iam_client = boto3.client('iam')
    dynamodb = boto3.resource('dynamodb')
    sns_client = boto3.client('sns')
    
    table = dynamodb.Table('SecurityComplianceResults')
    
    # REPLACE with your SNS topic ARN
    sns_topic_arn = 'arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:SecurityAlerts'
    
    # Get all IAM users
    try:
        paginator = iam_client.get_paginator('list_users')
        users = []
        for page in paginator.paginate():
            users.extend(page['Users'])
    except Exception as e:
        print(f"Error listing IAM users: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps('Error listing users')}
    
    results = []
    timestamp = int(time.time())
    compliant_count = 0
    non_compliant_count = 0
    non_compliant_resources = []
    
    for user in users:
        user_name = user['UserName']
        
        # Check if user has MFA enabled
        try:
            mfa_devices = iam_client.list_mfa_devices(UserName=user_name)
            has_mfa = len(mfa_devices['MFADevices']) > 0
            
            if has_mfa:
                status = "COMPLIANT"
                message = "MFA is enabled"
                compliant_count += 1
            else:
                status = "NON_COMPLIANT"
                message = "MFA is NOT enabled"
                non_compliant_count += 1
                non_compliant_resources.append(f"IAM User: {user_name} - {message}")
                
        except Exception as e:
            status = "ERROR"
            message = f"Error checking MFA: {str(e)}"
            print(f"Error checking MFA for {user_name}: {str(e)}")
        
        # Store result in DynamoDB
        try:
            table.put_item(
                Item={
                    'ResourceId': f"iam-user::{user_name}",
                    'Timestamp': timestamp,
                    'ResourceType': 'IAMUser',
                    'ResourceName': user_name,
                    'Status': status,
                    'Message': message,
                    'CheckType': 'MFAEnabled',
                    'CheckTime': datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"Error writing to DynamoDB: {str(e)}")
        
        results.append({
            'user': user_name,
            'status': status,
            'message': message
        })
        
        print(f"Checked {user_name}: {status} - {message}")
    
    # Send SNS alert if non-compliant resources found
    if non_compliant_resources:
        alert_subject = f"Security Alert: {non_compliant_count} IAM Users Without MFA"
        alert_message = f"""AWS Security Compliance Alert

Scan completed at: {datetime.now().isoformat()}

Summary:
- Total IAM Users Checked: {len(results)}
- Compliant: {compliant_count}
- Non-Compliant: {non_compliant_count}

Non-Compliant Resources:
{chr(10).join(non_compliant_resources)}

Action Required:
Enable MFA (Multi-Factor Authentication) for all IAM users to enhance security.

To fix:
1. Go to IAM console
2. Select the user
3. Go to Security credentials tab
4. Click "Assign MFA device"
5. Follow the setup wizard
"""
        
        try:
            sns_client.publish(
                TopicArn=sns_topic_arn,
                Subject=alert_subject,
                Message=alert_message
            )
            print(f"Alert sent via SNS to {sns_topic_arn}")
        except Exception as e:
            print(f"Error sending SNS notification: {str(e)}")
    
    summary = {
        'total_users': len(results),
        'compliant': compliant_count,
        'non_compliant': non_compliant_count,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"Summary: {json.dumps(summary)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary)
    }
