"""
Database layer for PlayStation Management System.
"""

import sqlite3
import os
import threading
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pscafe.db")

_local = threading.local()

def get_db_path() -> str:
    """Get the database file path."""
    return DB_PATH

def get_connection():
    """Get a thread-local database connection.
    
    Each thread gets its own connection, ensuring thread safety without
    relying on check_same_thread=False.
    Uses default isolation level for proper transaction support.
    """
    if not hasattr(_local, 'connection') or _local.connection is None:
        db_path = get_db_path()
        _local.connection = sqlite3.connect(
            db_path,
            timeout=10.0
        )
        _local.connection.row_factory = sqlite3.Row
        _local.connection.execute("PRAGMA journal_mode=WAL")
        _local.connection.execute("PRAGMA busy_timeout=10000")
        logger.debug(f"Created new thread-local database connection for thread {threading.current_thread().name}")
    
    return _local.connection

def close_connection():
    """Close the thread-local database connection."""
    if hasattr(_local, 'connection') and _local.connection:
        try:
            _local.connection.close()
            _local.connection = None
            logger.debug(f"Closed database connection for thread {threading.current_thread().name}")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

def init_database():
    """Initialize the database with required tables."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price_per_hour INTEGER NOT NULL DEFAULT 100,
            status TEXT NOT NULL DEFAULT 'available',
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            session_type TEXT NOT NULL,
            start_time TEXT NOT NULL,
            expected_end_time TEXT,
            end_time TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            billed_minutes INTEGER DEFAULT 0,
            final_price INTEGER DEFAULT 0,
            acknowledged INTEGER DEFAULT 0,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """)
    
    conn.commit()
    conn.close()

def sync_device_sessions():
    """Ensure device status matches active sessions."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE devices 
        SET status = 'in_use' 
        WHERE id IN (SELECT device_id FROM sessions WHERE status IN ('active', 'overdue'))
    """)
    
    cursor.execute("""
        UPDATE devices 
        SET status = 'available' 
        WHERE id NOT IN (SELECT device_id FROM sessions WHERE status IN ('active', 'overdue'))
        AND status != 'available'
    """)
    
    conn.commit()

def get_next_device_number() -> int:
    """Get next available device number (max + 1)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM devices WHERE name LIKE 'PS%' AND name GLOB 'PS[0-9]*'")
    names = cursor.fetchall()
    max_num = 0
    for row in names:
        try:
            num = int(row[0].replace('PS', ''))
            if num > max_num:
                max_num = num
        except:
            pass
    return max_num + 1

def device_name_exists(name: str, exclude_device_id: int = None) -> bool:
    """Check if device name already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_device_id:
        cursor.execute("SELECT id FROM devices WHERE name = ? AND id != ?", (name, exclude_device_id))
    else:
        cursor.execute("SELECT id FROM devices WHERE name = ?", (name,))
    return cursor.fetchone() is not None

def create_device(name: str, price_per_hour: int) -> int:
    """Create a new device."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO devices (name, price_per_hour, status, created_at) VALUES (?, ?, 'available', ?)",
        (name, price_per_hour, datetime.now().isoformat())
    )
    conn.commit()
    return cursor.lastrowid

def get_all_devices() -> List[Dict[str, Any]]:
    """Get all devices."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices ORDER BY id")
    return [dict(row) for row in cursor.fetchall()]

def get_device(device_id: int) -> Optional[Dict[str, Any]]:
    """Get a device by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def update_device(device_id: int, name: str, price_per_hour: int) -> bool:
    """Update a device."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE devices SET name = ?, price_per_hour = ? WHERE id = ?",
        (name, price_per_hour, device_id)
    )
    conn.commit()
    return cursor.rowcount > 0

def delete_device(device_id: int) -> bool:
    """Delete a device and all related data (only if no active session).
    
    Uses transactions to ensure data consistency.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check for active sessions
        cursor.execute(
            "SELECT id FROM sessions WHERE device_id = ? AND status = 'active'",
            (device_id,)
        )
        if cursor.fetchone():
            return False
        
        # Delete sessions first (foreign key constraint)
        cursor.execute("DELETE FROM sessions WHERE device_id = ?", (device_id,))
        
        # Delete device
        cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        
        # Commit transaction
        conn.commit()
        
        logger.info(f"Device {device_id} deleted successfully with all related sessions")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting device {device_id}: {e}")
        return False

def update_device_status(device_id: int, status: str) -> bool:
    """Update device status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE devices SET status = ? WHERE id = ?",
        (status, device_id)
    )
    conn.commit()
    return cursor.rowcount > 0

