import pandas as pd
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import logging

# --- Configuration ---
INPUT_FILE = "data/raw_logs.jsonl"
OUTPUT_DIR = "data"
PROCESSED_FILE = os.path.join(OUTPUT_DIR, "processed_features.csv")
ENCODERS_FILE = os.path.join(OUTPUT_DIR, "label_encoders.joblib")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def preprocess_logs():
    if not os.path.exists(INPUT_FILE) or os.path.getsize(INPUT_FILE) == 0:
        logging.warning(f"Input file is empty or does not exist: {INPUT_FILE}. Skipping preprocessing.")
        # Create an empty file to prevent the next step from failing
        pd.DataFrame().to_csv(PROCESSED_FILE, index=False)
        return

    logging.info(f"Starting preprocessing of {INPUT_FILE}")

    # Load the raw log data
    df = pd.read_json(INPUT_FILE, lines=True)
    
    # --- UPDATED: Expanded columns of interest to match the notebook analysis ---
    # This provides more features for the model and more context for triage.
    columns_of_interest = [
        "eventTime", "eventName", "eventSource", "awsRegion", 
        "sourceIPAddress", "userAgent", "userIdentity.type", "errorCode",
        "userIdentity.userName", "userIdentity.arn", "userIdentity.principalId",
        "recipientAccountId", "vpcEndpointId", "errorMessage", "requestID",
        "eventID", "responseElements", "managementEvent",
        "sessionCredentialFromConsole"
    ]
    # --- END OF UPDATE ---
    
    # Filter for columns that actually exist in the dataframe to avoid errors
    existing_columns = [col for col in columns_of_interest if col in df.columns]
    df_subset = df[existing_columns].copy()

    # --- Feature Engineering ---
    df_subset["eventTime"] = pd.to_datetime(df_subset["eventTime"])
    df_subset["hour"] = df_subset["eventTime"].dt.hour

    # Encode categorical features
    encoders = {}
    # Define which columns to apply label encoding to
    categorical_cols = [
        "eventName", "eventSource", "awsRegion", "sourceIPAddress", 
        "userAgent", "userIdentity.type", "userIdentity.userName", "errorCode"
    ]
    
    for col in categorical_cols:
        if col in df_subset.columns:
            le = LabelEncoder()
            # Handle potential missing values by converting to string and filling NaNs
            df_subset[col + "_code"] = le.fit_transform(df_subset[col].astype(str).fillna('missing'))
            encoders[col] = le
    
    logging.info("Feature engineering and encoding complete.")
    
    # Save the processed data and the encoders
    df_subset.to_csv(PROCESSED_FILE, index=False)
    joblib.dump(encoders, ENCODERS_FILE)
    
    logging.info(f"✅ Preprocessing complete. Processed data saved to {PROCESSED_FILE}")
    logging.info(f"✅ Label encoders saved to {ENCODERS_FILE}")

if __name__ == "__main__":
    preprocess_logs()
