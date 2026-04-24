"""
system_monitor.py
Sends machine metrics to Elasticsearch every 30 seconds.
"""
import time
import psutil
from datetime import datetime, timezone
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

print("📊 System monitor started — sending metrics to ES every 30s")
print("Press Ctrl+C to stop")

while True:
    doc = {
        "@timestamp":   datetime.now(timezone.utc).isoformat(),
        "type":         "system_metrics",
        "cpu_percent":  psutil.cpu_percent(interval=1),
        "ram_percent":  psutil.virtual_memory().percent,
        "ram_used_gb":  round(psutil.virtual_memory().used / 1e9, 2),
        "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 2),
        "disk_percent": psutil.disk_usage('/').percent,
        "disk_used_gb": round(psutil.disk_usage('/').used / 1e9, 2),
        "disk_free_gb": round(psutil.disk_usage('/').free / 1e9, 2),
    }
    es.index(index="system-metrics", document=doc)
    print(f"✅ {doc['@timestamp']} | CPU: {doc['cpu_percent']}% | RAM: {doc['ram_percent']}% | Disk: {doc['disk_percent']}%")
    time.sleep(30)
