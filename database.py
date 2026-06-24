"""
database.py - SQLite database layer.
Replaces flat CSV/JSON storage for users, students, attendance, notifications.
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash
from logger_setup import get_logger

logger = get_logger("database")
DB_PATH = "attendance.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create all tables and seed default admin/teacher accounts."""
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT    UNIQUE NOT NULL,
        password_hash TEXT    NOT NULL,
        role          TEXT    NOT NULL DEFAULT 'teacher',
        full_name     TEXT    NOT NULL,
        email         TEXT,
        created_at    TEXT    DEFAULT (datetime('now','localtime')),
        is_active     INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS students (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT    NOT NULL,
        roll_number   TEXT    UNIQUE NOT NULL,
        department    TEXT    NOT NULL DEFAULT 'General',
        email         TEXT,
        photo_path    TEXT,
        registered_at TEXT    DEFAULT (datetime('now','localtime')),
        is_active     INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS attendance (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  INTEGER NOT NULL,
        date        TEXT    NOT NULL,
        time_in     TEXT    NOT NULL,
        day_name    TEXT    NOT NULL,
        status      TEXT    NOT NULL DEFAULT 'Present',
        marked_by   INTEGER,
        confidence  REAL    DEFAULT 0.0,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (marked_by)  REFERENCES users(id),
        UNIQUE(student_id, date)
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        type        TEXT    NOT NULL,
        message     TEXT    NOT NULL,
        student_id  INTEGER,
        is_read     INTEGER DEFAULT 0,
        created_at  TEXT    DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS roles (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    UNIQUE NOT NULL,
        description TEXT
    );

    INSERT OR IGNORE INTO roles(name, description) VALUES
        ('admin',   'Full system access'),
        ('teacher', 'Attendance management');
    """)

    # Seed default admin
    if not c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        c.execute("""INSERT INTO users(username,password_hash,role,full_name,email)
                     VALUES(?,?,?,?,?)""",
                  ("admin",
                   generate_password_hash("admin123"),
                   "admin", "System Administrator", "admin@school.com"))
        logger.info("Default admin created  (username=admin  password=admin123)")

    # Seed default teacher
    if not c.execute("SELECT 1 FROM users WHERE username='teacher'").fetchone():
        c.execute("""INSERT INTO users(username,password_hash,role,full_name,email)
                     VALUES(?,?,?,?,?)""",
                  ("teacher",
                   generate_password_hash("teacher123"),
                   "teacher", "Default Teacher", "teacher@school.com"))
        logger.info("Default teacher created (username=teacher password=teacher123)")

    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", DB_PATH)
