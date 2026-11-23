"""Tests for the visitor-counter + guestbook app.

No real database is needed: psycopg2.connect is replaced with a fake
connection, so the tests run anywhere (including GitHub Actions).
"""

import re

import pytest

import app as app_module


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    """Point the app at a fake in-memory database."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "myapp")
    monkeypatch.setenv("DB_USER", "admin")
    monkeypatch.setenv("DB_PASSWORD", "test-password")

    class FakeCursor:
        def __init__(self):
            self.count = 42
            self.messages = [
                ("Asha", "Hello from the test!", None),
                ("Rahul", "Nice project", None),
            ]
            self.executed = []

        def execute(self, query, params=None):
            self.executed.append((query, params))
            if "INSERT INTO messages" in query:
                self.messages.insert(0, (params[0], params[1], None))

        def fetchone(self):
            return (self.count,)

        def fetchall(self):
            return self.messages

        def close(self):
            pass

    class FakeConn:
        def __init__(self):
            self.cursor_obj = FakeCursor()

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            pass

        def close(self):
            pass

    fake_conn = FakeConn()
    monkeypatch.setattr(
        app_module.psycopg2, "connect", lambda **kwargs: fake_conn
    )
    return fake_conn


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def metric_value(text, name):
    """Read one counter value out of /metrics output."""
    match = re.search(rf"^{name} (\d+(?:\.\d+)?)$", text, re.MULTILINE)
    assert match, f"{name} not found in /metrics"
    return float(match.group(1))


def test_home_returns_200_and_visitor_number(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Hello from Docker!" in resp.data
    assert b"You are visitor number 42." in resp.data


def test_home_shows_guestbook_form_and_messages(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"<form" in resp.data
    assert b'name="name"' in resp.data
    assert b'name="message"' in resp.data
    assert b"Asha" in resp.data
    assert b"Hello from the test!" in resp.data


def test_post_message_redirects_and_counts(client, fake_db):
    before = metric_value(client.get("/metrics").data.decode(), "app_messages_total")
    resp = client.post(
        "/message",
        data={"name": "Test User", "message": "CI says hello"},
        follow_redirects=False,
    )
    assert resp.status_code in (301, 302, 303, 307, 308)
    assert resp.headers["Location"].endswith("/")
    after = metric_value(client.get("/metrics").data.decode(), "app_messages_total")
    assert after == before + 1
    # The message really reached the (fake) database.
    inserts = [
        params
        for query, params in fake_db.cursor_obj.executed
        if "INSERT INTO messages" in query
    ]
    assert inserts == [("Test User", "CI says hello")]


def test_metrics_exposes_both_counters(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"app_visits_total" in resp.data
    assert b"app_messages_total" in resp.data
