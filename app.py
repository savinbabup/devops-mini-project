from flask import Flask, Response
import psycopg2, os, time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

VISITS = Counter("app_visits_total", "Total visits to the home page")
REQUEST_TIME = Histogram("app_request_seconds", "Time spent on requests")

def get_count():
    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY)")
    cur.execute("INSERT INTO visits DEFAULT VALUES")
    cur.execute("SELECT COUNT(*) FROM visits")
    count = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return count

@app.route("/")
def home():
    start = time.time()
    count = get_count()
    VISITS.inc()
    REQUEST_TIME.observe(time.time() - start)
    return f"<h1>Hello from Docker!</h1><p>You are visitor number {count}.</p>"

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
