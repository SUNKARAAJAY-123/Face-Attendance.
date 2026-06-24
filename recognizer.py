"""
recognizer.py - KNN face recognition with dynamic confidence threshold.
Separated from video/IO logic for testability.
"""
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from logger_setup import get_logger
from config import KNN_NEIGHBORS, THRESHOLD_MULT

logger = get_logger("recognizer")


class FaceRecognizer:
    """
    Wraps KNN classifier with:
      - dynamic threshold (no hardcoded magic number)
      - confidence score (0–100%)
      - unknown face detection
    """

    def __init__(self):
        self.knn        = None
        self.threshold  = None
        self._trained   = False

    def train(self, faces: np.ndarray, labels: list) -> None:
        """
        Train KNN on face vectors.
        Computes dynamic threshold from training data distribution.
        """
        if len(faces) == 0:
            raise ValueError("Cannot train with 0 samples.")

        k = min(KNN_NEIGHBORS, len(faces))
        self.knn = KNeighborsClassifier(n_neighbors=k)
        self.knn.fit(faces, labels)

        # Dynamic threshold — avoids hardcoded magic numbers
        dists, _ = self.knn.kneighbors(faces)
        self.threshold = float(dists.max() * THRESHOLD_MULT)
        self._trained  = True

        logger.info(f"KNN trained | k={k} | samples={len(faces)} "
                    f"| persons={set(labels)} | threshold={self.threshold:.0f}")

    def predict(self, face_vector: np.ndarray) -> tuple:
        """
        Predict name + confidence for a single face vector.

        Returns:
            (name: str, confidence: float)
            name = "Unknown" if distance exceeds threshold
            confidence = 0–100 (higher = more certain)
        """
        if not self._trained:
            raise RuntimeError("Model not trained. Call train() first.")

        vec = face_vector.reshape(1, -1).astype(np.float32)
        dists, _ = self.knn.kneighbors(vec)
        avg_dist  = float(dists[0].mean())

        if avg_dist > self.threshold:
            return "Unknown", 0.0

        name       = str(self.knn.predict(vec)[0])
        confidence = max(0.0, round((1 - avg_dist / self.threshold) * 100, 1))
        return name, confidence

    @property
    def is_trained(self) -> bool:
        return self._trained
