"""
URL Shortener
-------------
A Flask + SQLite URL shortener with:
  - Base62 short codes (counter-based, so no hash collisions)
  - Optional custom aliases
  - Optional link expiration
  - QR code generation per link
  - A per-link analytics page (clicks over time)

Run locally:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

import io
import re
import sqlite3
import string
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import qrcode
from flask import (
    Flask, abort, g, redirect, render_template, request, send_file, url_for,
)

app = Flask(__name__)
DATABASE = "urls.db"

# --------------------------------------------------------------------------
# Base62 encoding: 0-9, a-z, A-Z (62 symbols) turns a numeric ID into a
# short, guaranteed-unique code -- no hashing, so no collisions.
# --------------------------------------------------------------------------
ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE = len(ALPHABET)  # 62

# Custom aliases may only use these characters, and can't collide with a
# route name our app already uses.
ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
RESERVED_ALIASES = {"shorten", "static", "analytics", "qr"}

EXPIRY_CHOICES = {
    "never": None,
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


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
                expires_at TEXT,
                click_count INTEGER NOT NULL DEFAULT 0,
                is_custom INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER NOT NULL,
                clicked_at TEXT NOT NULL,
                FOREIGN KEY (url_id) REFERENCES urls(id)
            )
            """
        )
        db.commit()


def is_valid_url(candidate: str) -> bool:
    try:
        result = urlparse(candidate)
        return all([result.scheme in ("http", "https"), result.netloc])
    except ValueError:
        return False


def is_expired(row) -> bool:
    if row["expires_at"] is None:
        return False
    return datetime.now(timezone.utc) > datetime.fromisoformat(row["expires_at"])


def get_recent_links(db):
    return db.execute(
        "SELECT short_code, long_url, created_at, expires_at, click_count, is_custom "
        "FROM urls ORDER BY id DESC LIMIT 50"
    ).fetchall()


def render_home(db, error=None, short_url=None, short_code=None):
    return render_template(
        "index.html",
        links=get_recent_links(db),
        error=error,
        short_url=short_url,
        short_code=short_code,
    )


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.route("/")
def home():
    return render_home(get_db())


@app.route("/shorten", methods=["POST"])
def shorten():
    long_url = request.form.get("long_url", "").strip()
    custom_alias = request.form.get("custom_alias", "").strip()
    expiry_key = request.form.get("expires_in", "never")
    db = get_db()

    if not is_valid_url(long_url):
        return render_home(
            db, error="Please enter a valid URL starting with http:// or https://"
        )

    if custom_alias:
        if not ALIAS_RE.match(custom_alias):
            return render_home(
                db,
                error="Custom alias must be 3-20 characters: letters, "
                "numbers, hyphens, or underscores only.",
            )
        if custom_alias.lower() in RESERVED_ALIASES:
            return render_home(
                db, error=f'"{custom_alias}" is reserved, please choose another alias.'
            )
        taken = db.execute(
            "SELECT 1 FROM urls WHERE short_code = ?", (custom_alias,)
        ).fetchone()
        if taken:
            return render_home(
                db, error=f'The alias "{custom_alias}" is already taken.'
            )

    delta = EXPIRY_CHOICES.get(expiry_key)
    expires_at = (
        (datetime.now(timezone.utc) + delta).isoformat() if delta else None
    )
    created_at = datetime.now(timezone.utc).isoformat()

    if custom_alias:
        db.execute(
            "INSERT INTO urls (short_code, long_url, created_at, expires_at, is_custom) "
            "VALUES (?, ?, ?, ?, 1)",
            (custom_alias, long_url, created_at, expires_at),
        )
        short_code = custom_alias
    else:
        # Reuse an existing non-expired auto-generated code for the same URL.
        existing = db.execute(
            "SELECT short_code FROM urls WHERE long_url = ? AND is_custom = 0",
            (long_url,),
        ).fetchone()
        if existing:
            short_code = existing["short_code"]
        else:
            cursor = db.execute(
                "INSERT INTO urls (short_code, long_url, created_at, expires_at) "
                "VALUES (?, ?, ?, ?)",
                ("", long_url, created_at, expires_at),
            )
            new_id = cursor.lastrowid
            short_code = encode_base62(new_id)
            db.execute(
                "UPDATE urls SET short_code = ? WHERE id = ?", (short_code, new_id)
            )
    db.commit()

    short_url = url_for("redirect_short_code", short_code=short_code, _external=True)
    return render_home(db, short_url=short_url, short_code=short_code)


@app.route("/qr/<short_code>.png")
def qr_code(short_code):
    """Generate a QR code image on the fly for a given short link."""
    db = get_db()
    row = db.execute(
        "SELECT short_code FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    if row is None:
        abort(404)

    target_url = url_for("redirect_short_code", short_code=short_code, _external=True)
    img = qrcode.make(target_url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/delete/<short_code>", methods=["POST"])
def delete_link(short_code):
    """Delete a saved short link and its click history."""
    db = get_db()
    row = db.execute(
        "SELECT id FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()

    if row is None:
        abort(404)

    # Remove analytics rows first because SQLite foreign keys may not be enabled.
    db.execute("DELETE FROM clicks WHERE url_id = ?", (row["id"],))
    db.execute("DELETE FROM urls WHERE id = ?", (row["id"],))
    db.commit()
    return redirect(url_for("home"))


@app.route("/analytics/<short_code>")
def analytics(short_code):
    db = get_db()
    link = db.execute(
        "SELECT * FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    if link is None:
        abort(404)

    clicks_by_day = db.execute(
        """
        SELECT substr(clicked_at, 1, 10) AS day, COUNT(*) AS count
        FROM clicks WHERE url_id = ?
        GROUP BY day ORDER BY day
        """,
        (link["id"],),
    ).fetchall()

    return render_template(
        "analytics.html",
        link=link,
        expired=is_expired(link),
        chart_labels=[row["day"] for row in clicks_by_day],
        chart_values=[row["count"] for row in clicks_by_day],
    )


@app.route("/<short_code>")
def redirect_short_code(short_code):
    db = get_db()
    row = db.execute(
        "SELECT * FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()

    if row is None:
        abort(404)

    if is_expired(row):
        return render_template("expired.html", short_code=short_code), 410

    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?",
        (short_code,),
    )
    db.execute(
        "INSERT INTO clicks (url_id, clicked_at) VALUES (?, ?)", (row["id"], now)
    )
    db.commit()
    return redirect(row["long_url"], code=302)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)