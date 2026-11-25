import os
import uuid
import json
from datetime import datetime
from PIL import Image
import config
from database import get_db_connection, log_enrollment

# Try importing qrcode library
try:
    import qrcode
    QRCODE_LIB_AVAILABLE = True
except ImportError:
    QRCODE_LIB_AVAILABLE = False

def generate_voter_qr_token(voter_id: str) -> str:
    """
    Generates a secure, cryptographically random token for the voter.
    Does NOT expose Aadhaar, fingerprint, or raw biometric data.
    """
    random_part = uuid.uuid4().hex.upper()
    return f"VV-AUTH-{voter_id}-{random_part[:12]}"

def create_qr_image(token_payload: str, output_path: str):
    """
    Renders and saves a high-resolution QR code image.
    Uses qrcode library if available, with PIL fallback.
    """
    if QRCODE_LIB_AVAILABLE:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(token_payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
        img.save(output_path)
        return True
    else:
        # Fallback using OpenCV QRCodeEncoder and Pillow
        import cv2
        import numpy as np
        encoder = cv2.QRCodeEncoder_create()
        matrix = encoder.encode(token_payload)
        # Scale up matrix to high resolution
        scale = 12
        h, w = matrix.shape
        scaled = cv2.resize(matrix, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)
        # Invert: QR modules are 255 (white in OpenCV), background is 0 (black). We want dark on light.
        # In OpenCV matrix: 0 is white, 255 is black or vice-versa
        inv = 255 - scaled
        # Add quiet border
        border = 40
        bordered = cv2.copyMakeBorder(inv, border, border, border, border, cv2.BORDER_CONSTANT, value=255)
        cv2.imwrite(output_path, bordered)
        return True

def generate_and_save_voter_qr(voter_id: str):
    """
    Generates unique secure QR token, builds QR code image,
    stores in database, and updates voter enrollment status.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify voter exists
    cursor.execute("SELECT id, voter_id, full_name, face_status, fingerprint_status FROM voters WHERE voter_id = ?", (voter_id,))
    voter = cursor.fetchone()
    if not voter:
        conn.close()
        return {"success": False, "message": f"Voter ID '{voter_id}' not found."}

    # Generate token payload
    secure_token = generate_voter_qr_token(voter_id)
    payload_data = {
        "system": "VAULTVOTE-SMART-ELECTION-SYSTEM",
        "voter_id": voter_id,
        "auth_token": secure_token,
        "issued_at": datetime.now().isoformat(),
        "status": "VERIFIED_ENROLLMENT"
    }
    payload_str = json.dumps(payload_data)

    filename = f"{voter_id}_qr.png"
    qr_abs_path = os.path.join(config.QRCODES_DIR, filename)
    qr_rel_path = f"uploads/qrcodes/{filename}"

    # Generate and save image
    create_qr_image(payload_str, qr_abs_path)

    # Save to database
    cursor.execute("SELECT id FROM voter_qr_tokens WHERE voter_id = ?", (voter_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE voter_qr_tokens 
            SET qr_token = ?, qr_image_path = ?, generated_at = ?
            WHERE voter_id = ?
        ''', (secure_token, qr_rel_path, datetime.now().isoformat(), voter_id))
    else:
        cursor.execute('''
            INSERT INTO voter_qr_tokens (voter_id, qr_token, qr_image_path, generated_at)
            VALUES (?, ?, ?, ?)
        ''', (voter_id, secure_token, qr_rel_path, datetime.now().isoformat()))

    # Update voter qr_status
    cursor.execute('''
        UPDATE voters 
        SET qr_status = 'GENERATED', updated_at = ?
        WHERE voter_id = ?
    ''', (datetime.now().isoformat(), voter_id))

    # Check if registration is fully complete (Face Enrolled + FP Enrolled + QR Generated)
    cursor.execute("SELECT face_status, fingerprint_status FROM voters WHERE voter_id = ?", (voter_id,))
    v_status = cursor.fetchone()
    if v_status and v_status['face_status'] == 'ENROLLED' and v_status['fingerprint_status'] == 'ENROLLED':
        cursor.execute('''
            UPDATE voters 
            SET registration_status = 'COMPLETED', updated_at = ?
            WHERE voter_id = ?
        ''', (datetime.now().isoformat(), voter_id))
        is_completed = True
    else:
        is_completed = False

    conn.commit()
    conn.close()

    log_enrollment(
        voter_id=voter_id,
        action="QR_GENERATED",
        details=f"Secure QR Token issued: {secure_token[:18]}... Completed={is_completed}"
    )

    return {
        "success": True,
        "message": "QR CODE GENERATION SUCCESSFUL",
        "qr_token": secure_token,
        "qr_image_url": f"/static/{qr_rel_path}",
        "is_completed": is_completed
    }
