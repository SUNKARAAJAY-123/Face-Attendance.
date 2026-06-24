"""
app.py - Flask Web Dashboard
Run:  python app.py
      FLASK_DEBUG=true python app.py   ← enable debug mode via env var only

Endpoints:
  GET /                  → HTML dashboard
  GET /api/attendance    → JSON list of all records
  GET /api/persons       → JSON list of registered persons
  GET /health            → health check
"""

import time
from flask import Flask, render_template, jsonify

from config        import FLASK_DEBUG, FLASK_PORT, CACHE_TTL_SEC
from data_manager  import load_all_attendance, list_persons
from logger_setup  import get_logger

logger = get_logger("app")
app    = Flask(__name__)

# ── Simple in-memory cache (fixes: full CSV reload on every request) ───────────
_cache: dict = {"records": [], "ts": 0.0}


def get_cached_records() -> list:
    if time.time() - _cache["ts"] > CACHE_TTL_SEC:
        _cache["records"] = load_all_attendance()
        _cache["ts"]      = time.time()
        logger.debug(f"Cache refreshed — {len(_cache['records'])} records loaded.")
    return _cache["records"]


def get_summary(records: list) -> tuple[dict, dict]:
    per_person: dict[str, int] = {}
    per_date:   dict[str, int] = {}
    for r in records:
        name = r.get("NAME", "").strip()
        date = r.get("DATE", "").strip()
        if name:
            per_person[name] = per_person.get(name, 0) + 1
        if date:
            per_date[date]   = per_date.get(date, 0) + 1
    return per_person, per_date


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    from datetime import datetime
    records              = get_cached_records()
    per_person, per_date = get_summary(records)
    today                = datetime.now().strftime("%d-%m-%Y")
    today_count          = per_date.get(today, 0)
    return render_template(
        "index.html",
        records     = records,
        per_person  = per_person,
        per_date    = per_date,
        today       = today,
        today_count = today_count,
        total       = len(records),
        persons     = list_persons(),
    )


@app.route("/api/attendance")
def api_attendance():
    """JSON endpoint — all attendance records."""
    return jsonify(get_cached_records())


@app.route("/api/persons")
def api_persons():
    """JSON endpoint — registered persons."""
    return jsonify(list_persons())


@app.route("/health")
def health():
    """Health check for monitoring / uptime tools."""
    return jsonify({"status": "ok", "records": len(get_cached_records())})


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"Starting Flask on port {FLASK_PORT} | debug={FLASK_DEBUG}")
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT, use_reloader=False)
