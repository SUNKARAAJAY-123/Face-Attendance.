"""
models.py - Flask-Login User model + helper queries.
"""
from flask_login import UserMixin
from database import get_db


class User(UserMixin):
    def __init__(self, id, username, role, full_name, email, is_active=True):
        self.id        = id
        self.username  = username
        self.role      = role
        self.full_name = full_name
        self.email     = email
        self._active   = bool(is_active)

    @property
    def is_active(self):
        return self._active

    @staticmethod
    def get(user_id):
        conn = get_db()
        row  = conn.execute(
            "SELECT * FROM users WHERE id=?", (user_id,)
        ).fetchone()
        conn.close()
        if row:
            return User(row["id"], row["username"], row["role"],
                        row["full_name"], row["email"], row["is_active"])
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db()
        row  = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        conn.close()
        if row:
            return User(row["id"], row["username"], row["role"],
                        row["full_name"], row["email"], row["is_active"])
        return None

    def is_admin(self):
        return self.role == "admin"


# ── Student helpers ────────────────────────────────────────────────────────────

def get_all_students():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM students WHERE is_active=1 ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student(student_id):
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM students WHERE id=?", (student_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_student_by_name(name):
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM students WHERE name=? AND is_active=1", (name,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Attendance helpers ─────────────────────────────────────────────────────────

def get_attendance_stats():
    """Return aggregate stats used by the dashboard overview cards."""
    conn  = get_db()
    total = conn.execute("SELECT COUNT(*) FROM students WHERE is_active=1").fetchone()[0]

    from datetime import datetime
    today = datetime.now().strftime("%d-%m-%Y")

    present_today = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=? AND status='Present'",
        (today,)
    ).fetchone()[0]

    absent_today  = total - present_today
    total_records = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]

    # Per-student attendance %
    rows = conn.execute("""
        SELECT s.id, s.name,
               COUNT(a.id) as present_days
        FROM students s
        LEFT JOIN attendance a ON s.id=a.student_id AND a.status='Present'
        WHERE s.is_active=1
        GROUP BY s.id
    """).fetchall()

    # Count distinct dates recorded
    total_days_row = conn.execute(
        "SELECT COUNT(DISTINCT date) FROM attendance"
    ).fetchone()
    total_days = total_days_row[0] if total_days_row[0] > 0 else 1

    students_pct = []
    for r in rows:
        pct = round(r["present_days"] / total_days * 100, 1)
        students_pct.append({
            "id":       r["id"],
            "name":     r["name"],
            "present":  r["present_days"],
            "total":    total_days,
            "pct":      pct,
        })

    below_75   = [s for s in students_pct if s["pct"] < 75]
    top_10     = sorted(students_pct, key=lambda x: x["pct"], reverse=True)[:10]
    avg_pct    = round(sum(s["pct"] for s in students_pct) / len(students_pct), 1) \
                 if students_pct else 0

    conn.close()
    return {
        "total_students":  total,
        "present_today":   present_today,
        "absent_today":    absent_today,
        "avg_attendance":  avg_pct,
        "below_75":        below_75,
        "top_10":          top_10,
        "total_records":   total_records,
        "today":           today,
    }


def get_student_profile(student_id):
    conn = get_db()
    student = get_student(student_id)
    if not student:
        conn.close()
        return None

    rows = conn.execute("""
        SELECT date, time_in, day_name, status, confidence
        FROM attendance
        WHERE student_id=?
        ORDER BY date DESC
    """, (student_id,)).fetchall()

    history = [dict(r) for r in rows]
    present = sum(1 for h in history if h["status"] == "Present")
    total   = max(len(set(h["date"] for h in history)), 1)
    pct     = round(present / total * 100, 1)

    # Monthly breakdown
    monthly: dict = {}
    for h in history:
        try:
            parts = h["date"].split("-")
            key   = f"{parts[1]}-{parts[2]}"   # MM-YYYY
        except Exception:
            key = "Unknown"
        monthly.setdefault(key, {"present": 0, "absent": 0})
        if h["status"] == "Present":
            monthly[key]["present"] += 1
        else:
            monthly[key]["absent"]  += 1

    conn.close()
    return {
        "student":  student,
        "history":  history,
        "present":  present,
        "total":    total,
        "pct":      pct,
        "monthly":  monthly,
    }


def get_daily_trend(days=30):
    conn = get_db()
    rows = conn.execute("""
        SELECT date, COUNT(*) as cnt
        FROM attendance WHERE status='Present'
        GROUP BY date ORDER BY date DESC LIMIT ?
    """, (days,)).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def get_unread_notifications():
    conn = get_db()
    rows = conn.execute("""
        SELECT n.*, s.name as student_name
        FROM notifications n
        LEFT JOIN students s ON n.student_id=s.id
        WHERE n.is_read=0
        ORDER BY n.created_at DESC
        LIMIT 20
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_notifications_read():
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read=1")
    conn.commit()
    conn.close()


def generate_alerts():
    """Auto-generate notifications for low-attendance and absent streaks."""
    stats = get_attendance_stats()
    conn  = get_db()

    for s in stats["below_75"]:
        existing = conn.execute("""
            SELECT 1 FROM notifications
            WHERE student_id=? AND type='low_attendance'
            AND date(created_at)=date('now','localtime')
        """, (s["id"],)).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO notifications(type, message, student_id)
                VALUES(?,?,?)
            """, ("low_attendance",
                  f"⚠ {s['name']} has only {s['pct']}% attendance (below 75%)",
                  s["id"]))

    conn.commit()
    conn.close()
