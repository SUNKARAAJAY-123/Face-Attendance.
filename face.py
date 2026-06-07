"""
face.py - Face Data Collection Script
Captures face samples from webcam and stores them for training the KNN model.
"""

import cv2
import pickle
import numpy as np
import os

# ── Constants ──────────────────────────────────────────────────────────────────
DATA_DIR = "data"
MAX_SAMPLES = 100
SAMPLE_INTERVAL = 10          # capture every 10th frame
IMG_SIZE = (50, 50)

# ── Setup ──────────────────────────────────────────────────────────────────────
video = cv2.VideoCapture(0)
facedetect = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

name = input("Enter Your Name: ").strip()
if not name:
    print("Name cannot be empty.")
    video.release()
    exit()

faces_data = []
frame_count = 0

print(f"[INFO] Capturing {MAX_SAMPLES} samples for '{name}'. Press 'q' to stop early.")

# ── Capture Loop ───────────────────────────────────────────────────────────────
while True:
    ret, frame = video.read()
    if not ret:
        print("[ERROR] Failed to read from webcam.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        crop = frame[y:y + h, x:x + w]
        resized = cv2.resize(crop, IMG_SIZE).flatten()

        if len(faces_data) < MAX_SAMPLES and frame_count % SAMPLE_INTERVAL == 0:
            faces_data.append(resized)

        # Visual feedback
        cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 2)
        cv2.putText(
            frame,
            f"Samples: {len(faces_data)}/{MAX_SAMPLES}",
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (50, 255, 50),
            2,
        )

    frame_count += 1
    cv2.imshow("Face Data Collection - Press Q to quit", frame)

    if cv2.waitKey(1) == ord("q") or len(faces_data) >= MAX_SAMPLES:
        break

video.release()
cv2.destroyAllWindows()

# ── Save Data ──────────────────────────────────────────────────────────────────
if len(faces_data) == 0:
    print("[WARNING] No face data captured. Exiting without saving.")
    exit()

faces_data = np.array(faces_data)
actual_samples = len(faces_data)
print(f"[INFO] Captured {actual_samples} samples.")

os.makedirs(DATA_DIR, exist_ok=True)

names_path = os.path.join(DATA_DIR, "names.pkl")
faces_path = os.path.join(DATA_DIR, "faces_data.pkl")

# Append or create names
if os.path.exists(names_path):
    with open(names_path, "rb") as f:
        names = pickle.load(f)
    names += [name] * actual_samples
else:
    names = [name] * actual_samples

with open(names_path, "wb") as f:
    pickle.dump(names, f)

# Append or create faces
if os.path.exists(faces_path):
    with open(faces_path, "rb") as f:
        existing_faces = pickle.load(f)
    faces_data = np.append(existing_faces, faces_data, axis=0)

with open(faces_path, "wb") as f:
    pickle.dump(faces_data, f)

print(f"[INFO] Data saved to '{DATA_DIR}/'. Total entries: {len(names)}")
