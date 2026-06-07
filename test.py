"""
test.py - Real-time Face Recognition & Attendance Logging
Recognizes faces via KNN and logs attendance to a date-stamped CSV on keypress.
"""

import cv2
import pickle
import numpy as np
import os
import csv
import time
from datetime import datetime
from sklearn.neighbors import KNeighborsClassifier

# ── Constants ──────────────────────────────────────────────────────────────────
DATA_DIR = "data"
ATTENDANCE_DIR = "Attendance"
IMG_SIZE = (50, 50)
COL_NAMES = ["NAME", "TIME", "DAY", "DATE"]

# ── Load Trained Data ──────────────────────────────────────────────────────────
names_path = os.path.join(DATA_DIR, "names.pkl")
faces_path = os.path.join(DATA_DIR, "faces_data.pkl")

if not os.path.exists(names_path) or not os.path.exists(faces_path):
    print("[ERROR] No training data found. Run face.py first to collect face data.")
    exit()

with open(names_path, "rb") as f:
    LABELS = pickle.load(f)
with open(faces_path, "rb") as f:
    FACES = pickle.load(f)

print(f"[INFO] Loaded {len(FACES)} face samples for {len(set(LABELS))} person(s): {set(LABELS)}")

# Fix any length mismatch
if len(LABELS) != len(FACES):
    min_len = min(len(LABELS), len(FACES))
    LABELS = LABELS[:min_len]
    FACES = FACES[:min_len]
    print(f"[WARNING] Trimmed data to {min_len} samples to fix length mismatch.")

# ── Train KNN Classifier ───────────────────────────────────────────────────────
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)
print("[INFO] KNN model trained successfully.")

# ── Video & Detector Setup ─────────────────────────────────────────────────────
video = cv2.VideoCapture(0)
facedetect = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

os.makedirs(ATTENDANCE_DIR, exist_ok=True)

# Track who was already marked in this session
attendance_recorded = set()

print("[INFO] Press 'O' to mark attendance | Press 'Q' to quit")

# ── Main Loop ──────────────────────────────────────────────────────────────────
while True:
    ret, frame = video.read()
    if not ret:
        print("[ERROR] Failed to capture frame.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    detected = []   # [(name, x, y, w, h), ...]

    for (x, y, w, h) in faces:
        crop = frame[y:y + h, x:x + w]
        resized = cv2.resize(crop, IMG_SIZE).flatten().reshape(1, -1)
        predicted_name = knn.predict(resized)[0]
        detected.append((predicted_name, x, y, w, h))

        # Draw bounding box + label
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.rectangle(frame, (x, y - 40), (x + w, y), (50, 50, 255), -1)
        cv2.putText(
            frame,
            predicted_name,
            (x + 5, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

    # HUD
    status = f"Detected: {len(detected)} face(s) | O=Mark  Q=Quit"
    cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Attendance System - Face Recognition", frame)
    key = cv2.waitKey(1) & 0xFF

    # ── Mark Attendance ────────────────────────────────────────────────────────
    if key == ord("o"):
        if not detected:
            print("[INFO] No faces detected to mark.")
        else:
            ts = time.time()
            date_str = datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
            time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            day_str = datetime.fromtimestamp(ts).strftime("%A")
            filename = os.path.join(ATTENDANCE_DIR, f"Attendance_{date_str}.csv")
            file_exists = os.path.isfile(filename)

            with open(filename, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                if not file_exists:
                    writer.writerow(COL_NAMES)

                for (name, *_) in detected:
                    if name not in attendance_recorded:
                        attendance_recorded.add(name)
                        writer.writerow([name, time_str, day_str, date_str])
                        print(f"[✓] Attendance marked — {name} at {time_str}")
                    else:
                        print(f"[SKIP] {name} already marked this session.")

    if key == ord("q"):
        break

video.release()
cv2.destroyAllWindows()
print("[INFO] Session ended.")
