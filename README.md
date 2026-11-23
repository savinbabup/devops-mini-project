# DevOps mini project — visitor counter with Grafana monitoring

[![CI](https://github.com/savinbabup/devops-mini-project/actions/workflows/ci.yml/badge.svg)](https://github.com/savinbabup/devops-mini-project/actions/workflows/ci.yml)

**By Savin Babu P — B.Tech Computer Science and Technology (DevOps), Presidency University, Bangalore.**

A visitor-counter website with a guestbook, running in Docker: every visit is saved in PostgreSQL,
Prometheus collects the numbers, Grafana shows them live on a dashboard, and an
alert fires when the website goes down. A backup script saves the database and
can restore it. Every push to GitHub is automatically tested by a CI pipeline,
and the project can be deployed to Render's free tier.

Architecture: browser → Flask website → PostgreSQL; Flask → Prometheus → Grafana.
Run it with one command: `docker compose up -d`, then open http://localhost:5001.

Status: all phases complete and tested (November 2026) — website live, Prometheus
scraping, Grafana dashboard saved, alert tested, backup and restore proven.
Guestbook, CI pipeline and Render deploy added afterwards.

Live URL: https://visitor-counter-d2hz.onrender.com

## What it is

- **web** — Flask app. Every refresh adds a visit to the database and shows
  "You are visitor number N". It also exposes `/metrics` for Prometheus.
- **guestbook** — visitors can leave their name and a message on the home page
  (`POST /message`). Messages are saved in PostgreSQL and the 20 most recent
  are shown on the page. A second Prometheus counter, `app_messages_total`,
  counts every message saved.
- **db** — PostgreSQL 16. Visits and messages are stored here, so they survive restarts.
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

Open http://localhost:5001 and refresh — the visitor number goes up each time.
First run is slow: Docker downloads the images. Just wait.

Note: the website runs on port **5001**, not 5000, because macOS AirPlay Receiver
already uses port 5000.

## Phase 2 — Check Prometheus is collecting (15 min)

- Open http://localhost:9090 → Status → Targets. Both `web` and `node` should say UP.
- Search `app_visits_total` and press Execute — you should see your visitor count.
- Search `app_messages_total` to see how many guestbook messages were saved.

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

- Alerting → Alert rules → New alert rule: name `app is down`, query
  `up{job="web"}`, condition "when the value is below 1 for 1 minute".
- Test it: `docker compose stop web`, wait a minute, watch the alert fire in
  Grafana. Then `docker compose start web` and it goes back to normal.

## Phase 5 — Backup + finish (30 min)

```bash
chmod +x backup.sh
./backup.sh
```

That saves a `backup-*.sql` file. To prove it works, stop the stack and delete
only the database volume — never `docker compose down -v`, that would also
delete Grafana and your dashboard:

```bash
docker compose down
docker volume rm devops-mini-project_db-data
docker compose up -d
```

Then empty the fresh table and restore the backup:

```bash
docker compose exec -T db psql -U admin myapp -c "TRUNCATE visits RESTART IDENTITY;"
docker compose exec -T db psql -U admin myapp < backup-YYYY-MM-DD_HH-MM.sql
```

Refresh the page and your old visitor count is back. The backup covers the
guestbook messages too — they are in the same database.

## Guestbook

The home page has a small form: name + message. Submitting it saves the message
in the `messages` table and takes you back to the home page, where the 20 most
recent messages are shown newest first. The `app_messages_total` counter in
`/metrics` goes up by one for every message saved.

## CI pipeline

Every push and pull request to `main` runs the GitHub Actions workflow in
`.github/workflows/ci.yml` — see the green badge at the top of this README:

1. **test** — installs the requirements, installs pytest, runs `test_app.py`
   (the database is mocked, so no real database is needed).
2. **docker** — builds the Docker image from the Dockerfile, so a broken
   Dockerfile is caught before deploy.
3. **integration** — starts a real PostgreSQL 16 service, runs the app against
   it, checks `/` and `/metrics` return 200, and posts a guestbook message.

To run the tests on your own machine:

```bash
pip install -r requirements.txt pytest
pytest -v
```

## Cloud deploy (Render)

`render.yaml` is a Render blueprint: it creates a free web service from the
Dockerfile and a free PostgreSQL database, and wires the database settings
into the app automatically. The app listens on the `PORT` Render gives it.

1. Create a free account at https://render.com and connect your GitHub account.
2. In Render: New → Blueprint, pick this repository.
3. Render reads `render.yaml` and shows the web service + database. Click Apply.
4. Wait for the deploy to finish, then open the web service URL Render gives you.
5. Paste that URL in the "Live URL" line at the top of this README.

Note: Grafana and Prometheus are not part of the Render deploy — they keep
running in Docker on your Mac. The Render copy is the public website only.

## Ports

| Service | URL | Login |
|---|---|---|
| Website | http://localhost:5001 | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Node exporter | http://localhost:9100 | — |

## If something breaks

- Port already in use → change the left number in the ports mapping in
  `docker-compose.yml`, e.g. `"5001:5000"`.
- Change the demo database password in `docker-compose.yml` before sharing
  the project publicly — it is only a local demo password. Remember to change
  it in both places in the file (the web service and the database service),
  then recreate the database as described in the password-change steps.

## Demo checklist (presentation day)

- [ ] Start Docker Desktop
- [ ] `docker compose up -d`
- [ ] Open the website, refresh it a few times
- [ ] Leave a guestbook message and watch it appear on the page
- [ ] Open Grafana, show the dashboard moving
- [ ] `docker compose stop web` to show the alert firing, then start it again

## To make this final-year worthy

The three upgrades from the original mini project are now done: a real app
feature (guestbook), a CI/CD pipeline (GitHub Actions), and cloud deploy
(Render). To go further, add:
1. Login for the guestbook (only signed-in users can post, and can delete
   their own messages).
2. More tests — for example, a test that an empty message is not saved.
3. A custom domain for the Render link.
4. Keep the Grafana monitoring + alert — it is the part examiners love most.
