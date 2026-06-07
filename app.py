"""
app.py - Flask Web Dashboard for Attendance System
Run:  python app.py
Open: http://127.0.0.1:5000
"""

from flask import Flask, render_template, jsonify
import os
import csv
import glob
from datetime import datetime

app = Flask(__name__)

ATTENDANCE_DIR = "Attendance"


def load_all_attendance():
    """Read all CSV files in the Attendance folder and return a unified list."""
    records = []
    pattern = os.path.join(ATTENDANCE_DIR, "Attendance_*.csv")
    for filepath in sorted(glob.glob(pattern), reverse=True):
        with open(filepath, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    return records


def get_summary(records):
    """Return per-person and per-date summary stats."""
    per_person = {}
    per_date = {}

    for r in records:
        name = r.get("NAME", "Unknown")
        date = r.get("DATE", "Unknown")

        per_person[name] = per_person.get(name, 0) + 1
        per_date[date] = per_date.get(date, 0) + 1

    return per_person, per_date


@app.route("/")
def index():
    records = load_all_attendance()
    per_person, per_date = get_summary(records)
    today = datetime.now().strftime("%d-%m-%Y")
    today_count = per_date.get(today, 0)
    return render_template(
        "index.html",
        records=records,
        per_person=per_person,
        per_date=per_date,
        today=today,
        today_count=today_count,
        total=len(records),
    )


@app.route("/api/attendance")
def api_attendance():
    """JSON endpoint — useful for future integrations."""
    return jsonify(load_all_attendance())


if __name__ == "__main__":
    app.run(debug=True)
