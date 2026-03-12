# Face Recognition Attendance System
A simple, automated attendance tracking system using computer vision and machine learning to recognize faces and log attendance in real-time.

# Features
Face Data Collection: Capture and store face samples for training the recognition model
Real-time Recognition: Detect and identify faces from webcam feed using KNN classifier
Attendance Logging: Record attendance with timestamps to CSV files
Duplicate Prevention: Avoid logging the same person multiple times in a session
User-friendly Interface: Visual feedback with bounding boxes and predicted names
# Technologies Used
Python: Core programming language
OpenCV: Computer vision library for face detection and image processing
scikit-learn: Machine learning library for KNN classification
NumPy: Numerical computing for data manipulation
Pickle: Data serialization for storing face data and labels
CSV: Data logging for attendance records
# Installation
Clone the repository:
git clone <repository-url>
cd attendance-system
Create a virtual environment:
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On macOS/Linux
Install dependencies:
pip install opencv-python scikit-learn numpy

## Usage
Step 1: Collect Face Data
Run the data collection script to train the system with face samples:
python face.py
Enter your name when prompted
Position your face in front of the webcam
The system will capture 100 face samples automatically
Press 'q' to stop or wait for collection to complete

Step 2: Run Attendance System
Start the real-time recognition and attendance logging:
python test.py
The webcam feed will open showing detected faces with names
Press 'o' to record attendance for detected faces
Attendance is saved to Attendance/Attendance_<date>.csv
Press 'q' to exit
How It Works
Data Collection:

Captures face images from webcam
Converts images to numerical arrays (50x50 pixels flattened)
Stores face data and corresponding names using pickle
Model Training:

Uses K-Nearest Neighbors algorithm to learn face patterns
Trained on collected face data with associated names
Real-time Recognition:

Detects faces in video frames using Haar cascades
Compares detected faces with trained model
Displays predicted names on screen
Attendance Logging:

Records unique attendance entries with timestamp and day
Prevents duplicates within the same session
Saves to date-specific CSV files
# Project Structure:-
attendance-system/
├── face.py              # Face data collection script
├── test.py              # Main attendance recognition script
├── Ajay py/             # Directory for stored face data
│   ├── names.pkl        # Pickled list of names
│   └── faces_data.pkl   # Pickled face data arrays
├── Attendance/          # Directory for attendance CSV files
│   └── Attendance_12-03-2026.csv  # Example attendance file
├── .venv/               # Virtual environment (not in repo)
└── README.md            # This file

