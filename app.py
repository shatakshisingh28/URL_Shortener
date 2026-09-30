"""
URL Shortener
-------------
A simple URL shortener built with Flask + SQLite.

Design (matches the system-design writeup):
  - Each new URL gets an auto-incrementing integer ID from the database.
  - That ID is base62-encoded into a short, unique code (no hashing,
    so no collisions are possible -- every ID maps to exactly one code).
  - Reads (redirects) look up the code and increment a click counter.

Run locally:
    pip install flask
    python app.py
Then open http://127.0.0.1:5000
"""

import sqlite3
import string
from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import Flask, g, redirect, render_template, request, url_for, abort

app = Flask(__name__)
DATABASE = "urls.db"

# --------------------------------------------------------------------------
# Base62 encoding: 0-9, a-z, A-Z  (62 symbols instead of just 10)
# This is what turns database ID 125 into a short string like "cb".
# --------------------------------------------------------------------------
ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE = len(ALPHABET)  # 62


def encode_base62(num: int) -> str:
    """Convert a positive integer into a base62 string."""
    if num == 0:
        return ALPHABET[0]
    chars = []
    while num > 0:
        num, rem = divmod(num, BASE)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE NOT NULL,
                long_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                click_count INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        db.commit()


def is_valid_url(candidate: str) -> bool:
    """Reject obviously-invalid input before we store it."""
    try:
        result = urlparse(candidate)
        return all([result.scheme in ("http", "https"), result.netloc])
    except ValueError:
        return False


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.route("/")
def home():
    db = get_db()
    links = db.execute(
        "SELECT short_code, long_url, created_at, click_count "
        "FROM urls ORDER BY id DESC LIMIT 50"
    ).fetchall()
    return render_template("index.html", links=links, error=None, short_url=None)


@app.route("/shorten", methods=["POST"])
def shorten():
    long_url = request.form.get("long_url", "").strip()
    db = get_db()

    if not is_valid_url(long_url):
        links = db.execute(
            "SELECT short_code, long_url, created_at, click_count "
            "FROM urls ORDER BY id DESC LIMIT 50"
        ).fetchall()
        return render_template(
            "index.html",
            links=links,
            error="Please enter a valid URL starting with http:// or https://",
            short_url=None,
        )

    # If this exact URL was already shortened, reuse the existing code
    # instead of creating a duplicate row.
    existing = db.execute(
        "SELECT short_code FROM urls WHERE long_url = ?", (long_url,)
    ).fetchone()

    if existing:
        short_code = existing["short_code"]
    else:
        created_at = datetime.now(timezone.utc).isoformat()
        cursor = db.execute(
            "INSERT INTO urls (short_code, long_url, created_at) VALUES (?, ?, ?)",
            ("", long_url, created_at),
        )
        new_id = cursor.lastrowid
        short_code = encode_base62(new_id)
        db.execute(
            "UPDATE urls SET short_code = ? WHERE id = ?", (short_code, new_id)
        )
        db.commit()

    short_url = url_for("redirect_short_code", short_code=short_code, _external=True)

    links = db.execute(
        "SELECT short_code, long_url, created_at, click_count "
        "FROM urls ORDER BY id DESC LIMIT 50"
    ).fetchall()
    return render_template(
        "index.html", links=links, error=None, short_url=short_url
    )


@app.route("/<short_code>")
def redirect_short_code(short_code):
    db = get_db()
    row = db.execute(
        "SELECT long_url FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()

    if row is None:
        abort(404)

    db.execute(
        "UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?",
        (short_code,),
    )
    db.commit()
    return redirect(row["long_url"], code=302)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
