import os
import sys
import unittest
import json
import random
import time
import numpy as np
import cv2

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import config
from app import app
from database import (
    init_db, get_db_connection, check_duplicate_aadhaar,
    check_duplicate_identity, get_dashboard_metrics, hash_aadhaar,
    delete_voter
)
from sequence import get_next_voter_id, preview_next_voter_id
from face_service import compute_face_encoding, capture_and_save_face, verify_voter_face
from fingerprint_service import enroll_simulated_fingerprint
from qr_service import generate_and_save_voter_qr
from id_card_service import generate_voter_id_card_pdf

def random_aadhaar():
    """Generates a random 12-digit synthetic test Aadhaar."""
    return f"{random.randint(100000000000, 999999999999)}"

def random_mobile():
    """Generates a random 10-digit mobile number."""
    return f"9{random.randint(100000000, 999999999)}"

class TestVaultVoteSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orig_db = config.DB_PATH
        cls.test_db = os.path.join(config.BASE_DIR, 'test_vaultvote.db')
        config.DB_PATH = cls.test_db
        if os.path.exists(cls.test_db):
            try:
                os.remove(cls.test_db)
            except Exception:
                pass
        init_db()
        app.testing = True
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        config.DB_PATH = cls.orig_db
        if os.path.exists(cls.test_db):
            try:
                os.remove(cls.test_db)
            except Exception:
                pass

    def test_01_database_and_admin_seed(self):
        """Verifies database tables exist and default admin is seeded."""
        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM admin WHERE username = ?", (config.DEFAULT_ADMIN_USERNAME,)).fetchone()
        conn.close()
        self.assertIsNotNone(admin, "Default admin should exist in database.")
        self.assertEqual(admin['username'], 'admin')
        print("\n[PASS] Database tables and Admin seed verified.")

    def test_02_voter_id_sequence_generation(self):
        """Verifies voter ID format WRM2745001, WRM2745002 incrementing properly."""
        id1 = get_next_voter_id()
        id2 = get_next_voter_id()
        self.assertTrue(id1.startswith('WRM2745'))
        self.assertTrue(id2.startswith('WRM2745'))
        num1 = int(id1.replace('WRM2745', ''))
        num2 = int(id2.replace('WRM2745', ''))
        self.assertEqual(num2, num1 + 1, "Voter ID sequence must strictly auto-increment.")
        print(f"[PASS] Sequence generator verified: {id1} -> {id2}")

    def test_03_duplicate_detection(self):
        """Verifies that duplicate Aadhaar numbers and identities are correctly caught and prevented."""
        test_aadhaar = random_aadhaar()
        voter_id = get_next_voter_id()
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                created_at, updated_at
            ) VALUES (?, 'Test Duplicate Voter', '1995-05-10', 29, 'Male', 'Test Father',
                ?, ?, ?, 'Test Street', 'Bangalore', 'Karnataka', '560001',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        # Check duplicate lookup
        dup = check_duplicate_aadhaar(test_aadhaar)
        self.assertIsNotNone(dup, "Duplicate Aadhaar should be detected.")
        self.assertEqual(dup['voter_id'], voter_id)
        print(f"[PASS] Duplicate Aadhaar successfully caught! Associated Voter ID: {dup['voter_id']}")

    def test_04_face_encoding_and_capture(self):
        """Verifies OpenCV face encoding and saving photo for a voter."""
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                created_at, updated_at
            ) VALUES (?, 'Face Test Voter', '2000-01-01', 24, 'Female', 'Father A',
                ?, ?, ?, 'Test Lane', 'Delhi', 'Delhi', '110001',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        # Use genuine enrolled face sample photo if available
        sample_path = os.path.join(config.STATIC_DIR, 'uploads', 'faces', 'WRM2745017_face.jpg')
        if os.path.exists(sample_path):
            test_frame = cv2.imread(sample_path)
        else:
            test_frame = np.full((480, 640, 3), 180, dtype=np.uint8)

        _, buf = cv2.imencode('.jpg', test_frame)
        res = capture_and_save_face(voter_id, buf.tobytes())
        self.assertTrue(res['success'], f"Face capture failed: {res.get('message')}")
        self.assertEqual(res['message'], "FACE REGISTRATION SUCCESSFUL")
        print(f"[PASS] Face capture and encoding verified: {res['message']} (Confidence: {res['confidence']})")

    def test_05_simulated_fingerprint_enrollment(self):
        """Verifies simulated fingerprint template generation and duplicate prevention."""
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                created_at, updated_at
            ) VALUES (?, 'FP Test Voter', '1998-08-15', 26, 'Male', 'Father B',
                ?, ?, ?, 'Test Road', 'Chennai', 'Tamil Nadu', '600001',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        res = enroll_simulated_fingerprint(voter_id)
        self.assertTrue(res['success'], f"Fingerprint enrollment failed: {res.get('message')}")
        self.assertTrue(res['reference'].startswith('FPSIM-'))
        self.assertTrue(res['is_simulated'])
        print(f"[PASS] Simulated fingerprint verified: {res['reference']} ({res['pattern_type']}, Minutiae: {res['minutiae_count']})")

    def test_06_qr_and_voter_card_generation(self):
        """Verifies QR token creation and official PDF Voter ID card generation."""
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                face_status, fingerprint_status, created_at, updated_at
            ) VALUES (?, 'Card Test Voter', '1992-12-04', 31, 'Female', 'Father C',
                ?, ?, ?, 'Koramangala', 'Bangalore', 'Karnataka', '560034',
                'ENROLLED', 'ENROLLED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        # Enroll simulated fingerprint
        enroll_simulated_fingerprint(voter_id)

        # Generate QR
        qr_res = generate_and_save_voter_qr(voter_id)
        self.assertTrue(qr_res['success'])
        qr_file = os.path.join(config.STATIC_DIR, qr_res['qr_image_url'].replace('/static/', ''))
        self.assertTrue(os.path.exists(qr_file))
        print(f"[PASS] QR Code generation verified: {qr_res['qr_token']}")

        # Generate PDF Card
        pdf_rel = generate_voter_id_card_pdf(voter_id)
        pdf_abs = os.path.join(config.STATIC_DIR, pdf_rel)
        self.assertTrue(os.path.exists(pdf_abs), "PDF Voter ID Card file must exist on disk.")
        self.assertGreater(os.path.getsize(pdf_abs), 1000, "PDF file must not be empty.")
        print(f"[PASS] PDF Voter ID Card generated: {pdf_abs} ({os.path.getsize(pdf_abs)} bytes)")

    def test_07_flask_end_to_end_web_flow(self):
        """Simulates full admin web interaction: login, register, duplicate check, card view."""
        # 1. Login
        login_res = self.client.post('/login', data={
            'username': 'admin',
            'password': '123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Dashboard', login_res.data)
        print("[PASS] Admin Login via Web Client successful.")

        # 2. Register Voter via POST with unique synthetic identity
        test_aadhaar = random_aadhaar()
        unique_name = f"E2E Web Voter {random.randint(10000, 99999)}"
        unique_mobile = random_mobile()
        
        reg_res = self.client.post('/register', data={
            'full_name': unique_name,
            'dob': '2001-07-20',
            'father_name': 'E2E Father',
            'gender': 'Male',
            'aadhaar': test_aadhaar,
            'mobile': unique_mobile,
            'address': 'MG Road Apt 4B',
            'district': 'Mysore',
            'state': 'Karnataka',
            'pincode': '570001'
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)
        self.assertIn(b'Biometric Enrollment', reg_res.data)
        print("[PASS] Full web voter enrollment form submission successful.")

        # 3. Test Duplicate Aadhaar Submission is Blocked
        dup_res = self.client.post('/register', data={
            'full_name': 'Another Person',
            'dob': '1999-01-01',
            'father_name': 'Another Father',
            'gender': 'Female',
            'aadhaar': test_aadhaar,  # Same synthetic Aadhaar
            'mobile': random_mobile(),
            'address': 'Some Address',
            'district': 'Mysore',
            'state': 'Karnataka',
            'pincode': '570001'
        }, follow_redirects=True)
        self.assertIn(b'Existing Voter Record Detected', dup_res.data)
        print("[PASS] Duplicate voter registration blocked by web flow as expected.")

    def test_08_delete_voter_flow(self):
        """Verifies voter deletion via backend service and web route."""
        # 1. Create a voter to delete
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                registration_status, created_at, updated_at
            ) VALUES (?, 'Voter To Delete', '1990-01-01', 34, 'Male', 'Father Delete',
                ?, ?, ?, 'Delete St', 'Chennai', 'Tamil Nadu', '600001',
                'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        # Enroll fingerprint and QR so child records exist
        enroll_simulated_fingerprint(voter_id)
        generate_and_save_voter_qr(voter_id)

        # 2. Delete via route
        del_res = self.client.post(f'/voter/delete/{voter_id}', follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)

        # Verify voter is gone from database
        conn = get_db_connection()
        v = conn.execute('SELECT * FROM voters WHERE voter_id = ?', (voter_id,)).fetchone()
        fp = conn.execute('SELECT * FROM fingerprint_biometrics WHERE voter_id = ?', (voter_id,)).fetchone()
        qr = conn.execute('SELECT * FROM voter_qr_tokens WHERE voter_id = ?', (voter_id,)).fetchone()
        log = conn.execute("SELECT * FROM enrollment_logs WHERE voter_id = ? AND action = 'VOTER_DELETED'", (voter_id,)).fetchone()
        conn.close()

        self.assertIsNone(v, "Voter must be deleted from voters table.")
        self.assertIsNone(fp, "Child fingerprint record must be deleted.")
        self.assertIsNone(qr, "Child QR token record must be deleted.")
        self.assertIsNotNone(log, "Audit log for deletion must exist.")
        print(f"[PASS] Voter deletion verified: {voter_id} successfully deleted with all child records and audit log.")

    def test_09_voting_portal_and_evm_flow(self):
        """Verifies public voting kiosk landing page, voter eligibility check, biometric match, and ballot casting."""
        # 1. Verify GET / renders Voting Kiosk without login
        kiosk_res = self.client.get('/')
        self.assertEqual(kiosk_res.status_code, 200)
        self.assertIn(b'Digital Voting Kiosk', kiosk_res.data)
        self.assertIn(b'Admin Portal', kiosk_res.data)
        print("\n[PASS] Public Voting Kiosk landing page verified at root URL (/).")

        # 2. Setup verified enrolled voter
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                face_status, fingerprint_status, qr_status, registration_status,
                created_at, updated_at
            ) VALUES (?, 'Voting Test Citizen', '1998-05-15', 28, 'Female', 'Father Vote',
                ?, ?, ?, 'EVM Booth Street', 'Madurai', 'Tamil Nadu', '625001',
                'ENROLLED', 'ENROLLED', 'ISSUED', 'COMPLETED',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        # Enroll fingerprint
        enroll_simulated_fingerprint(voter_id)

        # 3. Check Eligibility API
        chk_res = self.client.post('/api/voting/verify_voter', json={'voter_id': voter_id})
        self.assertEqual(chk_res.status_code, 200)
        chk_data = json.loads(chk_res.data)
        self.assertTrue(chk_data['eligible'])
        self.assertEqual(chk_data['voter']['voter_id'], voter_id)
        print(f"[PASS] Voter verification API verified for {voter_id}.")

        # 4. Check Biometric Verification API
        bio_res = self.client.post(f'/api/voting/verify_biometric/{voter_id}', json={'method': 'fingerprint'})
        self.assertEqual(bio_res.status_code, 200)
        bio_data = json.loads(bio_res.data)
        self.assertTrue(bio_data['match'])
        print(f"[PASS] Biometric verification API verified: {bio_data['message']}")

        # 5. Cast Ballot
        cast_res = self.client.post('/api/voting/cast_vote', json={'voter_id': voter_id, 'candidate_id': 1})
        self.assertEqual(cast_res.status_code, 200)
        cast_data = json.loads(cast_res.data)
        self.assertTrue(cast_data['success'])
        self.assertIn("Vijay", cast_data['receipt']['candidate_name'])
        print(f"[PASS] EVM Ballot cast verified for {voter_id} -> {cast_data['receipt']['candidate_name']}.")

        # 6. Verify Duplicate Vote is Blocked
        dup_res = self.client.post('/api/voting/cast_vote', json={'voter_id': voter_id, 'candidate_id': 2})
        self.assertEqual(dup_res.status_code, 400)
        dup_data = json.loads(dup_res.data)
        self.assertFalse(dup_data['success'])
        self.assertIn("already", dup_data['message'].lower())
        print(f"[PASS] Double voting strictly blocked: {dup_data['message']}")

    def test_10_strict_face_verification(self):
        """Verifies that verification strictly rejects blank/wall frames and verifies genuine voter face."""
        # 1. Setup enrolled voter with photo
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                registration_status, created_at, updated_at
            ) VALUES (?, 'Strict Face Citizen', '1995-10-10', 31, 'Male', 'Father Strict',
                ?, ?, ?, 'Face Test Street', 'Chennai', 'Tamil Nadu', '600001',
                'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        # Enroll real face photo
        sample_path = os.path.join(config.STATIC_DIR, 'uploads', 'faces', 'WRM2745017_face.jpg')
        if os.path.exists(sample_path):
            sample_img = cv2.imread(sample_path)
            _, buf = cv2.imencode('.jpg', sample_img)
            capture_and_save_face(voter_id, buf.tobytes())

            # A. Test Blank Frame - MUST REJECT with NO FACE DETECTED
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            _, buf_blank = cv2.imencode('.jpg', blank_frame)
            res_blank = verify_voter_face(voter_id, buf_blank.tobytes())
            self.assertFalse(res_blank['match'], "Blank frame must not match.")
            self.assertEqual(res_blank['confidence'], 0.0)
            self.assertIn("NO FACE DETECTED", res_blank['message'])
            print(f"[PASS] Blank frame verification correctly rejected: {res_blank['message']}")

            # B. Test Wall / Background Frame - MUST REJECT with NO FACE DETECTED
            wall_img = np.full((480, 640, 3), 195, dtype=np.uint8) # Plain indoor wall
            _, buf_wall = cv2.imencode('.jpg', wall_img)
            res_wall = verify_voter_face(voter_id, buf_wall.tobytes())
            self.assertFalse(res_wall['match'], "Wall frame must not match.")
            self.assertEqual(res_wall['confidence'], 0.0)
            self.assertIn("NO FACE DETECTED", res_wall['message'])
            print(f"[PASS] Wall frame verification correctly rejected: {res_wall['message']}")

            # C. Test Different Person - MUST REJECT with FACE NOT RECOGNIZED
            diff_path = os.path.join(config.STATIC_DIR, 'img', 'Candidates', '1.png')
            if not os.path.exists(diff_path):
                diff_path = os.path.join(config.STATIC_DIR, 'uploads', 'faces', 'WRM2745018_face.jpg')
            if os.path.exists(diff_path):
                diff_img = cv2.imread(diff_path)
                _, buf_diff = cv2.imencode('.jpg', diff_img)
                res_diff = verify_voter_face(voter_id, buf_diff.tobytes())
                self.assertFalse(res_diff['match'], "Different person must not match.")
                self.assertTrue("FACE NOT RECOGNIZED" in res_diff['message'] or "BIOMETRIC MISMATCH" in res_diff['message'])
                print(f"[PASS] Different person verification correctly rejected: {res_diff['message']}")

            # D. Test Genuine Voter Face - MUST MATCH (>= 75%)
            res_gen = verify_voter_face(voter_id, buf.tobytes())
            self.assertTrue(res_gen['match'], "Enrolled voter face must verify successfully.")
            self.assertGreaterEqual(res_gen['confidence'], 0.75)
            print(f"[PASS] Genuine voter face verified successfully (Confidence: {res_gen['confidence'] * 100:.1f}%)")

    def test_11_optical_qr_scanner_api(self):
        """Verifies high-speed QR decoding API and JSON payload verification."""
        import base64
        # Create an enrolled voter in test DB with a QR token
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                face_status, fingerprint_status, registration_status, created_at, updated_at
            ) VALUES (?, 'QR Scanner Citizen', '1996-03-22', 30, 'Female', 'Father QR',
                ?, ?, ?, 'Scan Road', 'Bangalore', 'Karnataka', '560001',
                'ENROLLED', 'ENROLLED', 'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        qr_info = generate_and_save_voter_qr(voter_id)
        self.assertTrue(qr_info['success'])
        qr_file_path = os.path.join(config.STATIC_DIR, qr_info['qr_image_url'].replace('/static/', ''))

        with open(qr_file_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')

        res = self.client.post('/api/voting/scan_qr', json={'image': b64})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['found'])
        self.assertIn(voter_id, data['token'])
        print(f"[PASS] Optical QR Scanner API successfully decoded voter token: {data['token'][:45]}...")

        # Verify that eligibility check accepts the decoded QR JSON token
        ver_res = self.client.post('/api/voting/verify_voter', json={'voter_id': data['token']})
        self.assertEqual(ver_res.status_code, 200)
        ver_data = json.loads(ver_res.data)
        self.assertTrue(ver_data['eligible'])
        self.assertEqual(ver_data['voter']['voter_id'], voter_id)
        print(f"[PASS] QR Token voter eligibility confirmed for {ver_data['voter']['full_name']}.")

    def test_12_arcface_genuine_match_robustness(self):
        """Verifies ArcFace cosine similarity for genuine voter across lighting, rotation, and slight blur."""
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                registration_status, created_at, updated_at
            ) VALUES (?, 'Robustness Citizen', '1997-06-12', 29, 'Male', 'Father R',
                ?, ?, ?, 'Biometric Blvd', 'Madurai', 'Tamil Nadu', '625001',
                'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        sample_path = os.path.join(config.STATIC_DIR, 'uploads', 'faces', 'WRM2745017_face.jpg')
        if not os.path.exists(sample_path):
            self.skipTest("Sample face photo not available.")

        img = cv2.imread(sample_path)
        _, buf = cv2.imencode('.jpg', img)
        cap_res = capture_and_save_face(voter_id, buf.tobytes())
        self.assertTrue(cap_res['success'])

        # 1. Darker Lighting (-30%)
        dark_img = np.clip(img * 0.70, 0, 255).astype(np.uint8)
        _, buf_dark = cv2.imencode('.jpg', dark_img)
        res_dark = verify_voter_face(voter_id, buf_dark.tobytes())
        self.assertTrue(res_dark['match'], "Genuine voter under darker lighting must match.")
        self.assertGreaterEqual(res_dark['cosine_similarity'], 0.50)

        # 2. Brighter Lighting (+30%)
        bright_img = np.clip(img * 1.30, 0, 255).astype(np.uint8)
        _, buf_bright = cv2.imencode('.jpg', bright_img)
        res_bright = verify_voter_face(voter_id, buf_bright.tobytes())
        self.assertTrue(res_bright['match'], "Genuine voter under brighter lighting must match.")
        self.assertGreaterEqual(res_bright['cosine_similarity'], 0.50)

        # 3. Head Tilt / Rotation (10 degrees)
        h, w = img.shape[:2]
        M_rot = cv2.getRotationMatrix2D((w // 2, h // 2), 10, 1.0)
        rot_img = cv2.warpAffine(img, M_rot, (w, h))
        _, buf_rot = cv2.imencode('.jpg', rot_img)
        res_rot = verify_voter_face(voter_id, buf_rot.tobytes())
        self.assertTrue(res_rot['match'], "Genuine voter with 10 deg rotation must match.")
        self.assertGreaterEqual(res_rot['cosine_similarity'], 0.50)

        print(f"[PASS] ArcFace genuine match robustness verified (Dark sim: {res_dark['cosine_similarity']:.3f}, Bright sim: {res_bright['cosine_similarity']:.3f}, Rot sim: {res_rot['cosine_similarity']:.3f}).")

    def test_13_arcface_cross_voter_impostor_rejection(self):
        """Verifies ArcFace strictly rejects different-person attempts (e.g. Ragul trying to vote as Banu Sri K)."""
        voter_banu_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                registration_status, created_at, updated_at
            ) VALUES (?, 'Banu Sri Test', '1976-02-14', 50, 'Female', 'Father B',
                ?, ?, ?, 'Registry Road', 'Raman', 'Tamil Nadu', '624001',
                'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_banu_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        banu_photo = os.path.join(config.STATIC_DIR, 'uploads', 'faces', 'WRM2745020_face.jpg')
        ragul_photo = os.path.join(config.STATIC_DIR, 'uploads', 'faces', 'WRM2745017_face.jpg')
        if not os.path.exists(banu_photo) or not os.path.exists(ragul_photo):
            self.skipTest("Required voter comparison photos not available.")

        # Enroll Banu Sri K
        img_banu = cv2.imread(banu_photo)
        _, buf_banu = cv2.imencode('.jpg', img_banu)
        cap_res = capture_and_save_face(voter_banu_id, buf_banu.tobytes())
        self.assertTrue(cap_res['success'])

        # Live camera presents Ragul Kumaran K
        img_ragul = cv2.imread(ragul_photo)
        _, buf_ragul = cv2.imencode('.jpg', img_ragul)
        res_impostor = verify_voter_face(voter_banu_id, buf_ragul.tobytes())

        self.assertFalse(res_impostor['match'], "Impostor face must be strictly rejected.")
        self.assertLess(res_impostor['cosine_similarity'], 0.20, "Impostor cosine similarity must be far below threshold 0.50.")
        self.assertIn("FACE NOT RECOGNIZED", res_impostor['message'])
        print(f"[PASS] Impostor rejection verified: Banu vs Ragul cosine similarity = {res_impostor['cosine_similarity']:.4f} (Threshold: 0.50). Match: False.")

    def test_14_presentation_attack_detection(self):
        """Verifies Presentation-Attack Detection (PAD): rejects blurred frames, glare, and low-saturation attacks."""
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                registration_status, created_at, updated_at
            ) VALUES (?, 'PAD Test Citizen', '1993-04-18', 33, 'Male', 'Father PAD',
                ?, ?, ?, 'Security St', 'Salem', 'Tamil Nadu', '636001',
                'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        sample_path = os.path.join(config.STATIC_DIR, 'uploads', 'faces', 'WRM2745017_face.jpg')
        if not os.path.exists(sample_path):
            self.skipTest("Sample photo missing.")

        img = cv2.imread(sample_path)
        _, buf = cv2.imencode('.jpg', img)
        capture_and_save_face(voter_id, buf.tobytes())

        # 1. Heavy Defocus / Blur Attack
        blurry_frame = cv2.GaussianBlur(img, (41, 41), 15.0)
        _, buf_blur = cv2.imencode('.jpg', blurry_frame)
        res_blur = verify_voter_face(voter_id, buf_blur.tobytes())
        self.assertFalse(res_blur['match'])
        self.assertTrue("PRESENTATION ATTACK DETECTED" in res_blur['message'] or "NO FACE DETECTED" in res_blur['message'])

        # 2. Specular Reflection / Flash Glare Attack
        glare_frame = img.copy()
        glare_frame[120:280, 200:380] = 255
        _, buf_glare = cv2.imencode('.jpg', glare_frame)
        res_glare = verify_voter_face(voter_id, buf_glare.tobytes())
        self.assertFalse(res_glare['match'])
        self.assertTrue("PRESENTATION ATTACK DETECTED" in res_glare['message'] or "NO FACE DETECTED" in res_glare['message'])

        print(f"[PASS] Presentation-Attack Detection verified: Blurry and Glare spoof attempts strictly rejected.")

    def test_15_multi_face_rejection(self):
        """Verifies that multiple prominent faces in camera viewfinder strictly reject verification."""
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                registration_status, created_at, updated_at
            ) VALUES (?, 'Multi Face Citizen', '1994-11-20', 32, 'Female', 'Father MF',
                ?, ?, ?, 'Privacy Lane', 'Tiruchi', 'Tamil Nadu', '620001',
                'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        p1 = os.path.join(config.STATIC_DIR, 'uploads', 'faces', 'WRM2745017_face.jpg')
        p2 = os.path.join(config.STATIC_DIR, 'uploads', 'faces', 'WRM2745020_face.jpg')
        if not os.path.exists(p1) or not os.path.exists(p2):
            self.skipTest("Sample photos missing.")

        im1 = cv2.imread(p1)
        im2 = cv2.imread(p2)
        _, buf1 = cv2.imencode('.jpg', im1)
        capture_and_save_face(voter_id, buf1.tobytes())

        # Construct multi-face frame: two voters standing side by side
        h, w = 480, 640
        canvas = np.zeros((h, w * 2, 3), dtype=np.uint8)
        canvas[:, :w] = cv2.resize(im1, (w, h))
        canvas[:, w:] = cv2.resize(im2, (w, h))
        canvas_resized = cv2.resize(canvas, (w, h))

        _, buf_multi = cv2.imencode('.jpg', canvas_resized)
        res_multi = verify_voter_face(voter_id, buf_multi.tobytes())
        self.assertFalse(res_multi['match'])
        self.assertIn("MULTIPLE FACES DETECTED", res_multi['message'])
        print(f"[PASS] Multi-face rejection verified: {res_multi['message']}")

    def test_16_presiding_officer_manual_override(self):
        """Verifies alternative manual authentication route for false rejection / challenged voter."""
        voter_id = get_next_voter_id()
        test_aadhaar = random_aadhaar()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                registration_status, created_at, updated_at
            ) VALUES (?, 'Challenged Voter', '1950-01-01', 76, 'Male', 'Father Old',
                ?, ?, ?, 'Elderly Care', 'Madurai', 'Tamil Nadu', '625001',
                'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_id, hash_aadhaar(test_aadhaar), f"XXXX-XXXX-{test_aadhaar[-4:]}", random_mobile()))
        conn.commit()
        conn.close()

        # 1. Invalid Officer PIN -> 403 Forbidden
        bad_res = self.client.post(f'/api/voting/manual_override/{voter_id}', json={
            'officer_pin': '9999',
            'reason': 'Test unauthorized override'
        })
        self.assertEqual(bad_res.status_code, 403)
        bad_data = json.loads(bad_res.data)
        self.assertFalse(bad_data['success'])

        # 2. Valid Officer PIN -> 200 OK with manual override verified
        good_res = self.client.post(f'/api/voting/manual_override/{voter_id}', json={
            'officer_pin': '123',
            'reason': 'ECI Rule 49V: Elderly Voter Manual Verification'
        })
        self.assertEqual(good_res.status_code, 200)
        good_data = json.loads(good_res.data)
        self.assertTrue(good_data['success'])
        self.assertTrue(good_data['match'])
        self.assertTrue(good_data['manual_override'])
        self.assertIn("MANUAL IDENTITY VERIFIED", good_data['message'])

        # Verify audit log recorded
        conn = get_db_connection()
        log = conn.execute("SELECT * FROM enrollment_logs WHERE voter_id = ? AND action = 'POLLING_OFFICER_MANUAL_OVERRIDE'", (voter_id,)).fetchone()
        conn.close()
        self.assertIsNotNone(log)
        print(f"[PASS] Presiding Officer Manual Override alternative route verified: {good_data['message']}")

    def test_17_election_results_flow(self):
        """Verifies Election Results database query, admin authentication protection, and live tally views."""
        from database import get_election_results
        
        # 1. Verify get_election_results structure
        results = get_election_results()
        self.assertIn('total_voters', results)
        self.assertIn('total_votes', results)
        self.assertIn('turnout_pct', results)
        self.assertIn('candidates', results)
        self.assertIn('margin', results)
        self.assertIn('has_votes', results)
        self.assertGreater(len(results['candidates']), 0)
        
        # 2. Verify unauthenticated access redirects to /login using fresh client
        unauth_client = app.test_client()
        unauth_page = unauth_client.get('/results')
        self.assertEqual(unauth_page.status_code, 302)
        self.assertIn('/login', unauth_page.headers['Location'])

        unauth_api = unauth_client.get('/api/results')
        self.assertEqual(unauth_api.status_code, 302)
        self.assertIn('/login', unauth_api.headers['Location'])

        # 3. Authenticate as Admin
        login_res = self.client.post('/login', data={'username': 'admin', 'password': '123'}, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        # 4. Access Election Results page as Admin
        page_res = self.client.get('/results')
        self.assertEqual(page_res.status_code, 200)
        self.assertIn(b'Election Results', page_res.data)
        self.assertIn(b'Candidate Leaderboard', page_res.data)
        self.assertIn(b'Live EVM Ballot Tally', page_res.data)

        # 5. Access Election Results JSON API as Admin
        api_res = self.client.get('/api/results')
        self.assertEqual(api_res.status_code, 200)
        api_data = json.loads(api_res.data)
        self.assertTrue(api_data['success'])
        self.assertEqual(api_data['results']['total_votes'], results['total_votes'])
        print(f"[PASS] Election Results feature verified: {results['total_votes']} votes counted across {len(results['candidates'])} candidates.")

    def test_18_post_vote_sms_notification(self):
        """Verifies automatic post-vote SMS notification to the voter's respective mobile number and Admin SMS gateway controls."""
        from unittest.mock import patch, MagicMock
        from sms_service import normalize_phone, mask_phone
        from database import get_sms_logs

        # 1. Phone normalization & privacy masking
        self.assertEqual(normalize_phone('9876543210'), ('+919876543210', '9876543210'))
        self.assertEqual(normalize_phone('+91 98765 43210'), ('+919876543210', '9876543210'))
        self.assertEqual(mask_phone('9876543210'), '+91 XXXXXX3210')

        # 2. Register voter with specific mobile number and cast vote -> verify simulated SMS sent to that number
        voter_1 = get_next_voter_id()
        aadhaar_1 = random_aadhaar()
        mobile_1 = '9123456789'
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                face_status, fingerprint_status, qr_status, registration_status,
                created_at, updated_at
            ) VALUES (?, 'SMS Test Voter One', '1999-03-10', 27, 'Female', 'Father S',
                ?, ?, ?, 'SMS Lane 1', 'Chennai', 'Tamil Nadu', '600001',
                'ENROLLED', 'ENROLLED', 'ISSUED', 'COMPLETED',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_1, hash_aadhaar(aadhaar_1), f"XXXX-XXXX-{aadhaar_1[-4:]}", mobile_1))
        conn.commit()
        conn.close()

        cast_res = self.client.post('/api/voting/cast_vote', json={'voter_id': voter_1, 'candidate_id': 1})
        self.assertEqual(cast_res.status_code, 200)
        cast_data = json.loads(cast_res.data)
        self.assertTrue(cast_data['success'])
        self.assertIn('sms', cast_data)
        self.assertIn('sms', cast_data['receipt'])
        self.assertEqual(cast_data['sms']['masked_phone'], '+91 XXXXXX6789')
        self.assertNotIn('9123456789', json.dumps(cast_data), "Public kiosk JSON must not expose unmasked phone number.")
        self.assertNotIn('Vijay', cast_data['sms']['message_preview'], "SMS body must preserve ballot secrecy.")
        self.assertTrue(cast_data['sms']['simulated'])

        logs = get_sms_logs(limit=20)
        matching_logs = [row for row in logs if row['voter_id'] == voter_1]
        self.assertEqual(len(matching_logs), 1)
        self.assertEqual(matching_logs[0]['phone_number'], '+919123456789')
        self.assertEqual(matching_logs[0]['status'], 'SIMULATED')

        # 3. Verify Admin SMS Notifications route protection & rendering
        unauth_client = app.test_client()
        unauth_res = unauth_client.get('/sms-notifications')
        self.assertEqual(unauth_res.status_code, 302)
        self.assertIn('/login', unauth_res.headers['Location'])

        self.client.post('/login', data={'username': 'admin', 'password': '123'}, follow_redirects=True)
        admin_page = self.client.get('/sms-notifications')
        self.assertEqual(admin_page.status_code, 200)
        self.assertIn(b'Post-Vote Phone SMS Gateway', admin_page.data)
        self.assertIn(b'+919123456789', admin_page.data)

        # 4. Verify live Fast2SMS dispatch path using mocked HTTP gateway
        voter_2 = get_next_voter_id()
        aadhaar_2 = random_aadhaar()
        mobile_2 = '9988776655'
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO voters (
                voter_id, full_name, dob, age, gender, father_name,
                aadhaar_hash, aadhaar_masked, mobile, address, district, state, pincode,
                face_status, fingerprint_status, qr_status, registration_status,
                created_at, updated_at
            ) VALUES (?, 'SMS Live Voter Two', '1995-08-22', 31, 'Male', 'Father L',
                ?, ?, ?, 'SMS Lane 2', 'Madurai', 'Tamil Nadu', '625001',
                'ENROLLED', 'ENROLLED', 'ISSUED', 'COMPLETED',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (voter_2, hash_aadhaar(aadhaar_2), f"XXXX-XXXX-{aadhaar_2[-4:]}", mobile_2))
        conn.commit()
        conn.close()

        try:
            self.client.post('/sms-notifications', data={
                'enabled': 'on',
                'provider': 'fast2sms',
                'country_code': '+91',
                'fast2sms_api_key': 'test-fast2sms-secret-key',
                'fast2sms_route': 'q'
            }, follow_redirects=True)

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b'{"return": true, "request_id": "F2S_REQ_999"}'
            mock_resp.json.return_value = {'return': True, 'request_id': 'F2S_REQ_999'}

            app.config['SMS_TEST_FORCE_LIVE'] = True
            with patch('sms_service.requests.post', return_value=mock_resp) as mock_post:
                live_cast = self.client.post('/api/voting/cast_vote', json={'voter_id': voter_2, 'candidate_id': 2})
                self.assertEqual(live_cast.status_code, 200)
                live_data = json.loads(live_cast.data)
                self.assertTrue(live_data['sms']['delivered_live'])
                self.assertEqual(live_data['sms']['status'], 'SENT')
                self.assertEqual(live_data['sms']['provider'], 'FAST2SMS')
                self.assertEqual(live_data['sms']['masked_phone'], '+91 XXXXXX6655')
                self.assertTrue(mock_post.called)
                sent_json = mock_post.call_args.kwargs['json']
                self.assertEqual(sent_json['numbers'], '9988776655')
                self.assertIn(voter_2, sent_json['message'])
        finally:
            app.config['SMS_TEST_FORCE_LIVE'] = False
            self.client.post('/sms-notifications', data={
                'enabled': 'on',
                'provider': 'simulation',
                'country_code': '+91'
            }, follow_redirects=True)

        print(f"[PASS] Post-vote SMS dispatch verified for {voter_1} (+91 XXXXXX6789) and live gateway mock for {voter_2} (+91 XXXXXX6655).")

if __name__ == '__main__':
    unittest.main()
