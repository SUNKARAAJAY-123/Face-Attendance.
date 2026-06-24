"""
test.py - Real-time Face Recognition & Attendance Logging
Run:  python test.py

Keys:
  O  →  Mark attendance for all recognised faces in current frame
  Q  →  Quit
"""

import cv2
import sys
import time
from datetime import datetime

from config       import IMG_SIZE, ATTENDANCE_DIR
from preprocessor import normalize_face, largest_face
from recognizer   import FaceRecognizer
from data_manager import load_data, write_attendance, load_today_attendance
from logger_setup import get_logger

logger = get_logger("test.py")


# ── Load data & train model ────────────────────────────────────────────────────
try:
    FACES, LABELS = load_data()
except FileNotFoundError as e:
    logger.error(str(e))
    sys.exit(1)

recognizer = FaceRecognizer()
recognizer.train(FACES, LABELS)


# ── Webcam & detector setup ────────────────────────────────────────────────────
video = cv2.VideoCapture(0)
if not video.isOpened():
    logger.error("Cannot access webcam. Check connection.")
    sys.exit(1)

facedetect = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Load already-marked names from today's CSV (prevents double-marking on restart)
today_str           = datetime.now().strftime("%d-%m-%Y")
attendance_recorded = load_today_attendance(today_str)
if attendance_recorded:
    logger.info(f"Already marked today: {attendance_recorded}")

logger.info("Press 'O' to mark attendance | Press 'Q' to quit")


# ── Main loop ──────────────────────────────────────────────────────────────────
while True:
    ret, frame = video.read()
    if not ret:
        logger.error("Failed to capture frame from webcam.")
        break

    gray      = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    raw_faces = facedetect.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    detected = []   # list of (name, confidence, x, y, w, h)

    for (x, y, w, h) in raw_faces:      # all faces shown; largest_face used in face.py only
        crop = frame[y:y + h, x:x + w]

        try:
            vector = normalize_face(crop, IMG_SIZE)
        except ValueError:
            continue

        name, confidence = recognizer.predict(vector)
        detected.append((name, confidence, x, y, w, h))

        # Colour: blue=known, grey=unknown
        is_known   = name != "Unknown"
        box_color  = (200, 50, 0)  if is_known else (120, 120, 120)
        label_bg   = (180, 30, 0)  if is_known else (80, 80, 80)
        label      = f"{name}  {confidence:.0f}%" if is_known else "Unknown"

        cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
        cv2.rectangle(frame, (x, y - 40), (x + w, y), label_bg, -1)
        cv2.putText(frame, label, (x + 5, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

    # HUD
    known_count = sum(1 for d in detected if d[0] != "Unknown")
    hud = (f"Faces: {len(detected)}  Known: {known_count}  "
           f"|  O = Mark  Q = Quit  |  {datetime.now().strftime('%H:%M:%S')}")
    cv2.putText(frame, hud, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 0), 2)

    cv2.imshow("Attendance System", frame)
    key = cv2.waitKey(1) & 0xFF

    # ── Mark attendance ────────────────────────────────────────────────────────
    if key in (ord("o"), ord("O")):
        if not detected:
            logger.info("No faces in frame — nothing to mark.")
        else:
            ts       = time.time()
            date_str = datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
            time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            day_str  = datetime.fromtimestamp(ts).strftime("%A")

            for (name, confidence, *_) in detected:
                if name == "Unknown":
                    logger.info("Unknown face — skipping.")
                elif name in attendance_recorded:
                    logger.info(f"{name} already marked today — skipping.")
                else:
                    try:
                        write_attendance(name, time_str, day_str, date_str)
                        attendance_recorded.add(name)
                        logger.info(f"Marked — {name} | {time_str} | conf={confidence:.1f}%")
                    except Exception as e:
                        logger.error(f"Could not write attendance for {name}: {e}")

    if key in (ord("q"), ord("Q")):
        break

video.release()
cv2.destroyAllWindows()
logger.info("Session ended.")
