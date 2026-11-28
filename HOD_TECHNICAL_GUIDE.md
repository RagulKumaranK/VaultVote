# VaultVote — Complete Technical & HOD Presentation Guide

> Use this guide to walk your HOD (Head of Department) or external viva examiners through **how VaultVote is architected, coded, secured, and tested**, with honest answers for every technical question.

---

## 1. How to Open Your Explanation (30-Second Pitch)

> *"Sir/Madam, **VaultVote** is a hardware-free, full-stack biometric electronic voting and voter registration system built with **Python (Flask)**, **SQLite 3**, **OpenCV**, and **ONNX Runtime**. Unlike basic student demos that rely on slow Haar Cascades or external Raspberry Pi hardware, we built two separated portals—an **Admin Electoral Console** and a **5-Stage Citizen Voting Kiosk**—running entirely on a standard Windows laptop. Voters register once with **SHA-256 Aadhaar deduplication**, **YuNet + 512-dimensional ArcFace facial embeddings**, and receive a **ReportLab PDF Voter ID Card** with a signed QR code. At the kiosk, voters authenticate via a **3-tier optical QR scanner**, **passive anti-spoofing + ArcFace verification**, cast their vote on an **ECI M3-style EVM ballot** with **neural voice guidance**, get a **VVPAT audit slip**, and receive a **secret-ballot SMS confirmation** on their registered mobile number."*

---

## 2. Live Demo Flow (Show This Order in 4–5 Minutes)

1. **Admin Login (`/login`) & Dashboard (`/dashboard`)**:
   - Log in (`admin` / `123`). Point out the live KPI metrics (Total Voters, Face Enrolled, Completed Cards, Turnout %) and live results tally widget.
2. **Voter Registration (`/register`)**:
   - Enter synthetic 12-digit Aadhaar (real-time `/api/check_duplicate` warns immediately if already enrolled).
   - Type a Tamil Nadu district (e.g., `Ramanathapuram`) to demonstrate offline **District → State & PIN auto-fill** (`/api/lookup_location`).
   - Show auto-age validation (`>= 18` years) and sequential EPIC Voter ID generation (`WRM2745...`).
3. **Biometric Enrollment (`/biometric/<voter_id>`) & PVC ID Card (`/voter/card/<voter_id>`)**:
   - Capture live webcam photo with YuNet HUD overlay (saves 512-d ArcFace vector).
   - Trigger **Simulated Fingerprint** enrollment (honestly explain it is explicitly marked `is_simulated=1` for hardware-free laptops).
   - Finalize to generate the QR token (`VV-AUTH-...`) and open/download the official **100mm × 66mm PDF Voter ID Card**.
4. **Citizen Voting Kiosk (`/`) — Steps 0 to 4**:
   - **Step 0 (`step0_leading.html`):** Click **Start Voting** (unlocks browser audio playback for `edge-tts` voice guidance).
   - **Step 1 (`step1_voter_id.html`):** Scan QR code or switch to Manual Input (`WRM2745...`).
   - **Step 2 (`step2_biometric.html`):** Show live camera verification (demonstrate impostor rejection or multi-face rejection if two people sit in front of the camera, plus explain **Presiding Officer Manual Override** under ECI Rule 49V).
   - **Step 3 (`step3_ballot.html`):** Show the BEL M3-inspired bilingual English+Tamil EVM rows, Braille VOTE buttons, red LED lamp, and confirmation modal (`modal_confirm_vote.html`).
   - **Step 4 (`step4_vvpat.html`):** Listen to the 950 Hz EVM beep + chime + voice announcement, then show the **VVPAT Audit Slip** and **Phone SMS Confirmation** card (notice candidate choice is omitted from SMS to protect secret-ballot privacy).
   - Try scanning the **same Voter ID again** to prove double voting is blocked!
5. **Admin Results (`/results`), SMS Console (`/sms-notifications`), & Audit Logs (`/logs`)**:
   - Show the live ECI Form 20 leaderboard, SMS gateway settings/delivery history, and tamper-evident event logs.

---

## 3. System Architecture & File Breakdown

