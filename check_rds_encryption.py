import json
import boto3
import time
from datetime import datetime

def lambda_handler(event, context):
    rds_client = boto3.client('rds')
    dynamodb = boto3.resource('dynamodb')
    sns_client = boto3.client('sns')
    
    table = dynamodb.Table('SecurityComplianceResults')
    
    # REPLACE with your SNS topic ARN
    sns_topic_arn = 'arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:SecurityAlerts'
    
    # Get all RDS instances
    try:
        response = rds_client.describe_db_instances()
        db_instances = response['DBInstances']
    except Exception as e:
        print(f"Error describing RDS instances: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps('Error listing RDS instances')}
    
    results = []
    timestamp = int(time.time())
    compliant_count = 0
    non_compliant_count = 0
    non_compliant_resources = []
    
    for db in db_instances:
        db_identifier = db['DBInstanceIdentifier']
        engine = db['Engine']
        storage_encrypted = db.get('StorageEncrypted', False)
        
        if storage_encrypted:
            status = "COMPLIANT"
            message = f"RDS instance is encrypted (Engine: {engine})"
            compliant_count += 1
        else:
            status = "NON_COMPLIANT"
            message = f"RDS instance is NOT encrypted (Engine: {engine})"
            non_compliant_count += 1
            non_compliant_resources.append(f"RDS Instance: {db_identifier} - {message}")
        
        # Store result in DynamoDB
        try:
            table.put_item(
                Item={
                    'ResourceId': f"rds::{db_identifier}",
                    'Timestamp': timestamp,
                    'ResourceType': 'RDSInstance',
                    'ResourceName': db_identifier,
                    'Engine': engine,
                    'Status': status,
                    'Message': message,
                    'CheckType': 'StorageEncryption',
                    'CheckTime': datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"Error writing to DynamoDB: {str(e)}")
        
        results.append({
            'db_instance': db_identifier,
            'engine': engine,
            'status': status,
            'message': message
        })
        
        print(f"Checked {db_identifier}: {status} - {message}")
    
    # Send SNS alert if non-compliant resources found
    if non_compliant_resources:
        alert_subject = f"Security Alert: {non_compliant_count} Unencrypted RDS Instances"
        alert_message = f"""AWS Security Compliance Alert

Scan completed at: {datetime.now().isoformat()}

Summary:
- Total RDS Instances Checked: {len(results)}
- Compliant (Encrypted): {compliant_count}
- Non-Compliant (Unencrypted): {non_compliant_count}

Non-Compliant Resources:
{chr(10).join(non_compliant_resources)}

Action Required:
Enable encryption on RDS instances to protect data at rest.

To fix:
1. Create a snapshot of the unencrypted DB instance
2. Copy the snapshot and enable encryption during copy
3. Restore a new DB instance from the encrypted snapshot
4. Update application connection strings
5. Delete the old unencrypted instance

Note: Encryption cannot be enabled on existing RDS instances directly.
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
        'total_rds_instances': len(results),
        'compliant': compliant_count,
        'non_compliant': non_compliant_count,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"Summary: {json.dumps(summary)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary)
    }
