"""
VaultVote Database Biometric Migration Script
Migrates legacy face encodings in SQLite face_biometrics table
to 512-dimensional ArcFace identity embeddings with YuNet 5-point alignment.
"""

import os
import sys
import json
import sqlite3
import shutil
from datetime import datetime
import cv2
import numpy as np
import onnxruntime as ort  # type: ignore

# Ensure project root in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config
from database import get_db_connection, log_enrollment

YUNET_PATH = os.path.join(BASE_DIR, 'models', 'face_detection_yunet_2023mar.onnx')
ARCFACE_PATH = os.path.join(BASE_DIR, 'models', 'w600k_mbf.onnx')

REFERENCE_FACIAL_POINTS = np.array([
    [38.2946, 51.6963],   # right eye (subject's right, viewer's left)
    [73.5318, 51.5014],   # left eye (subject's left, viewer's right)
    [56.0252, 71.7366],   # nose tip
    [41.5493, 92.3655],   # right mouth corner
    [70.7299, 92.2041]    # left mouth corner
], dtype=np.float32)

def align_and_crop(img, f):
    lms = f[4:14].reshape(5, 2).astype(np.float32)
    M, _ = cv2.estimateAffinePartial2D(lms, REFERENCE_FACIAL_POINTS, method=cv2.LMEDS)
    if M is None:
        x, y, w, h = int(f[0]), int(f[1]), int(f[2]), int(f[3])
        H, W = img.shape[:2]
        crop = img[max(0, y):min(H, y+h), max(0, x):min(W, x+w)]
        return cv2.resize(crop, (112, 112))
    return cv2.warpAffine(img, M, (112, 112), borderValue=0.0)

def migrate_database():
    print("=" * 65)
    print("  VAULTVOTE BIOMETRIC MIGRATION: ARCFACE (512-D) + YUNET")
    print("=" * 65)

    # 1. Verify models exist
    if not os.path.exists(YUNET_PATH):
        raise FileNotFoundError(f"YuNet model missing at {YUNET_PATH}")
    if not os.path.exists(ARCFACE_PATH):
        raise FileNotFoundError(f"ArcFace model missing at {ARCFACE_PATH}")

    # 2. Verify database backup
    backup_file = os.path.join(BASE_DIR, f"vaultvote_backup_migration_{int(datetime.now().timestamp())}.db")
    shutil.copy2(config.DB_PATH, backup_file)
    print(f"[✓] Created pre-migration database snapshot: {backup_file}")

    # 3. Initialize models
    detector = cv2.FaceDetectorYN.create(YUNET_PATH, '', (320, 320), 0.6, 0.3, 5000)
    session = ort.InferenceSession(ARCFACE_PATH, providers=['CPUExecutionProvider'])

    conn = get_db_connection()
    rows = conn.execute("SELECT id, voter_id, photo_path, face_encoding FROM face_biometrics").fetchall()
    records = [dict(r) for r in rows]
    conn.close()

    print(f"\nProcessing {len(records)} registered biometric records...")

    success_count = 0
    fail_count = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    for row in records:
        vid = row['voter_id']
        photo_rel = row['photo_path']
        photo_abs = os.path.join(config.STATIC_DIR, photo_rel)

        if not os.path.exists(photo_abs):
            print(f"  [!] Photo file missing for voter {vid}: {photo_abs}")
            fail_count += 1
            continue

        img = cv2.imread(photo_abs)
        if img is None:
            print(f"  [!] Failed to read image for voter {vid}")
            fail_count += 1
            continue

        h, w = img.shape[:2]
        detector.setInputSize((w, h))
        _, faces = detector.detect(img)

        if faces is None or len(faces) == 0:
            print(f"  [!] No face detected by YuNet for voter {vid}")
            fail_count += 1
            continue

        aligned = align_and_crop(img, faces[0])
        rgb = cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB)
        norm = (rgb.astype(np.float32) - 127.5) / 128.0
        inp = np.transpose(norm, (2, 0, 1))[np.newaxis, :, :, :]
        out = session.run(None, {'input.1': inp})[0][0]
        embedding = out / np.linalg.norm(out)

        encoding_json = json.dumps(embedding.tolist())
        cursor.execute('''
            UPDATE face_biometrics
            SET face_encoding = ?, confidence_score = 0.98, enrolled_at = ?
            WHERE voter_id = ?
        ''', (encoding_json, datetime.now().isoformat(), vid))

        cursor.execute('''
            INSERT INTO enrollment_logs (voter_id, action, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (vid, "ARCFACE_MIGRATION_512D",
              "Migrated facial biometric vector to 512-dimensional ArcFace embedding with YuNet 5-point alignment.",
              "127.0.0.1", datetime.now().isoformat()))

        print(f"  [✓] {vid}: Successfully migrated to 512-d ArcFace vector.")
        success_count += 1

    conn.commit()
    conn.close()

    print("\n" + "=" * 65)
    print(f"  MIGRATION SUMMARY: {success_count} succeeded, {fail_count} failed.")
    print("=" * 65)
    return success_count, fail_count

if __name__ == '__main__':
    migrate_database()