```text
Browser (Admin Portal & 5-Stage Kiosk UI)
   ├── WebRTC Camera + jsQR / BarcodeDetector + Web Audio + localStorage State
   │
   ▼ HTTP / JSON / MJPEG Stream (127.0.0.1:5000)
Flask Backend Controller (app.py — 28 routes, @admin_required guards)
   ├── database.py           -> SQLite 3 (vaultvote.db, 11 tables, FK + UNIQUE constraints)
   ├── sequence.py           -> Thread-safe sequential Voter ID allocator (WRM2745001...)
   ├── location_service.py   -> Offline India District/PIN lookup (from location_data.js)
   ├── face_service.py       -> YuNet detector + 5-pt alignment + PAD + 512-d ArcFace CPU inference
   ├── fingerprint_service.py-> Simulated fingerprint template engine (FPSIM-..., is_simulated=1)
   ├── qr_service.py         -> Signed JSON QR generator (VV-AUTH-...)
   ├── id_card_service.py    -> Pillow (1024x682 PNG) + ReportLab (100x66mm PDF) PVC card builder
   ├── sms_service.py        -> Post-vote SMS dispatcher (Twilio / Fast2SMS / Webhook / Simulation)
   └── generate_announcements.py -> Pre-renders offline neural MP3s via edge-tts
```

### Database Schema (`database.py` — 11 SQLite Tables)

1. **`admin`** — Admin accounts with Werkzeug salted password hashes (`scrypt`/`pbkdf2`).
2. **`voters`** — Master roll: `voter_id (UNIQUE)`, `full_name`, `dob`, `age`, `aadhaar_hash (UNIQUE SHA-256)`, `aadhaar_masked`, `mobile`, `address/district/state/pincode`, and status flags (`face_status`, `fingerprint_status`, `qr_status`, `registration_status`).
3. **`face_biometrics`** — Links `voter_id (FK)` → `photo_path` + JSON 512-float ArcFace vector.
4. **`fingerprint_biometrics`** — Links `voter_id (FK)` → `simulated_reference`, `pattern_type`, `minutiae_count`, `is_simulated = 1`.
5. **`voter_qr_tokens`** — Links `voter_id (FK)` → `qr_token (UNIQUE)` + `qr_image_path`.
6. **`voter_id_sequence`** — Single-row atomic counter (`WRM2745`, `current_number`).
7. **`candidates`** — Contesting candidates (`name`, `party`, `symbol_name`, `banner_image`, `symbol_image`, `votes_count`).
8. **`votes`** — `(id, voter_id UNIQUE FK, candidate_id FK, cast_at, ip_address)` enforcing one-vote-per-voter at the DB engine level.
9. **`enrollment_logs`** — Audit ledger tracking `ADMIN_LOGIN`, `PERSONAL_DETAILS_SAVED`, `FACE_ENROLLED_ARCFACE`, `QR_GENERATED`, `CARD_GENERATED`, `VOTE_CAST`, `POLLING_OFFICER_MANUAL_OVERRIDE`, `VOTER_DELETED`, `SMS_*`.
10. **`sms_logs`** — SMS audit history (`phone_number`, `message_body`, `provider`, `status`, `receipt_ref`, `error_message`).
11. **`sms_settings`** — Singleton config (`id = 1`) for switching providers live in Admin UI.

---

## 4. How Every Core Feature Works Technically

### A. Deep Learning Facial Recognition (`face_service.py`)
1. **Detection (`detect_faces_yunet`):** Uses OpenCV's CNN detector **`YuNet`** (`models/face_detection_yunet_2023mar.onnx` via `cv2.FaceDetectorYN`, `score_threshold = 0.60`, `nms_threshold = 0.30`). Filters impossible box sizes (`< 35px`) and aspect ratios (`< 0.55` or `> 1.65`) to ignore curtains/background clutter, then ranks candidates by bounding-box area, centrality, and confidence.
2. **Multi-Face Rejection:** If a second face is present with `area > 35%` of primary face and confidence `>= 0.65`, verification rejects immediately (`MULTIPLE FACES DETECTED`).
3. **Passive Presentation-Attack Detection (`check_presentation_attack`):**
   - **Blur / Printed Photo Check:** Computes `cv2.Laplacian(gray, CV_64F).var()`. Rejects if `< 25.0`.
   - **Screen Flash / Glare Check:** Measures pixels with `R, G, B > 252`. Rejects if glare exceeds `15%` of face ROI.
   - **Monochrome / Paper Check:** Converts ROI to HSV and checks mean saturation. Rejects if `< 12.0`.
