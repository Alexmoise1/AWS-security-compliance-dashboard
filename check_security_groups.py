import json
import boto3
import time
from datetime import datetime

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('SecurityComplianceResults')
    
    # Get all security groups
    try:
        response = ec2_client.describe_security_groups()
    except Exception as e:
        print(f"Error describing security groups: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps('Error listing security groups')}
    
    results = []
    timestamp = int(time.time())
    compliant_count = 0
    non_compliant_count = 0
    
    for sg in response['SecurityGroups']:
        sg_id = sg['GroupId']
        sg_name = sg['GroupName']
        vpc_id = sg.get('VpcId', 'N/A')
        
        # Check for unrestricted SSH (port 22 from 0.0.0.0/0)
        has_unrestricted_ssh = False
        
        for rule in sg.get('IpPermissions', []):
            # Check if port 22 is allowed
            from_port = rule.get('FromPort')
            to_port = rule.get('ToPort')
            
            if from_port == 22 or to_port == 22 or (from_port is None and to_port is None):
                # Check if it allows 0.0.0.0/0
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        has_unrestricted_ssh = True
                        break
                
                # Check IPv6
                for ip_range in rule.get('Ipv6Ranges', []):
                    if ip_range.get('CidrIpv6') == '::/0':
                        has_unrestricted_ssh = True
                        break
        
        if has_unrestricted_ssh:
            status = "NON_COMPLIANT"
            message = f"Security group allows unrestricted SSH access (0.0.0.0/0 on port 22)"
            non_compliant_count += 1
        else:
            status = "COMPLIANT"
            message = "No unrestricted SSH access detected"
            compliant_count += 1
        
        # Store result in DynamoDB
        try:
            table.put_item(
                Item={
                    'ResourceId': f"sg::{sg_id}",
                    'Timestamp': timestamp,
                    'ResourceType': 'SecurityGroup',
                    'ResourceName': sg_name,
                    'VpcId': vpc_id,
                    'Status': status,
                    'Message': message,
                    'CheckType': 'UnrestrictedSSHAccess',
                    'CheckTime': datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"Error writing to DynamoDB: {str(e)}")
        
        results.append({
            'security_group': sg_name,
            'sg_id': sg_id,
            'status': status,
            'message': message
        })
        
        print(f"Checked {sg_name} ({sg_id}): {status} - {message}")
    
    summary = {
        'total_security_groups': len(results),
        'compliant': compliant_count,
        'non_compliant': non_compliant_count,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"Summary: {json.dumps(summary)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary)
    }
