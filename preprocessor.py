"""
preprocessor.py - Reusable face normalization pipeline.
Same preprocessing MUST be used in both face.py (capture) and test.py (predict).
"""
import cv2
import numpy as np
from config import IMG_SIZE


def normalize_face(crop: np.ndarray,
                   img_size: tuple = IMG_SIZE) -> np.ndarray:
    """
    Convert a BGR face crop into a flat, lighting-invariant feature vector.

    Pipeline:
        BGR → Grayscale → Histogram Equalization → BGR → Resize → Flatten

    Args:
        crop:     BGR image crop of a detected face (any size)
        img_size: target (width, height) before flattening

    Returns:
        1-D numpy array of length img_size[0] * img_size[1] * 3
    """
    if crop is None or crop.size == 0:
        raise ValueError("normalize_face received an empty crop")

    gray     = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    eq       = cv2.equalizeHist(gray)
    bgr_eq   = cv2.cvtColor(eq, cv2.COLOR_GRAY2BGR)
    resized  = cv2.resize(bgr_eq, img_size)
    return resized.flatten().astype(np.float32)


def largest_face(faces):
    """
    Given an array of (x,y,w,h) detections, return only the largest one.
    Prevents multiple faces being captured as the same person.
    """
    if len(faces) == 0:
        return []
    return [max(faces, key=lambda f: f[2] * f[3])]
