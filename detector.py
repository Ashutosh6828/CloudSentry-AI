import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os
import json
import logging
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Configuration ---
PROCESSED_FILE = "data/processed_features.csv"
MODEL_FILE = "data/anomaly_model.joblib"
ORIGINAL_LOGS_FILE = "data/raw_logs.jsonl"
TRUE_POSITIVES_FILE = "data/true_positives.txt"

# --- InfluxDB Configuration ---
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "vn5TnynGiTCNT5iLPdZ7UrNUsGC0TNCYWQe4hD37s0C904OmG7e65XVVAmNoEgPnShdQiNLuzfFWVx0qc0JrlA=="
INFLUX_ORG = "myorg"
INFLUX_BUCKET = "cloudtrail_logs"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Triage & Response Functions ---
def score_event(row):
    """Assigns a severity score based on predefined rules."""
    score = 0
    if row.get('eventSource') in ['signin.amazonaws.com', 'iam.amazonaws.com']: score += 3
    if row.get('hour', 12) < 6 or row.get('hour', 12) > 22: score += 2
    if row.get('eventName') in ['DeleteBucket', 'StopInstances', 'CreateUser', 'DeleteTrail']: score += 5
    return score

def categorize_severity(score):
    """Categorizes the severity score into Low, Medium, or High."""
    if score >= 7: return "High"
    elif score >= 4: return "Medium"
    else: return "Low"

def containment_workflow(triage_df):
    """Simulates containment actions and adds a containment tag."""
    actions = []
    for _, row in triage_df.iterrows():
        if row['severity_level'] == "High":
            action = "Disable user/session, rotate keys, block suspicious IP"
        elif row['severity_level'] == "Medium":
            action = "Restrict IAM role temporarily, enable MFA, monitor"
        else:
            action = "Monitor activity"
        actions.append(action)
    triage_df['containment_action'] = actions
    triage_df['containment_tag'] = "Contained - " + triage_df['severity_level']
    return triage_df

def eradication_action(row):
    """Simulates eradication actions based on severity level."""
    if row['severity_level'] == "High":
        return "Disable IAM user, rotate keys, check impacted resources"
    elif row['severity_level'] == "Medium":
        return "Restrict IAM role temporarily, enable MFA, monitor activity"
    else:
        return "Monitor only"

def recovery_action(row):
    """Simulates recovery actions based on severity level."""
    if row['severity_level'] == "High":
        return "Restore resources, verify backups, re-enable safe IAM users"
    elif row['severity_level'] == "Medium":
        return "Verify resources and IAM roles, monitor activity"
    else:
        return "No action needed, just monitor"

# --- Metric & Export Functions ---
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

def export_anomalies_to_influxdb(anomalous_logs_df):
    """Connects to InfluxDB and writes enriched anomalous logs."""
    logging.info(f"Writing {len(anomalous_logs_df)} enriched anomalies to bucket '{INFLUX_BUCKET}'...")
    with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        for index, row in anomalous_logs_df.iterrows():
            point = (
                Point("anomaly_event")
                .tag("eventSource", row.get("eventSource", "Unknown"))
                .tag("eventName", row.get("eventName", "Unknown"))
                .tag("awsRegion", row.get("awsRegion", "Unknown"))
                .tag("severity", row.get("severity_level", "Unknown"))
                .field("sourceIPAddress", row.get("sourceIPAddress", "N/A"))
                .field("is_anomaly", 1)
                .field("severity_score", int(row.get("severity_score", 0)))
                .field("containment_action", row.get("containment_action", "N/A"))
                .field("containment_tag", row.get("containment_tag", "N/A"))
                .field("eradication_action", row.get("eradication_action", "N/A"))
                .field("recovery_action", row.get("recovery_action", "N/A"))
                .time(row["eventTime"])
            )
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    logging.info("✅ Successfully wrote enriched anomalies to InfluxDB.")

def detect_anomalies():
    """Loads data, trains model, detects, triages, and simulates response for anomalies."""
    if not os.path.exists(PROCESSED_FILE) or os.path.getsize(PROCESSED_FILE) == 0:
        logging.warning(f"Processed file empty. Skipping detection.")
        send_metric_to_influxdb("pipeline_metrics", "anomalies_detected", 0)
        send_metric_to_influxdb("pipeline_metrics", "normal_events", 0)
        return

    logging.info("Starting anomaly detection.")
    df_processed = pd.read_csv(PROCESSED_FILE)
    
    if df_processed.empty:
        logging.info("No data to process. Skipping.")
        send_metric_to_influxdb("pipeline_metrics", "anomalies_detected", 0)
        send_metric_to_influxdb("pipeline_metrics", "normal_events", 0)
        return

    features = [col for col in df_processed.columns if '_code' in col or col == 'hour']
    X = df_processed[features]

    logging.info("Training a new Isolation Forest model for this run.")
    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(X)
    joblib.dump(model, MODEL_FILE)
    logging.info(f"✅ Latest model saved to {MODEL_FILE}")

    df_processed['anomaly'] = model.predict(X)
    
    df_original = pd.read_json(ORIGINAL_LOGS_FILE, lines=True)
    df_original["eventTime"] = pd.to_datetime(df_original["eventTime"])
    
    anomaly_indices = df_processed[df_processed['anomaly'] == -1].index
    anomalous_logs = df_original.iloc[anomaly_indices].copy()
    
    total_records = len(df_processed)
    anomaly_count = len(anomalous_logs)
    normal_count = total_records - anomaly_count

    # --- SEND ALL METRICS ---
    send_metric_to_influxdb("pipeline_metrics", "anomalies_detected", anomaly_count)
    send_metric_to_influxdb("pipeline_metrics", "normal_events", normal_count)

    if anomalous_logs.empty:
        logging.info("No anomalies detected in this run.")
    else:
        logging.info(f"Detected {anomaly_count} anomalies. Starting triage and response simulation...")
        anomalous_logs["hour"] = anomalous_logs["eventTime"].dt.hour
        
        # --- TRIAGE & RESPONSE WORKFLOW ---
        anomalous_logs['severity_score'] = anomalous_logs.apply(score_event, axis=1)
        anomalous_logs['severity_level'] = anomalous_logs['severity_score'].apply(categorize_severity)
        anomalous_logs = containment_workflow(anomalous_logs)
        anomalous_logs['eradication_action'] = anomalous_logs.apply(eradication_action, axis=1)
        anomalous_logs['recovery_action'] = anomalous_logs.apply(recovery_action, axis=1)
        logging.info("✅ Triage and response simulation complete.")
        
        export_anomalies_to_influxdb(anomalous_logs)

if __name__ == "__main__":
    detect_anomalies()
