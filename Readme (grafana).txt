### \#\# 1. Consolidated Queries for Dashboard Panels

These are the individual queries you can paste into new panels in Grafana.

#### \#\#\# For InfluxDB (Metrics Data)

Use these Flux queries when your data source is InfluxDB. Remember to replace `"cloudtrail_logs"` with your actual bucket name if it's different.

**Panel: Total Anomalies (Stat Panel)**

```js
from(bucket: "cloudtrail_logs")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "pipeline_metrics" and r["_field"] == "anomalies_detected")
  |> last()
```

**Panel: Total Normal Events (Stat Panel)**

```js
from(bucket: "cloudtrail_logs")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "pipeline_metrics" and r["_field"] == "normal_events")
  |> last()
```

**Panel: Normal vs. Anomaly Comparison (Bar Chart)**
*Note: Use this query with the "Labels to fields" transformation.*

```js
// Query for Anomalies
anomalies = from(bucket: "cloudtrail_logs")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "pipeline_metrics" and r["_field"] == "anomalies_detected")
  |> last()
  |> set(key: "type", value: "Anomalous")

// Query for Normal Events
normal = from(bucket: "cloudtrail_logs")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "pipeline_metrics" and r["_field"] == "normal_events")
  |> last()
  |> set(key: "type", value: "Normal")

// Combine the results
union(tables: [anomalies, normal])
```

-----

#### \#\#\# For Loki (Anomaly Logs)

Use these LogQL queries if you also set up Loki to store the detailed anomaly logs.

**Panel: Live Anomaly Log Stream (Logs Panel)**

```logql
{application="ey_incident_response"}
```

**Panel: Anomaly Count Over Time (Time Series Panel)**

```logql
sum(rate({application="ey_incident_response"}[5m])) by (event_name)
```

**Panel: Top Anomalous Events (Bar Chart Panel)**

```logql
sum by (event_name) (count_over_time({application="ey_incident_response"}[$__range]))
```

-----

### \#\# 2. Complete Dashboard as Code (JSON Model)

This is the most powerful way to use "code in one". You can import this entire JSON file to create a complete dashboard instantly.

**How to Use:**

1.  Go to your Grafana dashboard view.
2.  Click **New** in the top right and select **Import**.
3.  Paste the entire JSON code below into the text box.
4.  Grafana will ask you to select your **InfluxDB** and **Loki** data sources. Link them to the ones you have already configured.
5.  Click **Import**.

**Dashboard JSON Code:**

```json
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "links": [],
  "panels": [
    {
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "11.1.0",
      "targets": [
        {
          "datasource": {
            "type": "influxdb",
            "uid": "YOUR_INFLUXDB_UID"
          },
          "query": "from(bucket: \"cloudtrail_logs\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r[\"_measurement\"] == \"pipeline_metrics\" and r[\"_field\"] == \"anomalies_detected\")\n  |> last()",
          "refId": "A"
        }
      ],
      "title": "Anomalies Detected",
      "type": "stat"
    },
    {
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 6,
        "y": 0
      },
      "id": 2,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "11.1.0",
      "targets": [
        {
          "datasource": {
            "type": "influxdb",
            "uid": "YOUR_INFLUXDB_UID"
          },
          "query": "from(bucket: \"cloudtrail_logs\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r[\"_measurement\"] == \"pipeline_metrics\" and r[\"_field\"] == \"normal_events\")\n  |> last()",
          "refId": "A"
        }
      ],
      "title": "Normal Events",
      "type": "stat"
    },
    {
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 3,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "colorByField": "type",
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "auto",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 0
      },
      "pluginVersion": "11.1.0",
      "targets": [
        {
          "datasource": {
            "type": "influxdb",
            "uid": "YOUR_INFLUXDB_UID"
          },
          "query": "anomalies = from(bucket: \"cloudtrail_logs\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r[\"_measurement\"] == \"pipeline_metrics\" and r[\"_field\"] == \"anomalies_detected\")\n  |> last()\n  |> set(key: \"type\", value: \"Anomalous\")\n\nnormal = from(bucket: \"cloudtrail_logs\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r[\"_measurement\"] == \"pipeline_metrics\" and r[\"_field\"] == \"normal_events\")\n  |> last()\n  |> set(key: \"type\", value: \"Normal\")\n\nunion(tables: [anomalies, normal])",
          "refId": "A"
        }
      ],
      "title": "Normal vs. Anomaly Comparison",
      "transformations": [
        {
          "id": "labelsToFields",
          "options": {
            "label": "type",
            "valueLabel": "_value"
          }
        }
      ],
      "type": "barchart"
    },
    {
      "gridPos": {
        "h": 16,
        "w": 24,
        "x": 0,
        "y": 8
      },
      "id": 4,
      "options": {
        "dedupStrategy": "none",
        "enableLogDetails": true,
        "prettifyLogMessage": false,
        "showCommonLabels": false,
        "showLabels": true,
        "showTime": true,
        "sortOrder": "Descending",
        "wrapLogMessage": true
      },
      "pluginVersion": "11.1.0",
      "targets": [
        {
          "datasource": {
            "type": "loki",
            "uid": "YOUR_LOKI_UID"
          },
          "expr": "{application=\"ey_incident_response\"}",
          "refId": "A"
        }
      ],
      "title": "Live Anomaly Log Stream",
      "type": "logs"
    }
  ],
  "refresh": "1m",
  "schemaVersion": 39,
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "browser",
  "title": "CloudTrail Incident Response",
  "uid": "some-unique-id",
  "version": 1,
  "weekStart": ""
}
```