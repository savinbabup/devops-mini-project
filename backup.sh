#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M)
docker compose exec -T db pg_dump -U admin myapp > "backup-$DATE.sql"
echo "Backup saved as backup-$DATE.sql"
