"""
data_manager.py - Safe, non-pickle data persistence.

Face vectors → NumPy .npy  (safe binary format)
Name labels  → JSON        (human-readable, no code execution risk)
Attendance   → CSV         (atomic write via temp file)
"""
import os
import csv
import json
import shutil
import tempfile
import numpy as np
from logger_setup import get_logger
from config import FACES_FILE, NAMES_FILE, DATA_DIR, ATTENDANCE_DIR

logger = get_logger("data_manager")

COL_NAMES = ["NAME", "TIME", "DAY", "DATE"]


# ── Face / Name storage ────────────────────────────────────────────────────────

def load_data() -> tuple[np.ndarray, list]:
    """
    Load face vectors and name labels.
    Returns (faces_array, names_list) or raises FileNotFoundError.
    """
    if not os.path.exists(FACES_FILE) or not os.path.exists(NAMES_FILE):
        raise FileNotFoundError(
            "Training data not found. Run face.py first to collect face data."
        )
    faces = np.load(FACES_FILE)
    with open(NAMES_FILE, "r", encoding="utf-8") as f:
        names = json.load(f)

    if len(names) != len(faces):
        min_len = min(len(names), len(faces))
        logger.warning(f"Length mismatch detected — trimming to {min_len} samples.")
        faces = faces[:min_len]
        names = names[:min_len]
        save_data(faces, names)          # auto-repair on load

    logger.info(f"Loaded {len(faces)} samples | Persons: {set(names)}")
    return faces, names


def save_data(faces: np.ndarray, names: list) -> None:
    """Persist face vectors and name labels safely."""
    os.makedirs(DATA_DIR, exist_ok=True)
    np.save(FACES_FILE, faces)
    with open(NAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(names, f, ensure_ascii=False)
    logger.debug(f"Saved {len(names)} samples to {DATA_DIR}/")


def append_data(new_faces: np.ndarray, name: str) -> None:
    """
    Add new face samples for a person to existing data.
    Creates files if they don't exist yet.
    """
    if os.path.exists(FACES_FILE) and os.path.exists(NAMES_FILE):
        existing_faces, existing_names = load_data()
        combined_faces = np.append(existing_faces, new_faces, axis=0)
        combined_names = existing_names + [name] * len(new_faces)
    else:
        combined_faces = new_faces
        combined_names = [name] * len(new_faces)

    save_data(combined_faces, combined_names)
    logger.info(f"Saved OK — {len(combined_names)} total samples | Persons: {set(combined_names)}")


def delete_person(name: str) -> bool:
    """Remove all samples for a given person. Returns True if found & removed."""
    try:
        faces, names = load_data()
    except FileNotFoundError:
        logger.error("No training data found.")
        return False

    indices = [i for i, n in enumerate(names) if n != name]
    if len(indices) == len(names):
        logger.warning(f"Person '{name}' not found in training data.")
        return False

    filtered_faces = faces[indices]
    filtered_names = [names[i] for i in indices]
    save_data(filtered_faces, filtered_names)
    logger.info(f"Deleted '{name}'. Remaining persons: {set(filtered_names)}")
    return True


def list_persons() -> list:
    """Return sorted list of registered persons."""
    try:
        _, names = load_data()
        return sorted(set(names))
    except FileNotFoundError:
        return []


# ── Attendance CSV ─────────────────────────────────────────────────────────────

def write_attendance(name: str, time_str: str, day_str: str, date_str: str) -> None:
    """
    Atomically append one attendance record to today's CSV.
    Uses temp-file + rename to prevent corrupt writes on crash.
    """
    os.makedirs(ATTENDANCE_DIR, exist_ok=True)
    filename   = os.path.join(ATTENDANCE_DIR, f"Attendance_{date_str}.csv")
    file_exists = os.path.isfile(filename)

    # Write to temp file first, then move — atomic on most OSes
    tmp_fd, tmp_path = tempfile.mkstemp(dir=ATTENDANCE_DIR, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", newline="", encoding="utf-8") as tmp_file:
            # Copy existing content
            if file_exists:
                with open(filename, "r", newline="", encoding="utf-8") as src:
                    tmp_file.write(src.read())
            else:
                writer = csv.writer(tmp_file)
                writer.writerow(COL_NAMES)

            writer = csv.writer(tmp_file)
            writer.writerow([name, time_str, day_str, date_str])

        shutil.move(tmp_path, filename)
        logger.info(f"Attendance written — {name} | {time_str} | {day_str}")
    except Exception as e:
        os.unlink(tmp_path)          # cleanup temp on failure
        logger.error(f"Failed to write attendance for {name}: {e}")
        raise


def load_today_attendance(date_str: str) -> set:
    """Return set of names already marked today (for duplicate prevention)."""
    filename = os.path.join(ATTENDANCE_DIR, f"Attendance_{date_str}.csv")
    marked   = set()
    if os.path.isfile(filename):
        try:
            with open(filename, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("NAME"):
                        marked.add(row["NAME"].strip())
        except Exception as e:
            logger.warning(f"Could not read today's CSV: {e}")
    return marked


def load_all_attendance() -> list:
    """Read all CSV files and return a unified list of records (newest first)."""
    import glob
    records = []
    pattern = os.path.join(ATTENDANCE_DIR, "Attendance_*.csv")
    for filepath in sorted(glob.glob(pattern), reverse=True):
        try:
            with open(filepath, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    continue
                for row in reader:
                    if any(v.strip() for v in row.values()):
                        records.append(dict(row))
        except Exception as e:
            logger.warning(f"Could not read {filepath}: {e}")
    return records
