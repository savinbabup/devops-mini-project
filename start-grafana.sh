#!/bin/sh
# Bind Grafana to Render's $PORT (default 3000 for local runs) and tell it
# its public address, so links and redirects use the real Render URL.
export GF_SERVER_HTTP_PORT=${PORT:-3000}
if [ -n "$RENDER_EXTERNAL_HOSTNAME" ]; then
  export GF_SERVER_ROOT_URL="https://${RENDER_EXTERNAL_HOSTNAME}"
fi
exec /run.sh
