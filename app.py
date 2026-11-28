import os
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, Response, send_file, send_from_directory
)
from werkzeug.security import check_password_hash, generate_password_hash

import config
from database import (
    init_db, get_db_connection, log_enrollment,
    check_duplicate_aadhaar, check_duplicate_identity,
    get_dashboard_metrics, hash_aadhaar, mask_aadhaar,
    delete_voter, get_candidates, check_voter_voting_eligibility,
    cast_vote, get_election_results,
    get_sms_settings, save_sms_settings, get_sms_logs, get_sms_log_by_id
)
from sequence import get_next_voter_id, preview_next_voter_id
from face_service import (
    generate_webcam_stream, capture_and_save_face,
    verify_voter_face, FACE_RECOGNITION_AVAILABLE
)
from fingerprint_service import enroll_simulated_fingerprint
from qr_service import generate_and_save_voter_qr
from id_card_service import generate_voter_id_card_pdf
from location_service import lookup_district, lookup_pincode
from sms_service import send_vote_confirmation_sms, dispatch_sms

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Ensure database tables and initial seed data exist
init_db()

def admin_required(f):
    """Decorator to enforce admin authentication for protected views."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Authentication required. Please sign in as an Administrator.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- AUTHENTICATION ROUTES -----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('login.html', username=username)

        conn = get_db_connection()
        admin_user = conn.execute(
            "SELECT * FROM admin WHERE username = ?", (username,)
        ).fetchone()

        if admin_user and check_password_hash(admin_user['password_hash'], password):
            # Update last login timestamp
            conn.execute(
                "UPDATE admin SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), admin_user['id'])
            )
            conn.commit()
            conn.close()

            session['admin_logged_in'] = True
            session['admin_id'] = admin_user['id']
            session['admin_username'] = admin_user['username']
            session['admin_name'] = admin_user['full_name']

            log_enrollment(
                voter_id='SYSTEM',
                action='ADMIN_LOGIN',
                details=f"Admin '{username}' logged in successfully",
                ip_address=request.remote_addr or '127.0.0.1'
            )

            flash(f"Welcome back, {admin_user['full_name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            conn.close()
            flash("Invalid administrator credentials. Please verify and try again.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('admin_username', 'Unknown')
    session.clear()
    log_enrollment(
        voter_id='SYSTEM',
        action='ADMIN_LOGOUT',
        details=f"Admin '{username}' logged out",
        ip_address=request.remote_addr or '127.0.0.1'
    )
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('login'))

# ----------------- PUBLIC VOTING PORTAL (DEFAULT / LANDING) -----------------

@app.route('/')
def voting_portal():
    """
    Public Citizen-Facing Digital Voting Kiosk / EVM Booth.
    Displays the voting interface with active candidates and voter verification.
    """
    candidates = get_candidates()
    return render_template('voting.html', candidates=candidates)

# ----------------- ADMIN DASHBOARD -----------------

@app.route('/dashboard')
@admin_required
def dashboard():
    metrics = get_dashboard_metrics()
    next_preview_id = preview_next_voter_id()
    return render_template(
        'dashboard.html',
        metrics=metrics,
        next_preview_id=next_preview_id,
        face_engine="ArcFace 512-d (MobileFaceNet) + YuNet 5-Point Alignment"
    )

# ----------------- ELECTION RESULTS (ADMIN) -----------------

@app.route('/results')
@admin_required
def election_results():
    """
    Renders official election results dashboard for administrators.
    Displays live candidate vote tallies, percentages, victory margins, and turnout.
    """
    results = get_election_results()
    return render_template('election_results.html', results=results)

@app.route('/api/results')
@admin_required
def api_election_results():
    """
    JSON API returning live election results data for real-time polling or charts.
    """
    results = get_election_results()
    return jsonify({
        "success": True,
        "results": results
    })

# ----------------- VOTING KIOSK API ROUTES -----------------

@app.route('/api/voting/scan_qr', methods=['POST'])
def api_scan_qr():
    """Decodes QR code from webcam image frame or uploaded file using OpenCV."""
    import cv2
    import base64
    import numpy as np

    data = request.get_json(silent=True) or request.form
    image_data = data.get('image', '')
    img = None

    if not image_data:
        if 'file' in request.files:
            file = request.files['file']
            file_bytes = file.read()
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            return jsonify({"found": False, "message": "No image payload received."}), 400
    else:
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]
        try:
            raw_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(raw_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            return jsonify({"found": False, "message": f"Decode error: {e}"}), 400

    if img is None or img.size == 0:
        return jsonify({"found": False, "message": "Could not decode image frame."}), 400

    detector = cv2.QRCodeDetector()
    decoded_text, points, _ = detector.detectAndDecode(img)

    # Multi-pass enhancement pipeline to counter webcam blur, glare, and low contrast
    if not decoded_text:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
        
        # Pass 2: Unsharp masking (de-blur filter)
        gaussian = cv2.GaussianBlur(gray, (0, 0), 2.5)
        sharp = cv2.addWeighted(gray, 2.2, gaussian, -1.2, 0)
        decoded_text, points, _ = detector.detectAndDecode(sharp)

        # Pass 3: CLAHE adaptive contrast
        if not decoded_text:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl = clahe.apply(sharp)
            decoded_text, points, _ = detector.detectAndDecode(cl)

        # Pass 4: Otsu binarization
        if not decoded_text:
            _, otsu = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            decoded_text, points, _ = detector.detectAndDecode(otsu)

        # Pass 5: Adaptive Gaussian threshold
        if not decoded_text:
            adapt = cv2.adaptiveThreshold(sharp, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 5)
            decoded_text, points, _ = detector.detectAndDecode(adapt)

        # Pass 6: Upscaling for small/distant QR codes
        if not decoded_text:
            h, w = gray.shape[:2]
            if max(h, w) < 1200:
                up = cv2.resize(sharp, (int(w * 1.5), int(h * 1.5)), interpolation=cv2.INTER_CUBIC)
                decoded_text, points, _ = detector.detectAndDecode(up)

    if decoded_text:
        return jsonify({
            "found": True,
            "token": decoded_text,
            "has_points": points is not None
        })
    else:
        return jsonify({"found": False, "message": "No QR code detected in frame."})

@app.route('/api/voting/verify_voter', methods=['POST'])
def api_verify_voter():
    """Verifies voter eligibility using Voter ID or QR token."""
    data = request.get_json(silent=True) or request.form
    voter_identifier = data.get('voter_id', '').strip()
    if not voter_identifier:
        return jsonify({"eligible": False, "reason": "Please provide a valid Voter ID or QR code token."}), 400
        
    res = check_voter_voting_eligibility(voter_identifier)
    return jsonify(res)

@app.route('/api/voting/verify_biometric/<voter_id>', methods=['POST'])
def api_verify_biometric(voter_id):
    """Verifies face or simulated fingerprint during voting booth authentication."""
    data = request.get_json(silent=True) or request.form
    method = data.get('method', 'face')
    
    if method == 'fingerprint':
        conn = get_db_connection()
        fp = conn.execute("SELECT * FROM fingerprint_biometrics WHERE voter_id = ?", (voter_id,)).fetchone()
        conn.close()
        if fp:
            return jsonify({
                "match": True,
                "confidence": 0.98,
                "simulated": True,
                "message": f"FINGERPRINT VERIFIED: Match confirmed with template {fp['pattern_type']} ({fp['minutiae_count']} minutiae points)."
            })
        else:
            return jsonify({
                "match": False,
                "confidence": 0.0,
                "simulated": True,
                "message": "No registered fingerprint template found for this voter."
            }), 400
            
    # Face verification
    img_data = data.get('image')
    res = verify_voter_face(voter_id, img_data)
    return jsonify(res)

@app.route('/api/voting/manual_override/<voter_id>', methods=['POST'])
def api_manual_override(voter_id):
    """
    Manual identity verification override route by Presiding/Polling Officer.
    Provides an authorized alternative path for genuine voters who experience false rejection
    (e.g., facial trauma, severe cataracts, elderly voters, webcam hardware issues).
    """
    data = request.get_json(silent=True) or request.form
    officer_pin = str(data.get('officer_pin', '')).strip()
    reason = data.get('reason', 'Presiding Officer physical verification under ECI Rule 49V').strip()

    # Verify officer pin / credentials (admin pin '123' or 'admin')
    if officer_pin not in ['123', 'admin']:
        return jsonify({
            "success": False,
            "match": False,
            "message": "Invalid Polling Officer PIN. Authorization denied."
        }), 403

    conn = get_db_connection()
    voter = conn.execute("SELECT * FROM voters WHERE voter_id = ?", (voter_id,)).fetchone()
    conn.close()

    if not voter:
        return jsonify({
            "success": False,
            "match": False,
            "message": f"Voter '{voter_id}' not found in electoral registry."
        }), 404

    # Log the manual override audit trail
    log_enrollment(
        voter_id=voter_id,
        action="POLLING_OFFICER_MANUAL_OVERRIDE",
        details=f"Manual identity verification approved by Election Official. Reason: {reason}",
        ip_address=request.remote_addr or '127.0.0.1'
    )

    return jsonify({
        "success": True,
        "match": True,
        "manual_override": True,
        "confidence": 1.0,
        "face_detected": True,
        "simulated": False,
        "message": f"MANUAL IDENTITY VERIFIED: Polling Officer approved voter identity ({reason})."
    })

@app.route('/api/voting/cast_vote', methods=['POST'])
def api_cast_vote():
    """Casts secret electronic ballot for verified voter."""
    data = request.get_json(silent=True) or request.form
    voter_id = data.get('voter_id', '').strip()
    candidate_id = data.get('candidate_id')
    
    if not voter_id or not candidate_id:
        return jsonify({"success": False, "message": "Missing voter ID or candidate selection."}), 400
        
    try:
        cand_id_int = int(candidate_id)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid candidate ID format."}), 400

    ip_addr = request.remote_addr or '127.0.0.1'
    res = cast_vote(voter_id, cand_id_int, ip_address=ip_addr)
    if res['success']:
        voter_mobile = res['receipt'].pop('voter_mobile', '')
        allow_live_test = bool(app.config.get('SMS_TEST_FORCE_LIVE'))
        sms_res = send_vote_confirmation_sms(
            res['receipt'],
            voter_mobile=voter_mobile,
            ip_address=ip_addr,
            is_testing=bool(app.testing and not allow_live_test),
            force_live=allow_live_test
        )
        public_sms_summary = {
            'success': sms_res['success'],
            'status': sms_res['status'],
            'provider': sms_res['provider'],
            'masked_phone': sms_res['masked_phone'],
            'receipt_ref': sms_res['receipt_ref'],
            'message_preview': sms_res['message_preview'],
            'delivered_live': sms_res['delivered_live'],
            'simulated': sms_res['simulated'],
            'error': sms_res['error']
        }
        res['sms'] = public_sms_summary
        res['receipt']['sms'] = public_sms_summary
    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code

# ----------------- VOTER REGISTRATION FLOW -----------------

@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register_voter():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        dob = request.form.get('dob', '').strip()
        father_name = request.form.get('father_name', '').strip()
        gender = request.form.get('gender', '').strip()
        aadhaar_raw = request.form.get('aadhaar', '').strip()
        mobile = request.form.get('mobile', '').strip()
        address = request.form.get('address', '').strip()
        district = request.form.get('district', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()

        # Clean digits
        aadhaar_digits = ''.join(filter(str.isdigit, aadhaar_raw))
        mobile_digits = ''.join(filter(str.isdigit, mobile))
        pincode_digits = ''.join(filter(str.isdigit, pincode))

        # Basic form validations
        errors = []
        if not full_name:
            errors.append("Full Name is required.")
        if not dob:
            errors.append("Date of Birth is required.")
        if not father_name:
            errors.append("Father's Name is required.")
        if not gender:
            errors.append("Gender is required.")
        if len(aadhaar_digits) != 12:
            errors.append("Aadhaar Number must be exactly 12 digits (synthetic test format).")
        if len(mobile_digits) != 10:
            errors.append("Mobile Number must be 10 digits.")
        if len(pincode_digits) != 6:
            errors.append("Pincode must be 6 digits.")
        if not address or not district or not state:
            errors.append("Complete address fields (Address, District, State) are required.")

        # Calculate and validate age
        age = 0
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
            today = datetime.now().date()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            if age < 18:
                errors.append(f"Voter must be at least 18 years old to register. Calculated age: {age} years.")
        except Exception:
            errors.append("Invalid Date of Birth format. Please use YYYY-MM-DD.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                'register_voter.html',
                form=request.form,
                next_id=preview_next_voter_id()
            )

        # ----------------- DUPLICATE DETECTION -----------------
        # 1. Check duplicate Aadhaar
        existing_aadhaar = check_duplicate_aadhaar(aadhaar_digits)
        if existing_aadhaar:
            return render_template(
                'duplicate_alert.html',
                reason='Aadhaar Number',
                duplicate_val=mask_aadhaar(aadhaar_digits),
                existing_voter=existing_aadhaar,
                form=request.form
            )

        # 2. Check duplicate Name + DOB or Mobile
        existing_identity = check_duplicate_identity(full_name, dob, mobile_digits)
        if existing_identity:
            return render_template(
                'duplicate_alert.html',
                reason='Name and Date of Birth / Mobile Record',
                duplicate_val=f"{full_name} ({dob})",
                existing_voter=existing_identity,
                form=request.form
            )

        # ----------------- GENERATE VOTER ID & ENROLL -----------------
        new_voter_id = get_next_voter_id()
        a_hash = hash_aadhaar(aadhaar_digits)
        a_masked = mask_aadhaar(aadhaar_digits)

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                face_status, fingerprint_status, qr_status, registration_status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 'PENDING', 'PENDING', 'INCOMPLETE', ?, ?)
        ''', (
            new_voter_id, full_name, dob, age, gender, father_name,
            a_hash, a_masked, mobile_digits, address, district, state, pincode_digits,
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

        log_enrollment(
            voter_id=new_voter_id,
            action="PERSONAL_DETAILS_SAVED",
            details=f"Voter {full_name} enrolled. Generated Voter ID: {new_voter_id}",
            ip_address=request.remote_addr or '127.0.0.1'
        )

        flash(f"Personal details registered! Voter ID {new_voter_id} generated. Proceed with Biometric Registration.", "success")
        return redirect(url_for('biometric_enrollment', voter_id=new_voter_id))

    return render_template('register_voter.html', form={}, next_id=preview_next_voter_id())

@app.route('/biometric/<voter_id>')
@admin_required
def biometric_enrollment(voter_id):
    conn = get_db_connection()
    voter = conn.execute('''
        SELECT v.*, fb.photo_path, fp.simulated_reference, fp.pattern_type, qr.qr_token
        FROM voters v
        LEFT JOIN face_biometrics fb ON v.voter_id = fb.voter_id
        LEFT JOIN fingerprint_biometrics fp ON v.voter_id = fp.voter_id
        LEFT JOIN voter_qr_tokens qr ON v.voter_id = qr.voter_id
        WHERE v.voter_id = ?
    ''', (voter_id,)).fetchone()
    conn.close()

    if not voter:
        flash(f"Voter with ID '{voter_id}' does not exist.", "danger")
        return redirect(url_for('registered_voters'))

    return render_template('biometric_enroll.html', voter=dict(voter))

# ----------------- LIVE WEBCAM VIDEO STREAM -----------------

@app.route('/video_feed')
@admin_required
def video_feed():
    """Streams live MJPEG frames with real-time OpenCV face detection bounding boxes."""
    return Response(
        generate_webcam_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# ----------------- BIOMETRIC API ENDPOINTS -----------------

@app.route('/api/face/capture/<voter_id>', methods=['POST'])
@admin_required
def api_capture_face(voter_id):
    """Captures face photograph, extracts face encoding, and saves to database."""
    req_json = request.get_json(silent=True) or {}
    image_base64 = req_json.get('image_base64', None)

    result = capture_and_save_face(voter_id, image_base64)
    return jsonify(result), (200 if result.get('success') else 400)

@app.route('/api/fingerprint/enroll/<voter_id>', methods=['POST'])
@admin_required
def api_enroll_fingerprint(voter_id):
    """Enrolls simulated fingerprint biometric template."""
    result = enroll_simulated_fingerprint(voter_id)
    return jsonify(result), (200 if result.get('success') else 400)

@app.route('/api/finalize/<voter_id>', methods=['POST'])
@admin_required
def api_finalize_registration(voter_id):
    """Generates QR code, generates Voter ID Card PDF, and marks voter COMPLETED."""
    qr_result = generate_and_save_voter_qr(voter_id)
    if not qr_result.get('success'):
        return jsonify(qr_result), 400

    try:
        card_pdf_rel = generate_voter_id_card_pdf(voter_id)
    except Exception as e:
        return jsonify({"success": False, "message": f"PDF Card generation error: {str(e)}"}), 500

    return jsonify({
        "success": True,
        "message": "REGISTRATION COMPLETED SUCCESSFULLY",
        "qr_image_url": qr_result.get('qr_image_url'),
        "card_pdf_url": f"/static/{card_pdf_rel}",
        "redirect_url": url_for('view_voter_card', voter_id=voter_id)
    })

# ----------------- VOTER ID CARD VIEWS & DOWNLOADS -----------------

@app.route('/voter/card/<voter_id>')
@admin_required
def view_voter_card(voter_id):
    conn = get_db_connection()
    voter = conn.execute('''
        SELECT v.*, fb.photo_path, fp.simulated_reference, fp.pattern_type, qr.qr_token, qr.qr_image_path
        FROM voters v
        LEFT JOIN face_biometrics fb ON v.voter_id = fb.voter_id
        LEFT JOIN fingerprint_biometrics fp ON v.voter_id = fp.voter_id
        LEFT JOIN voter_qr_tokens qr ON v.voter_id = qr.voter_id
        WHERE v.voter_id = ?
    ''', (voter_id,)).fetchone()
    conn.close()

    if not voter:
        flash(f"Voter ID '{voter_id}' not found.", "danger")
        return redirect(url_for('registered_voters'))

    # If card image or PDF doesn't exist yet, generate on demand
    pdf_filename = f"{voter_id}_card.pdf"
    pdf_abs_path = os.path.join(config.CARDS_DIR, pdf_filename)
    png_filename = f"{voter_id}_card.png"
    png_abs_path = os.path.join(config.CARDS_DIR, png_filename)
    if not os.path.exists(pdf_abs_path) or not os.path.exists(png_abs_path):
        try:
            generate_voter_id_card_pdf(voter_id)
        except Exception as e:
            print(f"Error generating card on demand: {e}")

    return render_template('voter_card.html', voter=dict(voter))

@app.route('/voter/card/<voter_id>/download')
@admin_required
def download_voter_card(voter_id):
    """Downloads official generated PDF Voter ID Card."""
    pdf_filename = f"{voter_id}_card.pdf"
    pdf_abs_path = os.path.join(config.CARDS_DIR, pdf_filename)

    if not os.path.exists(pdf_abs_path):
        try:
            generate_voter_id_card_pdf(voter_id)
        except Exception as e:
            flash(f"Error generating PDF card: {str(e)}", "danger")
            return redirect(url_for('view_voter_card', voter_id=voter_id))

    return send_file(
        pdf_abs_path,
        as_attachment=True,
        download_name=f"VaultVote_VoterID_{voter_id}.pdf",
        mimetype="application/pdf"
    )

@app.route('/voter/qr/<voter_id>/download')
@admin_required
def download_voter_qr(voter_id):
    """Downloads generated QR code image."""
    qr_filename = f"{voter_id}_qr.png"
    qr_abs_path = os.path.join(config.QRCODES_DIR, qr_filename)

    if not os.path.exists(qr_abs_path):
        generate_and_save_voter_qr(voter_id)

    return send_file(
        qr_abs_path,
        as_attachment=True,
        download_name=f"VaultVote_QR_{voter_id}.png",
        mimetype="image/png"
    )

# ----------------- VOTER MANAGEMENT & SEARCH -----------------

@app.route('/voters')
@admin_required
def registered_voters():
    search_q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    conn = get_db_connection()
    query = '''
        SELECT v.*, fb.photo_path, qr.qr_token
        FROM voters v
        LEFT JOIN face_biometrics fb ON v.voter_id = fb.voter_id
        LEFT JOIN voter_qr_tokens qr ON v.voter_id = qr.voter_id
        WHERE 1=1
    '''
    params = []

    if search_q:
        query += ''' AND (
            v.voter_id LIKE ? OR
            v.full_name LIKE ? OR
            v.mobile LIKE ? OR
            v.district LIKE ?
        )'''
        wildcard = f"%{search_q}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if status_filter:
        query += ' AND v.registration_status = ?'
        params.append(status_filter)

    query += ' ORDER BY v.id DESC'
    voters = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        'registered_voters.html',
        voters=[dict(v) for v in voters],
        search_q=search_q,
        status_filter=status_filter
    )

@app.route('/voter/delete/<voter_id>', methods=['POST'])
@admin_required
def delete_voter_route(voter_id):
    """Permanently deletes a voter record and associated biometrics, cards, and files."""
    admin_name = session.get('admin_name', 'Admin')
    res = delete_voter(voter_id, admin_name=admin_name)
    if res['success']:
        flash(res['message'], "success")
    else:
        flash(res['message'], "danger")

    redirect_target = request.referrer or url_for('registered_voters')
    if f"/voter/card/{voter_id}" in redirect_target or f"/biometric/{voter_id}" in redirect_target:
        redirect_target = url_for('registered_voters')
    return redirect(redirect_target)

@app.route('/api/voter/delete/<voter_id>', methods=['POST', 'DELETE'])
@admin_required
def api_delete_voter(voter_id):
    """API endpoint to delete a voter record."""
    admin_name = session.get('admin_name', 'Admin')
    res = delete_voter(voter_id, admin_name=admin_name)
    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code

@app.route('/search')
@admin_required
def search_voter():
    search_query = request.args.get('query', '').strip()
    result = None
    searched = False

    if search_query:
        searched = True
        conn = get_db_connection()
        # Search by voter_id, synthetic Aadhaar, or full name
        a_hash = hash_aadhaar(search_query) if search_query.isdigit() else None
        
        row = conn.execute('''
            SELECT v.*, fb.photo_path, fb.confidence_score, 
                   fp.simulated_reference, fp.pattern_type, fp.minutiae_count,
                   qr.qr_token, qr.qr_image_path
            FROM voters v
            LEFT JOIN face_biometrics fb ON v.voter_id = fb.voter_id
            LEFT JOIN fingerprint_biometrics fp ON v.voter_id = fp.voter_id
            LEFT JOIN voter_qr_tokens qr ON v.voter_id = qr.voter_id
            WHERE v.voter_id = ? OR v.aadhaar_hash = ? OR LOWER(v.full_name) = LOWER(?) OR v.mobile = ?
        ''', (search_query.upper(), a_hash or '', search_query, search_query)).fetchone()
        conn.close()

        if row:
            result = dict(row)

    return render_template('search_voter.html', query=search_query, result=result, searched=searched)

@app.route('/logs')
@admin_required
def audit_logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM enrollment_logs ORDER BY id DESC LIMIT 100').fetchall()
    conn.close()
    return render_template('audit_logs.html', logs=[dict(l) for l in logs])

# ----------------- SMS NOTIFICATIONS & GATEWAY SETTINGS -----------------

@app.route('/sms-notifications', methods=['GET', 'POST'])
@admin_required
def sms_notifications():
    """Admin view for SMS gateway settings, test dispatch, and vote SMS logs."""
    if request.method == 'POST':
        updated = save_sms_settings({
            'enabled': request.form.get('enabled') == 'on',
            'provider': request.form.get('provider', 'simulation'),
            'country_code': request.form.get('country_code', '+91'),
            'twilio_account_sid': request.form.get('twilio_account_sid', ''),
            'twilio_auth_token': request.form.get('twilio_auth_token', ''),
            'twilio_from_number': request.form.get('twilio_from_number', ''),
            'fast2sms_api_key': request.form.get('fast2sms_api_key', ''),
            'fast2sms_route': request.form.get('fast2sms_route', 'q'),
            'webhook_url': request.form.get('webhook_url', ''),
            'webhook_token': request.form.get('webhook_token', '')
        })
        log_enrollment(
            voter_id='SYSTEM',
            action='SMS_SETTINGS_UPDATED',
            details=f"Admin updated SMS Gateway provider to '{updated['provider'].upper()}' (Enabled: {updated['enabled']}).",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        flash(f"SMS Gateway configuration saved (Active provider: {updated['provider'].upper()}).", "success")
        return redirect(url_for('sms_notifications'))

    settings = get_sms_settings()
    logs = get_sms_logs(limit=100)
    secret_hints = {
        'twilio_auth_token': ('••••' + settings['twilio_auth_token'][-4:]) if len(settings.get('twilio_auth_token', '')) >= 4 else ('Configured' if settings.get('twilio_auth_token') else ''),
        'fast2sms_api_key': ('••••' + settings['fast2sms_api_key'][-4:]) if len(settings.get('fast2sms_api_key', '')) >= 4 else ('Configured' if settings.get('fast2sms_api_key') else ''),
        'webhook_token': ('••••' + settings['webhook_token'][-4:]) if len(settings.get('webhook_token', '')) >= 4 else ('Configured' if settings.get('webhook_token') else ''),
    }
    stats = {
        'total': len(logs),
        'sent': sum(1 for row in logs if row['status'] == 'SENT'),
        'simulated': sum(1 for row in logs if row['status'] == 'SIMULATED'),
        'failed': sum(1 for row in logs if row['status'] == 'FAILED')
    }
    return render_template(
        'sms_notifications.html',
        settings=settings,
        secret_hints=secret_hints,
        logs=logs,
        stats=stats
    )

@app.route('/api/sms/test', methods=['POST'])
@admin_required
def api_test_sms():
    """Sends a test phone SMS from the Admin portal to verify gateway credentials."""
    data = request.get_json(silent=True) or request.form
    phone = str(data.get('phone', '')).strip()
    custom_msg = str(data.get('message', '')).strip()
    digits = ''.join(ch for ch in phone if ch.isdigit())

    if len(digits) < 10:
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit phone number.'}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = custom_msg or (
        f"VaultVote ECI Test Alert: SMS gateway verification successful at {now_str}. "
        f"Voters will receive vote confirmations on their registered mobile numbers."
    )
    allow_live_test = bool(app.config.get('SMS_TEST_FORCE_LIVE'))
    res = dispatch_sms(
        phone=phone,
        message_body=body,
        voter_id='ADMIN_TEST',
        is_testing=bool(app.testing and not allow_live_test),
        force_live=allow_live_test,
        ip_address=request.remote_addr or '127.0.0.1'
    )
    status_code = 200 if res['success'] else 502
    return jsonify(res), status_code

@app.route('/api/sms/resend/<int:log_id>', methods=['POST'])
@admin_required
def api_resend_sms(log_id):
    """Retries dispatching an existing SMS notification record."""
    log_row = get_sms_log_by_id(log_id)
    if not log_row:
        return jsonify({'success': False, 'message': 'SMS log record not found.'}), 404

    allow_live_test = bool(app.config.get('SMS_TEST_FORCE_LIVE'))
    res = dispatch_sms(
        phone=log_row['phone_number'],
        message_body=log_row['message_body'],
        voter_id=log_row['voter_id'],
        receipt_ref=log_row.get('receipt_ref', ''),
        is_testing=bool(app.testing and not allow_live_test),
        force_live=allow_live_test,
        ip_address=request.remote_addr or '127.0.0.1'
    )
    status_code = 200 if res['success'] else 502
    return jsonify(res), status_code

# ----------------- ASYNC DUPLICATE CHECK API -----------------

@app.route('/api/check_duplicate', methods=['POST'])
@admin_required
def api_check_duplicate():
    """Real-time duplicate check as the admin fills out the registration form."""
    data = request.get_json(silent=True) or {}
    aadhaar = data.get('aadhaar', '').strip()
    mobile = data.get('mobile', '').strip()
    full_name = data.get('full_name', '').strip()
    dob = data.get('dob', '').strip()

    if aadhaar and len(''.join(filter(str.isdigit, aadhaar))) == 12:
        dup = check_duplicate_aadhaar(aadhaar)
        if dup:
            return jsonify({
                "duplicate": True,
                "field": "Aadhaar Number",
                "message": f"Duplicate Aadhaar! Registered under Voter ID: {dup['voter_id']} ({dup['full_name']})",
                "existing_voter": dup
            })

    if full_name and dob and mobile:
        dup = check_duplicate_identity(full_name, dob, mobile)
        if dup:
            return jsonify({
                "duplicate": True,
                "field": "Name/DOB/Mobile",
                "message": f"Potential Duplicate! Found matching record: {dup['voter_id']} ({dup['full_name']})",
                "existing_voter": dup
            })

    return jsonify({"duplicate": False})

# ----------------- LOCATION AUTO-LOOKUP API -----------------

@app.route('/api/lookup_location', methods=['GET', 'POST'])
def api_lookup_location():
    """
    Auto-detects State and default PIN code when a District is typed,
    or auto-detects District and State when a PIN code is typed.
    """
    query = request.args.get('district') or request.args.get('query') or ''
    pincode = request.args.get('pincode') or ''
    
    if request.is_json:
        data = request.get_json(silent=True) or {}
        query = query or data.get('district', '') or data.get('query', '')
        pincode = pincode or data.get('pincode', '')

    if query:
        match = lookup_district(query)
        if match:
            return jsonify({
                "found": True,
                "district": match['district'],
                "state": match['state'],
                "pincode": match['pincode']
            })

    if pincode:
        match = lookup_pincode(pincode)
        if match:
            return jsonify({
                "found": True,
                "district": match['district'],
                "state": match['state'],
                "pincode": match['pincode']
            })

    return jsonify({"found": False, "message": "Location not found in database"})

if __name__ == '__main__':
    print("=" * 65)
    print("  VAULTVOTE - SMART BIOMETRIC VOTING SYSTEM (ADMIN MODULE)")
    print("  Running locally on Windows laptop (No external hardware required)")
    print("  Access dashboard: http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host='127.0.0.1', port=5000, debug=True)