4. **5-Point Geometric Alignment (`align_face_5points`):** Extracts 5 landmarks from YuNet (right eye, left eye, nose tip, right mouth corner, left mouth corner) and computes a similarity affine matrix (`cv2.estimateAffinePartial2D` with `LMEDS`) to warp the face into a canonical `112 × 112` ArcFace template (`REFERENCE_FACIAL_POINTS`).
5. **Embedding & Matching (`extract_arcface_embedding`, `verify_voter_face`):** Runs **ArcFace MobileFaceNet** (`models/w600k_mbf.onnx`) via **ONNX Runtime** (`CPUExecutionProvider`) to output a **512-dimensional vector**, $L_2$-normalizes it, and computes **Cosine Similarity** ($\mathbf{e}_{\text{live}} \cdot \mathbf{e}_{\text{enrolled}}$). Matches if `cosine_sim >= 0.50` (scaled to `75%–99%` display confidence).

### B. Hybrid 3-Tier Optical QR Scanning (`voting_kiosk.js` & `app.py`)
Every `260 ms`, `scanQrVideoFrame()` attempts:
1. **Browser `BarcodeDetector`** (native hardware-accelerated decoding in Chromium).
2. **Client-Side `jsQR`** (sub-pixel canvas decoding with `inversionAttempts: "attemptBoth"`).
3. **Server-Side 6-Pass OpenCV Fallback (`/api/voting/scan_qr`)** if client decoding misses due to webcam blur/lighting: raw frame → Unsharp Masking (`GaussianBlur` + `addWeighted`) → CLAHE contrast (`clipLimit=3.0`) → Otsu thresholding → Adaptive Gaussian threshold → `1.5×` bicubic upscale.

### C. Privacy & Concurrency Guarantees
- **Aadhaar Privacy:** Never stored in plaintext (`database.py:hash_aadhaar`). Only a deterministic **SHA-256** digest (for uniqueness lookup) and masked suffix (`XXXX-XXXX-9900`) are persisted.
- **QR Privacy:** QR codes contain only `VV-AUTH-{voter_id}-{uuid12}` + timestamps — **no Aadhaar, mobile number, or biometric vector** inside the QR matrix.
- **Double-Vote Prevention:** Enforced at two layers: pre-flight lookup (`check_voter_voting_eligibility`) AND database `UNIQUE(voter_id)` constraint in `votes` with `sqlite3.IntegrityError` rollback in `cast_vote()`.
- **Thread Safety:** Singletons `_detector_lock`, `_arcface_lock`, `_camera_lock` (`face_service.py`), and `_sequence_lock` (`sequence.py`) prevent race conditions under concurrent Flask requests.

### D. PVC Card Generation (`id_card_service.py`) & Audio (`voting_kiosk.js`)
- **Card Builder:** Composites a `1024 × 682` RGBA image using `Pillow` (ECI template + Ashoka watermark + rounded voter portrait + `BIOMETRIC ENROLLED` badge + QR code + ECI hologram + Hindi/English PNG labels + circular ECI stamp) and embeds it into a `100 mm × 66 mm` PDF using `ReportLab`.
- **Voice & Audio:** Pre-generated Indian English neural prompts (`edge-tts` `en-IN-NeerjaNeural` in `static/audio/*.mp3`) with automatic `window.speechSynthesis` fallback, plus Web Audio API synthesized `950 Hz` EVM beep and success chimes.

### E. Post-Vote SMS Architecture (`sms_service.py`)
- Executes inside `api_cast_vote()` **only after** `cast_vote()` commits, wrapped safely so external carrier/DNS failures **never abort or roll back a cast ballot**.
- Supports **Twilio**, **Fast2SMS (India `+91`)**, **Custom HTTP / Android Gateway Webhook**, and **Simulation mode** (`sms_logs` audit log), keeping candidate choice secret and returning only masked `+91 XXXXXX...` to the public kiosk UI.

---

## 5. Top 20 Tough HOD Questions & Model Answers

