Parses a `graylog_anomaly_detection_*.json` file to generate a list of anomaly detection configurations, and associated information.

Text output is in markdown format. Pipe output to a `.md` file to view formatting.

Text can be copy/pated into a confluence page.

## How to run
Prerequisites:
* Python 3.9

Usage:

```
python3 parse_gad.py --file graylog_anomaly_detection.json > out.md
```

