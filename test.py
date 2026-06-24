"""
test.py - Real-time Face Recognition with Auto-Attendance Marking

Feature 1: Auto-mark after 3 consecutive seconds of stable recognition
Feature 6: Unknown face → save photo + notification
Feature 8: Late detection based on CLASS_START_TIME

Keys:  O = manual mark   Q = quit
"""

import cv2
import sys
import time
import os
from datetime import datetime

from config       import (IMG_SIZE, ATTENDANCE_DIR, AUTO_MARK_SECONDS,
                           AUTO_MARK_ENABLED, CLASS_START_TIME,
                           LATE_AFTER_MINUTES, UNKNOWN_DIR)
from preprocessor import normalize_face, largest_face
from recognizer   import FaceRecognizer
from data_manager import load_data, write_attendance, load_today_attendance
from logger_setup import get_logger

logger = get_logger("test.py")

# ── Load data & train ──────────────────────────────────────────────────────────
try:
    FACES, LABELS = load_data()
except FileNotFoundError as e:
    logger.error(str(e))
    sys.exit(1)

recognizer = FaceRecognizer()
recognizer.train(FACES, LABELS)

# ── Webcam setup ───────────────────────────────────────────────────────────────
video = cv2.VideoCapture(0)
if not video.isOpened():
    logger.error("Cannot access webcam.")
    sys.exit(1)

facedetect = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

os.makedirs(ATTENDANCE_DIR, exist_ok=True)
os.makedirs(UNKNOWN_DIR,    exist_ok=True)

today_str           = datetime.now().strftime("%d-%m-%Y")
attendance_recorded = load_today_attendance(today_str)
if attendance_recorded:
    logger.info(f"Already marked today: {attendance_recorded}")

# ── Feature 1: Auto-mark tracker ──────────────────────────────────────────────
# Tracks how long each name has been continuously recognised
recognition_start: dict[str, float] = {}   # name → first seen timestamp
last_seen_name   : str = ""
success_flash    : dict[str, float] = {}   # name → timestamp for flash msg


def get_status(time_str: str) -> str:
    """Feature 8: determine Present / Late based on class start time."""
    try:
        from datetime import datetime as dt
        t_arrival = dt.strptime(time_str, "%H:%M:%S").time()
        h, m      = map(int, CLASS_START_TIME.split(":"))
        t_class   = dt.strptime(
            f"{h:02d}:{m + LATE_AFTER_MINUTES:02d}:00", "%H:%M:%S"
        ).time()
        return "Late" if t_arrival > t_class else "Present"
    except Exception:
        return "Present"


def mark(name: str, frame) -> None:
    """Write attendance and reset tracker."""
    ts       = time.time()
    date_str = datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
    time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    day_str  = datetime.fromtimestamp(ts).strftime("%A")
    status   = get_status(time_str)

    try:
        write_attendance(name, time_str, day_str, date_str, status=status)
        attendance_recorded.add(name)
        success_flash[name] = time.time()
        logger.info(f"[✓] AUTO-MARKED — {name} | {time_str} | {status}")
    except Exception as e:
        logger.error(f"Write failed for {name}: {e}")

    recognition_start.pop(name, None)


def save_unknown(frame, x, y, w, h) -> None:
    """Feature 6: save unknown face photo."""
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(UNKNOWN_DIR, f"unknown_{ts}.jpg")
    cv2.imwrite(path, frame[y:y+h, x:x+w])
    logger.warning(f"Unknown face saved → {path}")

    # Notify DB
    try:
        from database import get_db
        conn = get_db()
        conn.execute("""INSERT INTO notifications(type, message)
                        VALUES(?,?)""",
                     ("unknown_face",
                      f"⚠ Unknown face detected at {datetime.now().strftime('%H:%M:%S')} — photo saved."))
        conn.commit()
        conn.close()
    except Exception:
        pass


_last_unknown_save = 0.0   # throttle: save at most once per 10s

