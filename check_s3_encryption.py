import json
import boto3
import time
from datetime import datetime

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    sns_client = boto3.client('sns')
    
    table = dynamodb.Table('SecurityComplianceResults')
    
    # REPLACE with your SNS topic ARN
    sns_topic_arn = 'arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:SecurityAlerts'
    
    # Get all S3 buckets
    try:
        response = s3_client.list_buckets()
        buckets = response['Buckets']
    except Exception as e:
        print(f"Error listing buckets: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps('Error listing buckets')}
    
    results = []
    timestamp = int(time.time())
    encrypted_count = 0
    unencrypted_count = 0
    unencrypted_buckets = []
    
    for bucket in buckets:
        bucket_name = bucket['Name']
        
        # Check encryption
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
            status = "ENCRYPTED"
            message = f"Bucket has encryption enabled"
            encrypted_count += 1
        except s3_client.exceptions.ServerSideEncryptionConfigurationNotFoundError:
            status = "UNENCRYPTED"
            message = f"Bucket does NOT have encryption enabled"
            unencrypted_count += 1
            unencrypted_buckets.append(bucket_name)
        except Exception as e:
            status = "ERROR"
            message = f"Error checking encryption: {str(e)}"
            print(f"Error checking {bucket_name}: {str(e)}")
        
        # Store result in DynamoDB
        try:
            table.put_item(
                Item={
                    'ResourceId': f"s3::{bucket_name}",
                    'Timestamp': timestamp,
                    'ResourceType': 'S3Bucket',
                    'ResourceName': bucket_name,
                    'Status': status,
                    'Message': message,
                    'CheckType': 'Encryption',
                    'CheckTime': datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"Error writing to DynamoDB: {str(e)}")
        
        results.append({
            'bucket': bucket_name,
            'status': status,
            'message': message
        })
        
        print(f"Checked {bucket_name}: {status}")
    
    # Send SNS alert if unencrypted buckets found
    if unencrypted_buckets:
        alert_subject = f"Security Alert: {unencrypted_count} Unencrypted S3 Buckets Found"
        alert_message = f"""AWS Security Compliance Alert

Scan completed at: {datetime.now().isoformat()}

Summary:
- Total S3 Buckets: {len(results)}
- Encrypted: {encrypted_count}
- Unencrypted: {unencrypted_count}

Unencrypted Buckets:
{chr(10).join(unencrypted_buckets)}

Action Required:
Enable encryption on these S3 buckets to protect data at rest.

To fix:
1. Go to S3 console
2. Select the bucket
3. Go to Properties tab
4. Under Default encryption, click Edit
5. Enable Server-side encryption (SSE-S3 or SSE-KMS)
6. Save changes
"""
        
        try:
            sns_client.publish(
                TopicArn=sns_topic_arn,
                Subject=alert_subject,
                Message=alert_message
            )
            print(f"Alert sent via SNS")
        except Exception as e:
            print(f"Error sending SNS: {str(e)}")
    
    summary = {
        'total_buckets': len(results),
        'encrypted': encrypted_count,
        'unencrypted': unencrypted_count,
        'timestamp': datetime.now().isoformat()
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary)
    }
