#!/bin/sh
# Start Prometheus bound to Render's $PORT (default 9090 for local runs).
exec /bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.listen-address=0.0.0.0:${PORT:-9090}
