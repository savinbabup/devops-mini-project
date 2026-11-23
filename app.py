from flask import Flask, Response, request, redirect, url_for
import psycopg2, os, time
from markupsafe import escape
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

VISITS = Counter("app_visits_total", "Total visits to the home page")
MESSAGES = Counter("app_messages_total", "Total guestbook messages saved")
REQUEST_TIME = Histogram("app_request_seconds", "Time spent on requests")

MESSAGES_TABLE = (
    "CREATE TABLE IF NOT EXISTS messages "
    "(id SERIAL PRIMARY KEY, name TEXT, message TEXT, "
    "created_at TIMESTAMP DEFAULT NOW())"
)


def get_conn():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def get_count():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY)")
    cur.execute("INSERT INTO visits DEFAULT VALUES")
    cur.execute("SELECT COUNT(*) FROM visits")
    count = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return count


def get_messages():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(MESSAGES_TABLE)
    cur.execute(
        "SELECT name, message, created_at FROM messages "
        "ORDER BY created_at DESC, id DESC LIMIT 20"
    )
    rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return rows


def save_message(name, message):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(MESSAGES_TABLE)
    cur.execute(
        "INSERT INTO messages (name, message) VALUES (%s, %s)", (name, message)
    )
    conn.commit()
    cur.close()
    conn.close()


PAGE_CSS = """
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; background: #121327; color: #CBD7E6; }
  .wrap { max-width: 720px; margin: 0 auto; padding: 40px 20px 60px; }
  .badge { display: inline-block; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; color: #1FB0BC; border: 1px solid #1FB0BC; border-radius: 999px; padding: 5px 12px; }
  h1 { font-size: 42px; margin: 18px 0 8px; color: #fff; }
  .sub { color: #9FB0C3; margin: 0 0 24px; }
  .hero { background: #1B1E3A; border: 1px solid #2A2E55; border-radius: 16px; padding: 28px; text-align: center; }
  .hero .num { font-size: 64px; font-weight: 800; color: #1FB0BC; line-height: 1; }
  .hero .lbl { margin-top: 8px; color: #9FB0C3; }
  .stack { display: flex; flex-wrap: wrap; gap: 8px; margin: 24px 0; }
  .chip { background: #1B1E3A; border: 1px solid #2A2E55; border-radius: 999px; padding: 6px 12px; font-size: 13px; }
  h2 { margin-top: 36px; color: #fff; }
  form { display: flex; gap: 8px; flex-wrap: wrap; }
  input { flex: 1; min-width: 140px; background: #1B1E3A; border: 1px solid #2A2E55; color: #CBD7E6; border-radius: 10px; padding: 12px; font-size: 15px; }
  button { background: #1FB0BC; color: #08131A; border: 0; border-radius: 10px; padding: 12px 20px; font-size: 15px; font-weight: 700; cursor: pointer; }
  .cards { list-style: none; padding: 0; margin: 20px 0 0; display: grid; gap: 12px; }
  .cards li { background: #1B1E3A; border: 1px solid #2A2E55; border-radius: 12px; padding: 14px 16px; }
  .cards b { color: #fff; }
  .cards small { color: #7E93AB; margin-left: 6px; }
  .cards p { margin: 6px 0 0; }
  footer { margin-top: 40px; color: #7E93AB; font-size: 13px; text-align: center; }
  footer a { color: #4B82C3; }
</style>
"""


@app.route("/")
def home():
    start = time.time()
    count = get_count()
    VISITS.inc()
    REQUEST_TIME.observe(time.time() - start)
    rows = get_messages()
    items = ""
    for name, message, created_at in rows:
        when = created_at.strftime("%d %b %H:%M") if created_at else ""
        items += (
            f"<li><b>{escape(name)}</b><small>{when}</small>"
            f"<p>{escape(message)}</p></li>"
        )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Visitor Counter — DevOps Mini Project</title>"
        + PAGE_CSS
        + "</head><body><div class='wrap'>"
        "<span class='badge'>&#9679; Live</span>"
        "<h1>Hello from Docker!</h1>"
        "<p class='sub'>A tiny website that counts its visitors, running in Docker containers.</p>"
        "<div class='hero'>"
        f"<div class='num'>#{count}</div>"
        f"<div class='lbl'>You are visitor number {count}.</div>"
        "</div>"
        "<div class='stack'>"
        "<span class='chip'>Flask</span><span class='chip'>PostgreSQL</span>"
        "<span class='chip'>Docker</span><span class='chip'>Prometheus</span>"
        "<span class='chip'>Grafana</span>"
        "</div>"
        "<h2>Guestbook</h2>"
        "<p class='sub'>Leave your name and a message — it gets saved in the database.</p>"
        '<form method="post" action="/message">'
        '<input name="name" placeholder="Your name" required> '
        '<input name="message" placeholder="Say hello..." required> '
        '<button type="submit">Leave a message</button>'
        "</form>"
        f"<ul class='cards'>{items}</ul>"
        "<footer>Built by Savin Babu P · DevOps Mini Project · "
        "<a href='https://github.com/savinbabup/devops-mini-project'>GitHub</a></footer>"
        "</div></body></html>"
    )


@app.route("/message", methods=["POST"])
def add_message():
    name = request.form.get("name", "").strip() or "Guest"
    message = request.form.get("message", "").strip()
    if message:
        save_message(name, message)
        MESSAGES.inc()
    return redirect(url_for("home"))


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
