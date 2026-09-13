import sqlite3
from contextlib import contextmanager
from backend.config import DATA

@contextmanager
def connection():
    db = sqlite3.connect(DATA / 'studio.sqlite3', timeout=30)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    finally:
        db.close()

def initialize_database():
    with connection() as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
        CREATE TABLE IF NOT EXISTS voices (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, original TEXT NOT NULL,
            reference TEXT NOT NULL, duration REAL NOT NULL, created TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS emotion_refs (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, reference TEXT NOT NULL,
            duration REAL NOT NULL, created TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, status TEXT NOT NULL, request TEXT NOT NULL,
            audio TEXT, error TEXT, created TEXT NOT NULL, elapsed REAL, duration REAL
        );
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, script TEXT NOT NULL DEFAULT '',
            settings TEXT NOT NULL DEFAULT '{}', updated TEXT NOT NULL
        );
        ''')
        db.execute("UPDATE jobs SET status='failed', error='The application stopped before this job finished.' WHERE status IN ('queued','generating')")
