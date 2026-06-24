"""
face.py - Face Data Collection Script
Run:  python face.py
      python face.py --delete "Name"   ← remove a person
      python face.py --list            ← show registered persons
"""

import cv2
import numpy as np
import sys
import os

from config        import MAX_SAMPLES, SAMPLE_EVERY, IMG_SIZE
from preprocessor  import normalize_face, largest_face
from data_manager  import append_data, delete_person, list_persons
from logger_setup  import get_logger

logger = get_logger("face.py")


# ── CLI helpers ────────────────────────────────────────────────────────────────
def cmd_list():
    persons = list_persons()
    if persons:
        print("\nRegistered persons:")
        for p in persons:
            print(f"  • {p}")
    else:
        print("No persons registered yet.")
    sys.exit(0)


def cmd_delete(name: str):
    if delete_person(name):
        print(f"'{name}' removed successfully.")
    else:
        print(f"'{name}' not found.")
    sys.exit(0)


# ── Parse CLI args ─────────────────────────────────────────────────────────────
args = sys.argv[1:]
if "--list" in args:
    cmd_list()
if "--delete" in args:
    idx = args.index("--delete")
    if idx + 1 >= len(args):
        print("Usage: python face.py --delete \"Name\"")
        sys.exit(1)
    cmd_delete(args[idx + 1])


# ── Ask for name BEFORE opening webcam (fix: don't waste camera resource) ──────
name = input("Enter Your Name: ").strip()
if not name:
    logger.error("Name cannot be empty.")
    sys.exit(1)


# ── Open webcam ────────────────────────────────────────────────────────────────
video = cv2.VideoCapture(0)
if not video.isOpened():
    logger.error("Cannot access webcam. Check if it is connected.")
    sys.exit(1)

facedetect = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

faces_data   = []
face_counter = 0
logger.info(f"Capturing {MAX_SAMPLES} samples for '{name}'. Press Q to stop early.")


# ── Capture loop ───────────────────────────────────────────────────────────────
while True:
    ret, frame = video.read()
    if not ret:
        logger.error("Failed to read from webcam.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    raw_faces = facedetect.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    # FIX: only process the LARGEST face — prevents multi-face contamination
    for (x, y, w, h) in largest_face(raw_faces):
        crop = frame[y:y + h, x:x + w]

        try:
            vector = normalize_face(crop, IMG_SIZE)
        except ValueError as e:
            logger.warning(f"Skipping bad crop: {e}")
            continue

        face_counter += 1
        if len(faces_data) < MAX_SAMPLES and face_counter % SAMPLE_EVERY == 0:
            faces_data.append(vector)

        # Visual feedback
        cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 2)
        cv2.putText(
            frame,
            f"Samples: {len(faces_data)}/{MAX_SAMPLES}  —  {name}",
            (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 255, 50), 2,
        )

    cv2.imshow("Face Collection  [Q = quit early]", frame)

    if cv2.waitKey(1) & 0xFF == ord("q") or len(faces_data) >= MAX_SAMPLES:
        break

video.release()
cv2.destroyAllWindows()


# ── Validate & save ────────────────────────────────────────────────────────────
if len(faces_data) == 0:
    logger.warning("No face data captured — nothing saved.")
    sys.exit(1)

faces_array = np.array(faces_data, dtype=np.float32)
logger.info(f"Captured {len(faces_array)} samples for '{name}'.")

append_data(faces_array, name)
logger.info("Done. Run 'python test.py' to start recognition.")
