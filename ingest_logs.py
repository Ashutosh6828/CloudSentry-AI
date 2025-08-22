# ingest_logs.py (Processes logs for the current day in UTC)
import boto3
import gzip
import json
import os
import logging
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Configuration ---
S3_BUCKET = "aws-cloudtrail-logs-289979559671-8fc8af41"
AWS_ACCOUNT_ID = "289979559671"
AWS_REGION = "ap-south-1"

OUTPUT_DIR = "data"
RAW_LOGS_FILE = os.path.join(OUTPUT_DIR, "raw_logs.jsonl")

# --- InfluxDB Configuration ---
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "vn5TnynGiTCNT5iLPdZ7UrNUsGC0TNCYWQe4hD37s0C904OmG7e65XVVAmNoEgPnShdQiNLuzfFWVx0qc0JrlA=="
INFLUX_ORG = "myorg"
INFLUX_BUCKET = "cloudtrail_logs"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_metric_to_influxdb(measurement, field, value):
    """Sends a single metric value to InfluxDB."""
    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = Point(measurement).field(field, value)
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            logging.info(f"✅ Successfully wrote metric '{field}={value}' to InfluxDB.")
    except Exception as e:
        logging.error(f"Failed to write metric to InfluxDB: {e}")

def fetch_and_save_logs():
    """
    Fetches CloudTrail logs from S3 for the CURRENT DAY (UTC), 
    and saves the records to a local JSON Lines file.
    """
    s3 = boto3.client("s3")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    logging.info(f"Starting log ingestion from bucket: {S3_BUCKET} for the current day.")
    
    # Get today's date in UTC, as CloudTrail uses UTC
    today_utc = datetime.now(timezone.utc)
    
    # Create the S3 prefix for today
    # Path format: AWSLogs/ACCOUNT_ID/CloudTrail/REGION/YYYY/MM/DD/
    prefix = f"AWSLogs/{AWS_ACCOUNT_ID}/CloudTrail/{AWS_REGION}/{today_utc.year}/{today_utc.month:02d}/{today_utc.day:02d}/"
    
    paginator = s3.get_paginator("list_objects_v2")
    log_file_keys = []

    logging.info(f"Searching for logs with prefix: {prefix}")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj['Key'].endswith('.json.gz'):
                log_file_keys.append(obj['Key'])

    log_file_count = len(log_file_keys)
    send_metric_to_influxdb("pipeline_metrics", "files_processed", log_file_count)

    if not log_file_keys:
        logging.warning("No log files found for today.")
        open(RAW_LOGS_FILE, 'w').close()
        send_metric_to_influxdb("pipeline_metrics", "log_records_ingested", 0) # Send 0 if no files
        return

    logging.info(f"Found {log_file_count} log files to process.")
    
    record_count = 0
    with open(RAW_LOGS_FILE, "w") as outfile:
        for key in log_file_keys:
            try:
                response = s3.get_object(Bucket=S3_BUCKET, Key=key)
                with gzip.GzipFile(fileobj=response['Body']) as gzfile:
                    log_data = json.load(gzfile)
                    records = log_data.get("Records", [])
                    for record in records:
                        outfile.write(json.dumps(record) + '\n')
                        record_count += 1
            except Exception as e:
                logging.error(f"Failed to process file {key}: {e}")

    send_metric_to_influxdb("pipeline_metrics", "log_records_ingested", record_count)
    logging.info(f"✅ Ingestion complete. Wrote {record_count} records to {RAW_LOGS_FILE}")

if __name__ == "__main__":
    fetch_and_save_logs()
