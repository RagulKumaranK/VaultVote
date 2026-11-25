import os
import uuid
import random
import hashlib
from datetime import datetime
from database import get_db_connection, log_enrollment

PATTERN_TYPES = ['Whorl', 'Right Loop', 'Left Loop', 'Tented Arch', 'Double Loop']

def generate_simulated_fingerprint_template(voter_id: str):
    """
    Generates a cryptographically unique simulated fingerprint enrollment reference
    and synthetic biometric minutiae parameters for demonstration purposes.
    Explicitly marked as simulated.
    """
    # Deterministic yet unique seed based on voter_id and salt
    seed_str = f"{voter_id}_{uuid.uuid4().hex}_{datetime.now().isoformat()}"
    digest = hashlib.sha256(seed_str.encode('utf-8')).hexdigest().upper()
    
    simulated_ref = f"FPSIM-{digest[:8]}-{digest[8:16]}"
    pattern = random.choice(PATTERN_TYPES)
    minutiae_count = random.randint(45, 68)
    quality_score = round(random.uniform(92.0, 99.4), 1)

    return {
        "reference": simulated_ref,
        "pattern_type": pattern,
        "minutiae_count": minutiae_count,
        "quality_score": quality_score,
        "is_simulated": True
    }

def enroll_simulated_fingerprint(voter_id: str):
    """
    Enrolls a simulated fingerprint for the given voter ID.
    Performs duplicate reference check, stores in database, updates voter status,
    and writes to audit log.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify voter exists
    cursor.execute("SELECT id, voter_id, full_name, fingerprint_status FROM voters WHERE voter_id = ?", (voter_id,))
    voter = cursor.fetchone()
    if not voter:
        conn.close()
        return {"success": False, "message": f"Voter ID '{voter_id}' not found."}

    # Generate unique simulated reference with collision avoidance
    max_retries = 5
    template = None
    for _ in range(max_retries):
        candidate_template = generate_simulated_fingerprint_template(voter_id)
        cursor.execute("SELECT id FROM fingerprint_biometrics WHERE simulated_reference = ?", (candidate_template['reference'],))
        if not cursor.fetchone():
            template = candidate_template
            break

    if not template:
        conn.close()
        return {"success": False, "message": "Failed to generate unique fingerprint reference."}

    # Check if voter already has an enrolled fingerprint record
    cursor.execute("SELECT id FROM fingerprint_biometrics WHERE voter_id = ?", (voter_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE fingerprint_biometrics 
            SET simulated_reference = ?, pattern_type = ?, minutiae_count = ?, is_simulated = 1, enrolled_at = ?
            WHERE voter_id = ?
        ''', (template['reference'], template['pattern_type'], template['minutiae_count'], datetime.now().isoformat(), voter_id))
    else:
        cursor.execute('''
            INSERT INTO fingerprint_biometrics (voter_id, simulated_reference, pattern_type, minutiae_count, is_simulated, enrolled_at)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (voter_id, template['reference'], template['pattern_type'], template['minutiae_count'], datetime.now().isoformat()))

    # Update voters table
    cursor.execute('''
        UPDATE voters 
        SET fingerprint_status = 'ENROLLED', updated_at = ?
        WHERE voter_id = ?
    ''', (datetime.now().isoformat(), voter_id))

    conn.commit()
    conn.close()

    # Log to audit trail
    log_enrollment(
        voter_id=voter_id,
        action="FINGERPRINT_ENROLLED",
        details=f"Simulated Biometric Enrolled: Ref={template['reference']}, Pattern={template['pattern_type']}, Minutiae={template['minutiae_count']}"
    )

    return {
        "success": True,
        "message": "SIMULATED FINGERPRINT ENROLLMENT SUCCESSFUL",
        "reference": template['reference'],
        "pattern_type": template['pattern_type'],
        "minutiae_count": template['minutiae_count'],
        "quality_score": template['quality_score'],
        "is_simulated": True
    }
