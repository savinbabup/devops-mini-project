# DevOps mini project — visitor counter with Grafana monitoring

Mac-compatible. Built phase by phase on 2026-11-20: a Flask website + PostgreSQL
database in Docker containers, with Prometheus collecting metrics and Grafana
showing them live, plus an alert and a backup script. About 3 hours total.

## What it is

- **web** — Flask app. Every refresh adds a visit to the database and shows
  "You are visitor number N". It also exposes `/metrics` for Prometheus.
- **db** — PostgreSQL 16. Visits are stored here, so the count survives restarts.
- **prometheus** — collects the app's numbers every 5 seconds.
- **grafana** — draws the numbers as live graphs.
- **node-exporter** — exposes CPU / system numbers for the CPU panel.

## Phase 0 — Setup (20 min)

1. Install Docker Desktop for Mac — Apple Chip version for M1/M2/M3, Intel Chip
   for older Macs. Open it once so it starts.
2. Install VS Code.
3. In Terminal, check: `docker --version`
4. Put this folder on your Mac and open it in VS Code.

## Phase 1 — Run it

```bash
docker compose up --build
```

Open http://localhost:5000 and refresh — the visitor number goes up each time.
First run is slow: Docker downloads the images. Just wait.

## Phase 2 — Check Prometheus is collecting (15 min)

- Open http://localhost:9090 → Status → Targets. Both `web` and `node` should say UP.
- Search `app_visits_total` and press Execute — you should see your visitor count.

## Phase 3 — Build the Grafana dashboard (45 min)

- Open http://localhost:3000, log in with `admin` / `admin`.
  (Grafana may ask you to change the password on first login — you can skip it.)
- Connections → Data sources → Add data source → Prometheus.
  URL: `http://prometheus:9090` → Save & test. It should say "Successfully queried."
- New dashboard, 4 panels:
  1. Stat, "Total Visitors" — `app_visits_total`
  2. Time series, "Visitors per minute" — `rate(app_visits_total[1m])`
  3. Time series, "CPU usage %" — `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)`
  4. Stat, "App Status" — `up{job="web"}` (1 = running, 0 = down)
- Save as "Visitor App Monitoring". Refresh the website a few times and watch
  the graphs move — that is your live demo.

## Phase 4 — Add an alert (20 min)

- Open the "App Status" panel → Alert tab → create an alert rule: when the
  value is below 1 for 1 minute.
- Test it: `docker compose stop web`, wait a minute, watch the alert fire in
  Grafana. Then `docker compose start web` and it goes back to normal.

## Phase 5 — Backup + finish (30 min)

```bash
chmod +x backup.sh
./backup.sh
```

That saves a `backup-*.sql` file. To prove it works: `docker compose down -v`,
then `docker compose up -d`, then restore with
`docker compose exec -T db psql -U admin myapp < backup-YYYY-MM-DD_HH-MM.sql`
— refresh the page and your old visitor count is back.

Write a short README note of your own: what the project does, the architecture
(web → database, Prometheus → Grafana), and how to run it with one command.

## Ports

| Service | URL | Login |
|---|---|---|
| Website | http://localhost:5000 | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Node exporter | http://localhost:9100 | — |

## If something breaks

- Port already in use → change the left number in the ports mapping in
  `docker-compose.yml`, e.g. `"5001:5000"`.
- Change the demo database password (`secret123` in `docker-compose.yml`)
  before sharing the project publicly — it is only a local demo password.

## Demo checklist (presentation day)

- [ ] Start Docker Desktop
- [ ] `docker compose up -d`
- [ ] Open the website, refresh it a few times
- [ ] Open Grafana, show the dashboard moving
- [ ] `docker compose stop web` to show the alert firing, then start it again

## To make this final-year worthy

As it stands this is a strong mini project. For a final-year project, add:
1. A real app (e.g. a task manager with login) instead of just a counter.
2. A CI/CD pipeline (GitHub Actions: test → build image → deploy on every push).
3. Cloud deployment (free tier like Render or Railway) so there is a live link.
4. Keep the Grafana monitoring + alert — it is the part examiners love most.
