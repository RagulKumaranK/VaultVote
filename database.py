import os
import sqlite3
import hashlib
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import config

def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(config.DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_aadhaar(aadhaar_str: str) -> str:
    """Computes a one-way SHA-256 hash of the synthetic Aadhaar number for privacy-safe deduplication."""
    cleaned = ''.join(filter(str.isdigit, str(aadhaar_str).strip()))
    return hashlib.sha256(cleaned.encode('utf-8')).hexdigest()

def mask_aadhaar(aadhaar_str: str) -> str:
    """Masks synthetic Aadhaar as XXXX-XXXX-1234."""
    cleaned = ''.join(filter(str.isdigit, str(aadhaar_str).strip()))
    if len(cleaned) == 12:
        return f"XXXX-XXXX-{cleaned[-4:]}"
    elif len(cleaned) >= 4:
        return f"XXXX-XXXX-{cleaned[-4:]}"
    return "XXXX-XXXX-0000"

def init_db():
    """Initializes the database schema and seeds default admin and voter ID sequence."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Admin Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')

    # 2. Voters Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            father_name TEXT NOT NULL,
            aadhaar_hash TEXT UNIQUE NOT NULL,
            aadhaar_masked TEXT NOT NULL,
            mobile TEXT NOT NULL,
            address TEXT NOT NULL,
            district TEXT NOT NULL,
            state TEXT NOT NULL,
            pincode TEXT NOT NULL,
            face_status TEXT DEFAULT 'PENDING',
            fingerprint_status TEXT DEFAULT 'PENDING',
            qr_status TEXT DEFAULT 'PENDING',
            registration_status TEXT DEFAULT 'INCOMPLETE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Face Biometrics Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_biometrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            photo_path TEXT NOT NULL,
            face_encoding TEXT NOT NULL,
            confidence_score REAL DEFAULT 0.95,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voter_id) REFERENCES voters (voter_id) ON DELETE CASCADE
        )
    ''')

    # 4. Fingerprint Biometrics Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fingerprint_biometrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            simulated_reference TEXT UNIQUE NOT NULL,
            pattern_type TEXT DEFAULT 'Whorl',
            minutiae_count INTEGER DEFAULT 48,
            is_simulated INTEGER DEFAULT 1,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voter_id) REFERENCES voters (voter_id) ON DELETE CASCADE
        )
    ''')

    # 5. Voter QR Tokens Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voter_qr_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            qr_token TEXT UNIQUE NOT NULL,
            qr_image_path TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voter_id) REFERENCES voters (voter_id) ON DELETE CASCADE
        )
    ''')

    # 6. Voter ID Sequence Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voter_id_sequence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefix TEXT NOT NULL DEFAULT 'WRM2745',
            current_number INTEGER NOT NULL DEFAULT 0,
            last_voter_id TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 7. Enrollment Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollment_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 8. Candidates Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            party TEXT NOT NULL,
            symbol_name TEXT NOT NULL,
            symbol_icon TEXT NOT NULL,
            color TEXT DEFAULT '#2563EB',
            banner_image TEXT,
            symbol_image TEXT,
            votes_count INTEGER DEFAULT 0
        )
    ''')

    # Ensure banner_image and symbol_image columns exist for existing tables
    cursor.execute('PRAGMA table_info(candidates)')
    existing_cols = [c[1] for c in cursor.fetchall()]
    if 'banner_image' not in existing_cols:
        cursor.execute('ALTER TABLE candidates ADD COLUMN banner_image TEXT')
    if 'symbol_image' not in existing_cols:
        cursor.execute('ALTER TABLE candidates ADD COLUMN symbol_image TEXT')

    # 9. Votes Table (One vote per voter enforced via UNIQUE constraint)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            candidate_id INTEGER NOT NULL,
            cast_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            FOREIGN KEY (voter_id) REFERENCES voters (voter_id) ON DELETE CASCADE,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
        )
    ''')

    # Create Indexes for fast querying
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voters_voter_id ON voters(voter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voters_aadhaar_hash ON voters(aadhaar_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voters_name ON voters(full_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_voter_id ON enrollment_logs(voter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_voter_id ON votes(voter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_candidate_id ON votes(candidate_id)')

    # Seed Default Admin if table is empty
    cursor.execute('SELECT COUNT(*) as count FROM admin')
    if cursor.fetchone()['count'] == 0:
        hashed_pw = generate_password_hash(config.DEFAULT_ADMIN_PASSWORD)
        cursor.execute('''
            INSERT INTO admin (username, password_hash, full_name, created_at)
            VALUES (?, ?, ?, ?)
        ''', (config.DEFAULT_ADMIN_USERNAME, hashed_pw, config.DEFAULT_ADMIN_NAME, datetime.now().isoformat()))

    # Seed Voter ID sequence if table is empty
    cursor.execute('SELECT COUNT(*) as count FROM voter_id_sequence')
    if cursor.fetchone()['count'] == 0:
        cursor.execute('''
            INSERT INTO voter_id_sequence (prefix, current_number, last_voter_id, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (config.DEFAULT_VOTER_ID_PREFIX, 0, None, datetime.now().isoformat()))

    # Seed Default Official Candidates if table is empty
    cursor.execute('SELECT COUNT(*) as count FROM candidates')
    if cursor.fetchone()['count'] == 0:
        default_candidates = [
            ("Vijay (விஜய்)", "Tamizhaga Vettri Kazhagam (தமிழக வெற்றி கழகம்)", "TVK", "bi-flag-fill", "#DC2626", "Candidates/1.png", "Candidates/symbol1.png", 0),
            ("M. K. Stalin (மு.க. ஸ்டாலின்)", "Dravida Munnetra Kazhagam (திராவிட முன்னேற்றக் கழகம்)", "Rising Sun", "bi-sun-fill", "#DC2626", "Candidates/2.png", "Candidates/symbol2.png", 0),
            ("Edappadi K. Palaniswami (எடப்பாடி பழனிசாமி)", "All India Anna Dravida Munnetra Kazhagam (அஇஅதிமுக)", "Two Leaves", "bi-tree-fill", "#16A34A", "Candidates/3.png", "Candidates/symbol3.png", 0),
            ("Seeman (சீமான்)", "Naam Tamilar Katchi (நாம் தமிழர் கட்சி)", "Tiger & Torch", "bi-fire", "#EAB308", "Candidates/4.png", "Candidates/symbol4.png", 0),
            ("None of the Above (NOTA)", "Independent / NOTA (நோட்டா)", "NOTA Ballot", "bi-x-circle-fill", "#64748B", "Candidates/5.png", "Candidates/symbol5.png", 0)
        ]
        cursor.executemany('''
            INSERT INTO candidates (name, party, symbol_name, symbol_icon, color, banner_image, symbol_image, votes_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_candidates)
    else:
        # Ensure candidate assets (banner and symbol) are synced
        candidate_assets = {
            1: ('Candidates/1.png', 'Candidates/symbol1.png'),
            2: ('Candidates/2.png', 'Candidates/symbol2.png'),
            3: ('Candidates/3.png', 'Candidates/symbol3.png'),
            4: ('Candidates/4.png', 'Candidates/symbol4.png'),
            5: ('Candidates/5.png', 'Candidates/symbol5.png')
        }
        for cid, (b_img, s_img) in candidate_assets.items():
            cursor.execute('UPDATE candidates SET banner_image = ?, symbol_image = ? WHERE id = ?', (b_img, s_img, cid))

    conn.commit()
    conn.close()

def log_enrollment(voter_id: str, action: str, details: str = '', ip_address: str = '127.0.0.1'):
    """Appends an event to the audit/enrollment log."""
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO enrollment_logs (voter_id, action, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (voter_id, action, details, ip_address, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging enrollment event: {e}")

def check_duplicate_aadhaar(aadhaar_number: str):
    """
    Checks if a voter with the given Aadhaar number is already enrolled.
    Returns existing voter record dict or None.
    """
    a_hash = hash_aadhaar(aadhaar_number)
    conn = get_db_connection()
    row = conn.execute('''
        SELECT voter_id, full_name, dob, aadhaar_masked, mobile, created_at, registration_status
        FROM voters
        WHERE aadhaar_hash = ?
    ''', (a_hash,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def check_duplicate_identity(full_name: str, dob: str, mobile: str):
    """
    Checks if a voter with matching full name + DOB or matching mobile exists.
    Returns existing voter record dict or None.
    """
    conn = get_db_connection()
    # Check exact name (case-insensitive) and DOB match
    row = conn.execute('''
        SELECT voter_id, full_name, dob, aadhaar_masked, mobile, created_at, registration_status
        FROM voters
        WHERE LOWER(full_name) = LOWER(?) AND dob = ?
    ''', (full_name.strip(), dob.strip())).fetchone()
    
    if not row:
        row = conn.execute('''
            SELECT voter_id, full_name, dob, aadhaar_masked, mobile, created_at, registration_status
            FROM voters
            WHERE mobile = ?
        ''', (mobile.strip(),)).fetchone()
        
    conn.close()
    if row:
        return dict(row)
    return None

def get_dashboard_metrics():
    """Calculates statistics for admin dashboard."""
    conn = get_db_connection()
    total_voters = conn.execute('SELECT COUNT(*) as c FROM voters').fetchone()['c']
    face_registered = conn.execute("SELECT COUNT(*) as c FROM voters WHERE face_status = 'ENROLLED'").fetchone()['c']
    fp_registered = conn.execute("SELECT COUNT(*) as c FROM voters WHERE fingerprint_status = 'ENROLLED'").fetchone()['c']
    completed = conn.execute("SELECT COUNT(*) as c FROM voters WHERE registration_status = 'COMPLETED'").fetchone()['c']

    recent_voters = conn.execute('''
        SELECT v.*, fb.photo_path, qr.qr_token
        FROM voters v
        LEFT JOIN face_biometrics fb ON v.voter_id = fb.voter_id
        LEFT JOIN voter_qr_tokens qr ON v.voter_id = qr.voter_id
        ORDER BY v.created_at DESC
        LIMIT 6
    ''').fetchall()

    recent_logs = conn.execute('''
        SELECT * FROM enrollment_logs ORDER BY timestamp DESC LIMIT 8
    ''').fetchall()

    total_votes = conn.execute('SELECT COUNT(*) as c FROM votes').fetchone()['c']
    turnout_pct = round((total_votes / total_voters * 100), 1) if total_voters > 0 else 0
    candidates = conn.execute('SELECT * FROM candidates ORDER BY votes_count DESC, id ASC').fetchall()

    conn.close()
    return {
        'total_voters': total_voters,
        'face_registered': face_registered,
        'fingerprint_registered': fp_registered,
        'completed': completed,
        'total_votes': total_votes,
        'turnout_pct': turnout_pct,
        'candidates': [dict(c) for c in candidates],
        'recent_voters': [dict(r) for r in recent_voters],
        'recent_logs': [dict(l) for l in recent_logs]
    }

def delete_voter(voter_id: str, admin_name: str = 'Admin') -> dict:
    """
    Permanently deletes a voter record and associated biometric files,
    tokens, generated card files, and logs the deletion audit event.
    Returns {"success": bool, "message": str}.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch voter and related file paths
    voter = cursor.execute('SELECT * FROM voters WHERE voter_id = ?', (voter_id,)).fetchone()
    if not voter:
        conn.close()
        return {"success": False, "message": f"Voter '{voter_id}' does not exist."}
    
    voter_name = voter['full_name']
    
    # Get photo path
    fb = cursor.execute('SELECT photo_path FROM face_biometrics WHERE voter_id = ?', (voter_id,)).fetchone()
    photo_path = fb['photo_path'] if fb else None
    
    # Get qr image path
    qr = cursor.execute('SELECT qr_image_path FROM voter_qr_tokens WHERE voter_id = ?', (voter_id,)).fetchone()
    qr_image_path = qr['qr_image_path'] if qr else None
    
    # 2. Delete database rows (explicitly clean child tables as well)
    cursor.execute('DELETE FROM face_biometrics WHERE voter_id = ?', (voter_id,))
    cursor.execute('DELETE FROM fingerprint_biometrics WHERE voter_id = ?', (voter_id,))
    cursor.execute('DELETE FROM voter_qr_tokens WHERE voter_id = ?', (voter_id,))
    cursor.execute('DELETE FROM voters WHERE voter_id = ?', (voter_id,))
    conn.commit()
    conn.close()
    
    # 3. Clean up physical files from disk
    files_to_remove = []
    if photo_path:
        files_to_remove.append(os.path.join(config.STATIC_DIR, photo_path))
    if qr_image_path:
        files_to_remove.append(os.path.join(config.STATIC_DIR, qr_image_path))
    
    # Card files
    files_to_remove.append(os.path.join(config.CARDS_DIR, f"{voter_id}_card.png"))
    files_to_remove.append(os.path.join(config.CARDS_DIR, f"{voter_id}_card.pdf"))
    
    for fpath in files_to_remove:
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception as e:
                print(f"Notice: Failed to remove file {fpath}: {e}")
                
    # 4. Log the audit event
    log_enrollment(
        voter_id=voter_id,
        action="VOTER_DELETED",
        details=f"Voter {voter_id} ({voter_name}) was permanently deleted by {admin_name}."
    )
    
    return {"success": True, "message": f"Voter {voter_id} ({voter_name}) has been permanently deleted."}

def get_candidates():
    """Returns list of all active candidates."""
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM candidates ORDER BY id ASC').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_election_results():
    """
    Computes and returns comprehensive live election results:
    - total_voters: count of registered voters
    - total_votes: total votes cast
    - turnout_pct: percentage turnout
    - candidates: list of candidates ordered by votes_count DESC, id ASC, with rank, share_pct
    - leader: leading candidate dict (if votes exist)
    - runner_up: second place candidate dict (if votes exist)
    - margin: difference in votes between leader and runner-up
    - is_tie: bool, whether there is a tie for 1st place
    - has_votes: bool
    - timestamp: current formatted time
    """
    conn = get_db_connection()
    total_voters = conn.execute('SELECT COUNT(*) as c FROM voters').fetchone()['c']
    total_votes = conn.execute('SELECT COUNT(*) as c FROM votes').fetchone()['c']
    turnout_pct = round((total_votes / total_voters * 100), 2) if total_voters > 0 else 0.0

    candidates_raw = conn.execute('SELECT * FROM candidates ORDER BY votes_count DESC, id ASC').fetchall()
    conn.close()

    candidates = [dict(c) for c in candidates_raw]
    for idx, cand in enumerate(candidates):
        cand['rank'] = idx + 1
        cand['share_pct'] = round((cand['votes_count'] / total_votes * 100), 1) if total_votes > 0 else 0.0

    leader = candidates[0] if candidates and total_votes > 0 and candidates[0]['votes_count'] > 0 else None
    runner_up = candidates[1] if len(candidates) > 1 and total_votes > 0 and candidates[1]['votes_count'] > 0 else None

    is_tie = False
    if leader and runner_up and leader['votes_count'] == runner_up['votes_count']:
        is_tie = True

    margin = (leader['votes_count'] - runner_up['votes_count']) if leader and runner_up else (leader['votes_count'] if leader else 0)

    return {
        'total_voters': total_voters,
        'total_votes': total_votes,
        'turnout_pct': turnout_pct,
        'candidates': candidates,
        'leader': leader,
        'runner_up': runner_up,
        'margin': margin,
        'is_tie': is_tie,
        'has_votes': total_votes > 0,
        'timestamp': datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    }

def check_voter_voting_eligibility(voter_identifier: str):
    """
    Checks if a voter is eligible to vote using either voter_id or qr_token.
    Returns:
    {
        "eligible": bool,
        "voter": dict or None,
        "reason": str,
        "has_voted": bool,
        "voted_at": str or None
    }
    """
    conn = get_db_connection()
    v_id = voter_identifier.strip()
    
    # If a full QR code JSON payload was passed, extract voter_id or auth_token
    if v_id.startswith('{') and '}' in v_id:
        try:
            parsed = json.loads(v_id)
            v_id = parsed.get('voter_id') or parsed.get('auth_token') or v_id
        except Exception:
            pass
    
    # Try finding by voter_id or QR token
    voter = conn.execute('''
        SELECT v.*, fb.photo_path, qr.qr_token
        FROM voters v
        LEFT JOIN face_biometrics fb ON v.voter_id = fb.voter_id
        LEFT JOIN voter_qr_tokens qr ON v.voter_id = qr.voter_id
        WHERE v.voter_id = ? OR qr.qr_token = ?
    ''', (v_id, v_id)).fetchone()

    if not voter:
        conn.close()
        return {
            "eligible": False,
            "voter": None,
            "reason": "Invalid Voter: No matching record found in the election registry. Please check your Voter ID or scan a valid card QR.",
            "has_voted": False,
            "voted_at": None
        }

    voter_dict = dict(voter)
    voter_id = voter_dict['voter_id']

    # Check if already voted
    vote = conn.execute('SELECT * FROM votes WHERE voter_id = ?', (voter_id,)).fetchone()
    if vote:
        conn.close()
        return {
            "eligible": False,
            "voter": voter_dict,
            "reason": f"VOTE ALREADY RECORDED: Voter {voter_id} ({voter_dict['full_name']}) has already cast their ballot on {vote['cast_at']}.",
            "has_voted": True,
            "voted_at": vote['cast_at']
        }

    # Check registration status
    if voter_dict['registration_status'] != 'COMPLETED':
        conn.close()
        return {
            "eligible": False,
            "voter": voter_dict,
            "reason": f"Biometric enrollment incomplete for {voter_id}. Both face photo and fingerprint must be registered before voting.",
            "has_voted": False,
            "voted_at": None
        }

    conn.close()
    return {
        "eligible": True,
        "voter": voter_dict,
        "reason": "Voter verified and eligible to cast vote.",
        "has_voted": False,
        "voted_at": None
    }

def cast_vote(voter_id: str, candidate_id: int, ip_address: str = '127.0.0.1') -> dict:
    """
    Casts a secret electronic ballot for the verified voter.
    Enforces one-vote-per-voter and atomic tallying.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify voter exists
    voter = cursor.execute('SELECT full_name, registration_status FROM voters WHERE voter_id = ?', (voter_id,)).fetchone()
    if not voter:
        conn.close()
        return {"success": False, "message": f"Voter '{voter_id}' not found."}
        
    # Check duplicate vote
    existing = cursor.execute('SELECT cast_at FROM votes WHERE voter_id = ?', (voter_id,)).fetchone()
    if existing:
        conn.close()
        return {"success": False, "message": f"Vote already cast by {voter_id} on {existing['cast_at']}."}

    # Verify candidate exists
    candidate = cursor.execute('SELECT name, party, symbol_name FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    if not candidate:
        conn.close()
        return {"success": False, "message": "Invalid candidate selection."}

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
            INSERT INTO votes (voter_id, candidate_id, cast_at, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (voter_id, candidate_id, now_iso, ip_address))
        cursor.execute('UPDATE candidates SET votes_count = votes_count + 1 WHERE id = ?', (candidate_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        return {"success": False, "message": "Duplicate vote detected. You have already voted."}
    finally:
        conn.close()

    log_enrollment(
        voter_id=voter_id,
        action="VOTE_CAST",
        details=f"Ballot successfully cast by {voter_id} ({voter['full_name']}) at {now_iso}.",
        ip_address=ip_address
    )

    return {
        "success": True,
        "message": "Your vote has been securely recorded and confirmed.",
        "receipt": {
            "voter_id": voter_id,
            "voter_name": voter['full_name'],
            "candidate_name": candidate['name'],
            "candidate_party": candidate['party'],
            "candidate_symbol": candidate['symbol_name'],
            "timestamp": now_iso
        }
    }
