"""
config.py - Single source of truth for all constants.
"""
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR        = "data"
ATTENDANCE_DIR  = "Attendance"
BACKUP_DIR      = "backups"
UNKNOWN_DIR     = "unknown_faces"
LOG_FILE        = "app.log"

# ── Face Capture ───────────────────────────────────────────────────────────────
IMG_SIZE        = (50, 50)
MAX_SAMPLES     = 100
SAMPLE_EVERY    = 10

# ── KNN Model ─────────────────────────────────────────────────────────────────
KNN_NEIGHBORS   = 5
THRESHOLD_MULT  = 2.0

# ── Flask ──────────────────────────────────────────────────────────────────────
FLASK_DEBUG     = os.getenv("FLASK_DEBUG", "false").lower() == "true"
FLASK_PORT      = int(os.getenv("FLASK_PORT", 5000))
CACHE_TTL_SEC   = 30

# ── Storage ────────────────────────────────────────────────────────────────────
FACES_FILE      = os.path.join(DATA_DIR, "faces_data.npy")
NAMES_FILE      = os.path.join(DATA_DIR, "names.json")

# ── Auto-mark attendance ───────────────────────────────────────────────────────
AUTO_MARK_SECONDS   = 3       # seconds face must be stable before auto-mark
AUTO_MARK_ENABLED   = True

# ── Class timing (late detection) ─────────────────────────────────────────────
CLASS_START_TIME    = "09:00"  # HH:MM  — on time threshold
LATE_AFTER_MINUTES  = 15       # mark Late if arrival > CLASS_START_TIME + this

# ── Attendance threshold ───────────────────────────────────────────────────────
LOW_ATTENDANCE_PCT  = 75.0

# ── Email (configure via env vars for security) ───────────────────────────────
EMAIL_ENABLED       = os.getenv("EMAIL_ENABLED",  "false").lower() == "true"
EMAIL_HOST          = os.getenv("EMAIL_HOST",     "smtp.gmail.com")
EMAIL_PORT          = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER          = os.getenv("EMAIL_USER",     "")
EMAIL_PASS          = os.getenv("EMAIL_PASS",     "")
EMAIL_ADMIN         = os.getenv("EMAIL_ADMIN",    "")

# ── Scheduler times ───────────────────────────────────────────────────────────
DEFAULTER_CHECK_TIME    = "18:00"   # 6 PM daily defaulter check
DAILY_REPORT_TIME       = "19:00"   # 7 PM email report
BACKUP_TIME             = "23:00"   # 11 PM nightly backup
MONTHLY_REPORT_DAY      = 1         # 1st of every month
