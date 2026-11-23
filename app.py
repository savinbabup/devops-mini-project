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
        items += f"<li><b>{escape(name)}</b> <small>{when}</small><br>{escape(message)}</li>"
    return (
        f"<h1>Hello from Docker!</h1>"
        f"<p>You are visitor number {count}.</p>"
        f"<h2>Guestbook</h2>"
        f'<form method="post" action="/message">'
        f'<input name="name" placeholder="Your name" required> '
        f'<input name="message" placeholder="Say hello..." required> '
        f'<button type="submit">Leave a message</button>'
        f"</form>"
        f"<ul>{items}</ul>"
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
