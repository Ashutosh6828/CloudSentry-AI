import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
import os

# =========================
# Logging and InfluxDB Config
# =========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "vn5TnynGiTCNT5iLPdZ7UrNUsGC0TNCYWQe4hD37s0C904OmG7e65XVVAmNoEgPnShdQiNLuzfFWVx0qc0JrlA=="
INFLUX_ORG = "myorg"
INFLUX_BUCKET = "cloudtrail_logs" # Use the same bucket
DATASET_FILE = "csv_result-KDDTrain+.csv" # The labeled dataset from your notebook

def send_metric_to_influxdb(measurement, field, value):
    """Sends a single metric value to InfluxDB."""
    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = Point(measurement).field(field, float(value)) # Ensure value is float
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            logging.info(f"✅ Successfully wrote metric '{field}={value}' to InfluxDB.")
    except Exception as e:
        logging.error(f"Failed to write metric to InfluxDB: {e}")

def evaluate_model():
    """
    Loads data, analyzes it, trains the supervised model, evaluates it, 
    and sends all metrics to InfluxDB.
    """
    if not os.path.exists(DATASET_FILE):
        logging.error(f"Dataset file not found: {DATASET_FILE}. Please download it.")
        return

    logging.info(f"Loading dataset from {DATASET_FILE}...")
    df = pd.read_csv(DATASET_FILE)

    # --- Preprocessing (from your notebook) ---
    df.columns = df.columns.str.replace("'", "").str.strip()
    df["class"] = df["class"].astype(str).replace("0", "anomaly")
    
    # --- NEW: Analyze and Send Dataset Composition ---
    logging.info("Analyzing dataset composition...")
    class_counts = df['class'].value_counts()
    normal_count = class_counts.get('normal', 0)
    anomaly_count = class_counts.get('anomaly', 0)
    logging.info(f"Dataset contains {normal_count} normal records and {anomaly_count} anomaly records.")
    
    send_metric_to_influxdb("dataset_stats", "normal_records", normal_count)
    send_metric_to_influxdb("dataset_stats", "anomaly_records", anomaly_count)
    # --- END OF NEW CODE ---

    X = df.drop(["id", "class"], axis=1)
    y_raw = df["class"]

    categorical_cols = X.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col])

    target_encoder = LabelEncoder()
    y = target_encoder.fit_transform(y_raw)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42, stratify=y
    )
    logging.info("Preprocessing complete.")

    # --- Model Training ---
    logging.info("Training RandomForestClassifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    logging.info("Model training complete.")

    # --- Evaluation ---
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred) * 100
    precision = precision_score(y_test, y_pred, average='binary') * 100
    recall = recall_score(y_test, y_pred, average='binary') * 100
    f1 = f1_score(y_test, y_pred, average='binary') * 100

    logging.info(f"Accuracy: {accuracy:.2f}%")
    logging.info(f"Precision: {precision:.2f}%")
    logging.info(f"Recall: {recall:.2f}%")
    logging.info(f"F1-Score: {f1:.2f}%")

    # --- Send Performance Metrics to InfluxDB ---
    send_metric_to_influxdb("supervised_performance", "accuracy", accuracy)
    send_metric_to_influxdb("supervised_performance", "precision", precision)
    send_metric_to_influxdb("supervised_performance", "recall", recall)
    send_metric_to_influxdb("supervised_performance", "f1_score", f1)

if __name__ == "__main__":
    evaluate_model()
