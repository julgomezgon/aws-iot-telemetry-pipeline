import json
import boto3
import base64
import logging
from decimal import Decimal 

# Logging Configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Resource Initialization
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'iot-device-status'
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    processed_count = 0
    
    for record in event['Records']:
        try:
            # 1. Decode Base64
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            
            # 2. Parse JSON converting floats to Decimals (Crucial for DynamoDB)
            data = json.loads(payload, parse_float=Decimal)
            
            device_id = data.get('device_id', 'Unknown')
            logger.info(f"Processing telemetry for device: {device_id}")
            
            # 3. Persistence to DynamoDB (Hot Path)
            table.put_item(Item=data)
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            continue
            
    return {
        'statusCode': 200,
        'body': json.dumps({'records_count': processed_count})
    }
