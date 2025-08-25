# CloudSentry

CloudSentry is a security-focused project built with Python libraries to detect anomalies in cloud environments. It leverages **machine learning** techniques, specifically the **Isolation Forest algorithm**, to identify unusual patterns and activities within AWS CloudTrail logs stored in S3 buckets.  

---

## 🚀 Features
- **Anomaly Detection with Isolation Forest**  
  Utilizes an unsupervised machine learning approach to catch deviations in log behavior without requiring labeled data.  

- **Severity Analysis**  
  After anomalies are detected, the system classifies them by severity to prioritize response actions.  

- **Real-time Visualization**  
  A full **Grafana dashboard** is integrated to monitor detected anomalies, trends, and severity levels in real time.  

- **Cloud-native Integration**  
  Built around AWS services, using **S3 for log storage** and **CloudTrail logs** as the primary data source.  

---

## ⚙️ How It Works
1. **Log Collection** – AWS CloudTrail logs are stored in S3 buckets.  
2. **Preprocessing** – Python scripts clean and prepare logs for modeling.  
3. **Anomaly Detection** – Isolation Forest model detects unusual activities.  
4. **Severity Check** – Each anomaly is assigned a severity level.  
5. **Dashboard Visualization** – Results are pushed to Grafana for monitoring.  

---

## 📊 Dashboard
The Grafana dashboard provides:  
- Real-time anomaly counts  
- Severity breakdown (Low, Medium, High)  
- Historical trends of anomalies  
- Log-level insights for cloud activities  

---

## 🛠️ Tech Stack
- **Language**: Python  
- **Machine Learning**: scikit-learn (Isolation Forest)  
- **Visualization**: Grafana  
- **Cloud**: AWS (S3, CloudTrail)  

---

## 🔒 Purpose
CloudSentry enhances cloud security by proactively identifying anomalies, prioritizing threats, and giving teams a real-time view of their cloud activities.

---
