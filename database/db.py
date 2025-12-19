# database/db.py
import sqlite3

DB_PATH = "database/kiosk.db"

def get_conn():
    con = sqlite3.connect(DB_PATH, timeout=5)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA busy_timeout = 5000;")
    return con


def log_event(account_id, event_type, amount=0.0, details="", conn=None):
    """
    If conn is provided, reuse it (prevents DB locking).
    Otherwise, open a safe standalone connection.
    """
    if conn is None:
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("""
                INSERT INTO audit_log (account_id, event_type, amount, details)
                VALUES (?, ?, ?, ?)
            """, (account_id, event_type, amount, details))
            con.commit()
    else:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_log (account_id, event_type, amount, details)
            VALUES (?, ?, ?, ?)
        """, (account_id, event_type, amount, details))
