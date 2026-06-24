"""
config.py - Single source of truth for all constants.
"""
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR        = "data"
ATTENDANCE_DIR  = "Attendance"
LOG_FILE        = "app.log"

# ── Face Capture ───────────────────────────────────────────────────────────────
IMG_SIZE        = (50, 50)
MAX_SAMPLES     = 100
SAMPLE_EVERY    = 10          # capture 1 sample every N detected-face frames

# ── KNN Model ─────────────────────────────────────────────────────────────────
KNN_NEIGHBORS   = 5
THRESHOLD_MULT  = 2.0         # dynamic threshold = max_intra_dist × this

# ── Flask ──────────────────────────────────────────────────────────────────────
FLASK_DEBUG     = os.getenv("FLASK_DEBUG", "false").lower() == "true"
FLASK_PORT      = int(os.getenv("FLASK_PORT", 5000))
CACHE_TTL_SEC   = 30          # dashboard cache refresh interval

# ── Storage (safe formats — no pickle) ────────────────────────────────────────
FACES_FILE      = os.path.join(DATA_DIR, "faces_data.npy")
NAMES_FILE      = os.path.join(DATA_DIR, "names.json")