def create_session(device_id: int, session_type: str, expected_end_time: Optional[str] = None) -> int:
    """Create a new session."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO sessions (device_id, session_type, start_time, expected_end_time, status) VALUES (?, ?, ?, ?, 'active')",
        (device_id, session_type, now, expected_end_time)
    )
    conn.commit()
    session_id = cursor.lastrowid
    update_device_status(device_id, 'in_use')
    return session_id

def get_active_session(device_id: int) -> Optional[Dict[str, Any]]:
    """Get active session for a device."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sessions WHERE device_id = ? AND status IN ('active', 'overdue') ORDER BY id DESC LIMIT 1",
        (device_id,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None

def get_session(session_id: int) -> Optional[Dict[str, Any]]:
    """Get a session by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_all_active_sessions() -> List[Dict[str, Any]]:
    """Get all active sessions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE status IN ('active', 'overdue')")
    return [dict(row) for row in cursor.fetchall()]

def end_session(session_id: int, final_price: int, billed_minutes: int) -> bool:
    """End a session.
    
    Updates session status and device status atomically.
    """
    conn = get_connection()
    session = get_session(session_id)
    if not session:
        logger.warning(f"Attempted to end non-existent session {session_id}")
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE sessions SET status = 'completed', end_time = ?, final_price = ?, billed_minutes = ? WHERE id = ?",
            (datetime.now().isoformat(), final_price, billed_minutes, session_id)
        )
        
        update_device_status(session['device_id'], 'available')
        
        conn.commit()
        logger.info(f"Session {session_id} ended. Price: {final_price}, Duration: {billed_minutes}m")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error ending session {session_id}: {e}")
        return False

def mark_session_overdue(session_id: int) -> bool:
    """Mark a session as overdue."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET status = 'overdue' WHERE id = ?",
        (session_id,)
    )
    conn.commit()
    return cursor.rowcount > 0

def acknowledge_session(session_id: int) -> bool:
    """Acknowledge an overdue session alert."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET acknowledged = 1 WHERE id = ?",
        (session_id,)
    )
    conn.commit()
    return cursor.rowcount > 0

def extend_session(session_id: int, new_expected_end_time: str) -> bool:
    """Extend a session's expected end time."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET expected_end_time = ?, status = 'active' WHERE id = ?",
        (new_expected_end_time, session_id)
    )
    conn.commit()
    return cursor.rowcount > 0

def get_session_history(start_date: Optional[str] = None, end_date: Optional[str] = None, 
                        device_id: Optional[int] = None, session_type: Optional[str] = None,
                        status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get session history with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT s.*, d.name as device_name FROM sessions s JOIN devices d ON s.device_id = d.id WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND s.start_time >= ?"
        params.append(start_date)
    if end_date:
        query += " AND s.start_time <= ?"
        params.append(end_date)
    if device_id:
        query += " AND s.device_id = ?"
        params.append(device_id)
    if session_type:
        query += " AND s.session_type = ?"
        params.append(session_type)
    if status_filter:
        query += " AND s.status = ?"
        params.append(status_filter)
    
    query += " ORDER BY s.start_time DESC"
    
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

def get_report_summary(start_date: str, end_date: str, device_id: Optional[int] = None) -> Dict[str, Any]:
    """Get report summary statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT COUNT(*) as total_sessions,
               COALESCE(SUM(billed_minutes), 0) as total_minutes,
               COALESCE(SUM(final_price), 0) as total_revenue,
               AVG(billed_minutes) as avg_duration
        FROM sessions
        WHERE start_time >= ? AND start_time <= ?
        AND status = 'completed'
    """
    params = [start_date, end_date]
    
    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
    
    cursor.execute(query, params)
    row = cursor.fetchone()
    
    result = dict(row) if row else {'total_sessions': 0, 'total_minutes': 0, 'total_revenue': 0, 'avg_duration': 0}
    
    cursor.execute("""
        SELECT d.name, COUNT(*) as usage_count
        FROM sessions s
        JOIN devices d ON s.device_id = d.id
        WHERE s.start_time >= ? AND s.start_time <= ?
        AND s.status = 'completed'
        GROUP BY s.device_id
        ORDER BY usage_count DESC
        LIMIT 1
    """, [start_date, end_date])
    
    most_used = cursor.fetchone()
    result['most_used_device'] = most_used['name'] if most_used else None
    
    return result