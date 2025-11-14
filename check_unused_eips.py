import json
import boto3
import time
from datetime import datetime

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    dynamodb = boto3.resource('dynamodb')
    sns_client = boto3.client('sns')
    
    table = dynamodb.Table('SecurityComplianceResults')
    
    # REPLACE with your SNS topic ARN
    sns_topic_arn = 'arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:SecurityAlerts'
    
    # Get all Elastic IPs
    try:
        response = ec2_client.describe_addresses()
        addresses = response['Addresses']
    except Exception as e:
        print(f"Error describing Elastic IPs: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps('Error listing Elastic IPs')}
    
    results = []
    timestamp = int(time.time())
    attached_count = 0
    unattached_count = 0
    unattached_resources = []
    monthly_cost_per_eip = 3.60  # Approximate cost per unused EIP per month
    
    for address in addresses:
        allocation_id = address.get('AllocationId', 'N/A')
        public_ip = address.get('PublicIp', 'N/A')
        instance_id = address.get('InstanceId')
        association_id = address.get('AssociationId')
        
        # Check if EIP is attached to an instance
        if instance_id or association_id:
            status = "ATTACHED"
            message = f"Elastic IP is attached to instance {instance_id}"
            attached_count += 1
        else:
            status = "UNATTACHED"
            message = f"Elastic IP is NOT attached (wasting ${monthly_cost_per_eip}/month)"
            unattached_count += 1
            unattached_resources.append(f"Elastic IP: {public_ip} ({allocation_id}) - {message}")
        
        # Store result in DynamoDB
        try:
            table.put_item(
                Item={
                    'ResourceId': f"eip::{allocation_id}",
                    'Timestamp': timestamp,
                    'ResourceType': 'ElasticIP',
                    'ResourceName': public_ip,
                    'AllocationId': allocation_id,
                    'Status': status,
                    'Message': message,
                    'CheckType': 'UnusedResource',
                    'CheckTime': datetime.now().isoformat(),
                    'MonthlyCost': monthly_cost_per_eip if status == 'UNATTACHED' else 0
                }
            )
        except Exception as e:
            print(f"Error writing to DynamoDB: {str(e)}")
        
        results.append({
            'public_ip': public_ip,
            'allocation_id': allocation_id,
            'status': status,
            'message': message
        })
        
        print(f"Checked {public_ip}: {status} - {message}")
    
    # Calculate potential savings
    potential_monthly_savings = unattached_count * monthly_cost_per_eip
    potential_yearly_savings = potential_monthly_savings * 12
    
    # Send SNS alert if unattached resources found
    if unattached_resources:
        alert_subject = f"Cost Optimization Alert: {unattached_count} Unused Elastic IPs"
        alert_message = f"""AWS Cost Optimization Alert

Scan completed at: {datetime.now().isoformat()}

Summary:
- Total Elastic IPs: {len(results)}
- Attached (In Use): {attached_count}
- Unattached (Wasting Money): {unattached_count}

💰 Cost Impact:
- Monthly Cost: ${potential_monthly_savings:.2f}
- Yearly Cost: ${potential_yearly_savings:.2f}

Unattached Elastic IPs:
{chr(10).join(unattached_resources)}

Action Required:
Release unused Elastic IPs to save costs.

To fix:
1. Go to EC2 console
2. Navigate to Elastic IPs
3. Select the unattached Elastic IP
4. Click Actions → Release Elastic IP address
5. Confirm the release

⚠️ Warning: Only release IPs you're sure you don't need!
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
        'total_elastic_ips': len(results),
        'attached': attached_count,
        'unattached': unattached_count,
        'potential_monthly_savings': round(potential_monthly_savings, 2),
        'potential_yearly_savings': round(potential_yearly_savings, 2),
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"Summary: {json.dumps(summary)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary)
    }