| # | Likely HOD Question | Strong Technical Answer |
|---|---|---|
| 1 | **Why did you use YuNet + ArcFace instead of Haar Cascade or `face_recognition` (dlib)?** | Haar Cascades struggle with tilted heads, lighting changes, and background textures (curtain false positives), and `dlib` requires heavy C++ compilation on Windows. **YuNet** gives CNN accuracy plus **5 facial landmarks** for affine alignment, and **ArcFace (`w600k_mbf.onnx`)** outputs a discriminative **512-d L2-normalized embedding** running fast on CPU via **ONNX Runtime** without GPU or C++ build tools. |
| 2 | **What mathematical metric compares two faces, and why is your threshold `0.50`?** | Because ArcFace vectors are $L_2$-normalized ($\|\mathbf{e}\|_2 = 1$), their **cosine similarity** simplifies to a dot product ($\mathbf{e}_1 \cdot \mathbf{e}_2$). In our tests (`test_12`, `test_13`), genuine captures under `-30%` dark, `+30%` bright, and `10°` rotation scored **`0.979–0.983`**, whereas cross-person impostor pairs scored **`0.0399`**, making `0.50` (`75%` UI confidence) a safe separation boundary. |
| 3 | **How do you stop someone holding a photo or phone screen to the camera?** | `verify_voter_face()` runs three checks before ArcFace: (1) **Multi-face rejection** if a second face exceeds 35% area, (2) **Passive PAD** checking Laplacian blur (`< 25.0` catches low-res photos), specular glare (`RGB > 252 > 15%` catches glossy phone screens), and HSV saturation (`< 12.0` catches B&W printouts). *(Be honest: this is single-frame passive PAD; full 3D depth or blink challenges are noted as future work.)* |
| 4 | **Why is the fingerprint marked "Simulated"? Doesn't that weaken Dual Biometric?** | Our design constraint was **zero external hardware** on standard Windows laptops (`README.md`). Instead of hiding a fake check, `fingerprint_service.py` explicitly marks templates `is_simulated=1` (`FPSIM-...`), demonstrates the dual-biometric enrollment workflow and database schema (`fingerprint_biometrics`), and keeps hardware scanner SDK integration modular for future deployment. |
| 5 | **What happens if a genuine voter's face fails due to poor lighting or aging?** | Rather than permanently locking out eligible voters, Step 2 supports **Presiding Officer Manual Override** (`/api/voting/manual_override/<voter_id>`), modeled on **ECI Rule 49V**. An officer enters a PIN + reason, generating a permanent `POLLING_OFFICER_MANUAL_OVERRIDE` audit record in `enrollment_logs`. |
| 6 | **Why did you store votes in SQLite instead of Blockchain?** | For a standalone polling booth kiosk, a relational database provides microsecond local latency and zero gas/network dependency. SQLite's **`UNIQUE(voter_id)` constraint** on `votes` combined with atomic transactions and `PRAGMA foreign_keys = ON` guarantees single-vote enforcement offline. |
| 7 | **Can an administrator or hacker see who a specific voter voted for in the SMS or QR code?** | **No in the SMS or QR code:** QR tokens only contain `VV-AUTH-...`, and SMS confirmation messages intentionally omit candidate choice to prevent voter coercion ("receipt buying"). *(Honest architectural caveat to mention if asked about DB privacy: the `votes` table stores `voter_id` + `candidate_id` via FK for strict audit/uniqueness in this prototype; decoupling voter participation status from anonymous ballot tokens via blind/hashed receipts is a planned enhancement.)* |
| 8 | **How do you prevent duplicate voter registrations at enrollment?** | We enforce two deduplication checks in `database.py` + `/api/check_duplicate`: (1) One-way **SHA-256 hashing** (`aadhaar_hash TEXT UNIQUE`) catches matching 12-digit numbers without storing raw Aadhaar, and (2) `check_duplicate_identity()` checks `LOWER(full_name) + dob` or matching `mobile`. |
| 9 | **What prevents race conditions if two admins click Register simultaneously?** | `sequence.py` wraps sequential Voter ID allocation (`WRM2745001...`) inside a Python `threading.Lock()` and verifies the ID does not already exist in `voters` before updating `voter_id_sequence`. Likewise, YuNet, ArcFace, and webcam access use dedicated `threading.Lock()` singletons in `face_service.py`. |
| 10 | **Why do you run 6 image-processing passes on the server for QR scanning?** | Laptop webcams often suffer from motion blur, uneven backlight, or small QR size on printed cards. If browser `BarcodeDetector` and `jsQR` miss a frame, `/api/voting/scan_qr` automatically runs unsharp masking, CLAHE contrast enhancement, Otsu thresholding, adaptive Gaussian thresholding, and `1.5×` bicubic upscaling before `cv2.QRCodeDetector`. |
| 11 | **What happens if the voter refreshes or closes the tab mid-vote?** | `voting_kiosk.js` persists the active step, voter object, and VVPAT metadata to `localStorage` (`vaultvote_kiosk_state`) via `saveKioskState()` and restores the exact step in `restoreKioskState()`. |
| 12 | **What happens if the SMS API (Twilio/Fast2SMS) is offline when someone votes?** | `dispatch_sms()` in `sms_service.py` executes *after* `cast_vote()` commits and uses a `6 s` timeout with full exception handling. If DNS/network fails (`FAILED`), the vote remains safely recorded, the failure is logged in `sms_logs`, and the Admin can retry manually with one click (`Resend`). |
| 13 | **Why wasn't a live Indian SMS received automatically without configuring Fast2SMS/Twilio?** | In India, **TRAI DLT regulations** block unverified A2P SMS API traffic unless an entity registers headers/templates or uses an Android SIM gateway. Therefore VaultVote runs in **Simulation Mode** by default offline and supports **Fast2SMS**, **Twilio**, and **HTTP/Android Webhook** live dispatch from Admin Settings without code changes. |
| 14 | **How do you generate Voter ID cards with Hindi labels cleanly on Windows?** | In `id_card_service.py`, static Hindi field labels (`card_labels/*.png`) and security overlays (`ashoka_watermark.png`, `eci_hologram_clean.png`, `eci_stamp_clean.png`) are composited onto a `1024 × 682` RGBA Pillow canvas alongside the cropped voter portrait (`ImageOps.fit` + rounded mask) and QR code, then embedded into a `100 mm × 66 mm` PDF via ReportLab. |
| 15 | **Why use pre-rendered `edge-tts` MP3s instead of only browser `speechSynthesis`?** | Different Windows browsers have inconsistent voices or mute restrictions. Pre-generating Indian English female prompts (`en-IN-NeerjaNeural`) into `static/audio/*.mp3` ensures reliable offline playback, while Web Speech acts as a fallback and Web Audio generates exact `950 Hz` EVM tones. |
| 16 | **How are Admin routes protected from voters at the kiosk?** | All 16+ admin endpoints (`/dashboard`, `/register`, `/biometric`, `/voters`, `/results`, `/sms-notifications`, `/logs`) are wrapped with the `@admin_required` Flask decorator checking `session.get('admin_logged_in')`, redirecting unauthenticated users to `/login`. |
| 17 | **How do you maintain code quality and verify nothing broke after updates?** | We maintain an automated **18-test `unittest` suite (`test_suite.py`)** running against an isolated `test_vaultvote.db` database, testing database seeding, deduplication, ArcFace robustness across lighting/rotation, impostor rejection (`0.0399`), blur/glare PAD spoofing, multi-face rejection, Rule 49V override, election results, and SMS dispatch (`18 tests — OK`). |
| 18 | **What is stored in `static/uploads/` when a voter is deleted?** | `delete_voter()` (`database.py:318-435`) deletes the `voters` row (cascading to `face_biometrics`, `fingerprint_biometrics`, `voter_qr_tokens`, and `votes`), explicitly unlinks the face `.jpg`, QR `.png`, and card `.pdf`/`.png` files from disk, and logs `VOTER_DELETED`. |
| 19 | **Why did you put `test_vaultvote.db` and `app.config['SMS_TEST_FORCE_LIVE']` safeguards in tests?** | So running automated tests never modifies live election data (`vaultvote.db`) and never accidentally fires live paid Twilio/Fast2SMS requests to synthetic `random_mobile()` phone numbers unless explicitly mocked (`unittest.mock.patch`). |
| 20 | **If you had 3 more months (Phase 2), what would you upgrade next?** | Integrate a physical USB fingerprint SDK (replacing `is_simulated=1`), add multi-frame challenge-response liveness, add an asynchronous SMS retry worker, and separate voter identity (`voters`) from anonymous vote tokens (`votes`) via blind signatures or an append-only cryptographic ledger. |

---

## 6. Quick Pre-Presentation Checklist

* [ ] Start the server cleanly from a networked terminal: `.\.venv\Scripts\python.exe app.py`
* [ ] Pre-verify `http://127.0.0.1:5000` (Kiosk) and `http://127.0.0.1:5000/login` (Admin: `admin` / `123`) in Chrome/Edge.
* [ ] Keep one enrolled Voter ID QR code ready on your phone or printed card (`static/uploads/cards/<VOTER_ID>_card.pdf`) for the live QR scan demo.
* [ ] Ensure webcam lighting is bright and even so YuNet & passive PAD (`lap_var >= 25.0`, `sat_mean >= 12.0`) pass on the first attempt.
* [ ] If demonstrating live SMS via Fast2SMS/Twilio/Android gateway, test it once from **Admin → SMS Notifications** before stepping in front of your HOD; otherwise explain **Simulation Mode** confidently as your offline carrier-independent fallback.
