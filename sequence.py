import sqlite3
import threading
from datetime import datetime
import config
from database import get_db_connection

_sequence_lock = threading.Lock()

def get_next_voter_id() -> str:
    """
    Atomically generates and increments the next unique Voter ID in the format:
    WRM2745001, WRM2745002, WRM2745003...
    Guarantees no duplicates and thread safety.
    """
    with _sequence_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        while True:
            # Fetch current sequence row with exclusive lock
            cursor.execute("SELECT prefix, current_number FROM voter_id_sequence LIMIT 1")
            row = cursor.fetchone()
            
            if not row:
                prefix = config.DEFAULT_VOTER_ID_PREFIX
                current_num = 0
                cursor.execute(
                    "INSERT INTO voter_id_sequence (prefix, current_number, last_voter_id, updated_at) VALUES (?, ?, ?, ?)",
                    (prefix, 0, None, datetime.now().isoformat())
                )
            else:
                prefix = row['prefix']
                current_num = row['current_number']
                
            next_num = current_num + 1
            # Format as WRM2745001 (padded to at least 3 digits)
            candidate_id = f"{prefix}{next_num:03d}"
            
            # Verify candidate ID does not exist in voters table
            cursor.execute("SELECT id FROM voters WHERE voter_id = ?", (candidate_id,))
            exists = cursor.fetchone()
            
            if not exists:
                # Update sequence table
                cursor.execute(
                    "UPDATE voter_id_sequence SET current_number = ?, last_voter_id = ?, updated_at = ?",
                    (next_num, candidate_id, datetime.now().isoformat())
                )
                conn.commit()
                conn.close()
                return candidate_id
            else:
                # If already exists, bump number and continue loop
                cursor.execute(
                    "UPDATE voter_id_sequence SET current_number = ?, updated_at = ?",
                    (next_num, datetime.now().isoformat())
                )
                conn.commit()

def preview_next_voter_id() -> str:
    """
    Returns what the next Voter ID will likely be without incrementing the counter.
    Useful for display in forms.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT prefix, current_number FROM voter_id_sequence LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return f"{config.DEFAULT_VOTER_ID_PREFIX}001"
    
    next_num = row['current_number'] + 1
    return f"{row['prefix']}{next_num:03d}"