logger.info("Auto-mark enabled — stable recognition for "
            f"{AUTO_MARK_SECONDS}s triggers attendance.")
logger.info("Press 'O' for manual mark | 'Q' to quit")

# ── Main loop ──────────────────────────────────────────────────────────────────
while True:
    ret, frame = video.read()
    if not ret:
        logger.error("Webcam read failed.")
        break

    gray      = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    raw_faces = facedetect.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    now       = time.time()
    detected  = []

    for (x, y, w, h) in raw_faces:
        crop = frame[y:y+h, x:x+w]
        try:
            vec = normalize_face(crop, IMG_SIZE)
        except ValueError:
            continue

        name, conf = recognizer.predict(vec)

        # ── Feature 6: unknown face alert (throttled) ──────────────────
        if name == "Unknown":
            if now - _last_unknown_save > 10:
                save_unknown(frame, x, y, w, h)
                _last_unknown_save = now

        detected.append((name, conf, x, y, w, h))

        # ── Feature 1: auto-mark tracker ───────────────────────────────
        if AUTO_MARK_ENABLED and name != "Unknown":
            if name not in attendance_recorded:
                if name not in recognition_start:
                    recognition_start[name] = now
                elapsed = now - recognition_start[name]

                # Progress bar width (0–100)
                prog = min(int(elapsed / AUTO_MARK_SECONDS * 100), 100)
                bar_w = int((w) * prog / 100)

                # Draw progress bar under face box
                cv2.rectangle(frame, (x, y+h+4), (x+w, y+h+10),
                              (50,50,50), -1)
                cv2.rectangle(frame, (x, y+h+4), (x+bar_w, y+h+10),
                              (0,200,80), -1)

                if elapsed >= AUTO_MARK_SECONDS:
                    mark(name, frame)
            else:
                recognition_start.pop(name, None)

        # Draw bounding box
        is_known   = name != "Unknown"
        box_color  = (0,180,0)   if is_known else (120,120,120)
        label_bg   = (0,140,0)   if is_known else (80,80,80)

        # Flash green on success
        if name in success_flash and now - success_flash[name] < 2:
            box_color = (0,255,100)
            label_bg  = (0,200,80)

        label = f"{name}  {conf:.0f}%" if is_known else "Unknown"
        cv2.rectangle(frame, (x,y), (x+w,y+h), box_color, 2)
        cv2.rectangle(frame, (x,y-38), (x+w,y), label_bg, -1)
        cv2.putText(frame, label, (x+5, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255,255,255), 2)

        # Success flash message
        if name in success_flash and now - success_flash[name] < 2:
            cv2.putText(frame, "MARKED!", (x, y+h+28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,100), 2)

    # HUD
    known = sum(1 for d in detected if d[0] != "Unknown")
    t_str = datetime.now().strftime("%H:%M:%S")
    hud   = f"Faces:{len(detected)} Known:{known} | O=Mark Q=Quit | {t_str}"
    cv2.putText(frame, hud, (10,28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,220,0), 2)

    # Auto-mark countdown HUD
    for name, start in list(recognition_start.items()):
        if name not in attendance_recorded:
            rem = max(0, AUTO_MARK_SECONDS - (now - start))
            cv2.putText(frame, f"Auto-marking {name} in {rem:.1f}s",
                        (10, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,200,255), 2)

    cv2.imshow("Attendance System — Auto Mark", frame)
    key = cv2.waitKey(1) & 0xFF

    # Manual mark
    if key in (ord("o"), ord("O")):
        for (name, conf, *_) in detected:
            if name == "Unknown":
                logger.info("Unknown — skipping.")
            elif name in attendance_recorded:
                logger.info(f"{name} already marked.")
            else:
                mark(name, frame)

    if key in (ord("q"), ord("Q")):
        break

video.release()
cv2.destroyAllWindows()
logger.info("Session ended.")
