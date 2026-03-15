import boto3
import psutil
import json
import time
from datetime import datetime

STREAM_NAME = 'iot-telemetry-stream'
kinesis_client = boto3.client('kinesis', region_name='us-east-1')

def get_metrics():
    # Capture more hardware information
    return {
        'device_id': 'JULIAN-PC-01',
        'timestamp': datetime.utcnow().isoformat(),
        'cpu_usage': psutil.cpu_percent(interval=1),
        'ram_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'net_sent': psutil.net_io_counters().bytes_sent / 1024 / 1024, # MB
        'status': 'ACTIVE'
    }

def start_streaming():
    print("🚀 Streaming enhanced metrics to AWS...")
    while True:
        data = get_metrics()
        kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(data),
            PartitionKey=data['device_id']
        )
        print(f"Sent: CPU {data['cpu_usage']}% | RAM {data['ram_usage']}% | Disk {data['disk_usage']}%")
        time.sleep(3)

if __name__ == "__main__":
    start_streaming()