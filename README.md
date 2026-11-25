# VaultVote – Smart Biometric Voting System
## Development Mode: Laptop Only – No External Hardware

**VaultVote** is an advanced, hardware-free electoral registration and biometric identity system developed for academic demonstration. Engineered specifically to run seamlessly on standard **Windows 10 / Windows 11 laptops**, it eliminates the requirement for Raspberry Pi, physical fingerprint readers, or external camera peripherals.

---

## 🌟 Key Features

1. **Laptop-Only Architecture**:
   - Uses the built-in laptop webcam via **OpenCV** for live face detection, HUD bounding box tracking, and 128-dimensional biometric encoding extraction.
   - Includes a high-tech **software-simulated fingerprint registration module** with animated laser sweep visuals, minutiae analysis, and cryptographic template generation.
2. **Secure Admin Module**:
   - Session management and password hashing via `werkzeug.security`.
   - Real-time statistical dashboard showing total voters, face registrations, fingerprint simulations, and completed credentials.
3. **Automated Sequential Voter ID Generation**:
   - Generates non-duplicate voter IDs in the exact format: `WRM2745001`, `WRM2745002`, `WRM2745003`...
   - Atomically tracked in SQLite (`voter_id_sequence`) to guarantee zero gaps and zero collisions.
4. **Duplicate Detection & Integrity Safeguards**:
   - Real-time duplicate checking against synthetic 12-digit Aadhaar numbers using one-way SHA-256 hashes.
   - Duplicate prevention against matching Full Name + Date of Birth + Mobile combinations.
   - Immediate conflict alert displaying the existing Voter ID to block multi-registration.
5. **Privacy-Preserving QR Code Generation**:
   - Generates cryptographically secure, signed verification tokens (`VV-AUTH-WRM...`).
   - Does **not** expose raw Aadhaar numbers or raw biometric templates in the QR code payload.
   - High-resolution downloadable PNG output.
6. **Official PDF Voter ID Card Generation**:
   - Programmatically renders laminated PVC-style official election cards via **ReportLab**.
   - Includes official emblems, voter photo, voter ID, demographic details, security chip watermark, and QR verification matrix.
   - Instant PDF download and direct print-ready stylesheet.
7. **Comprehensive Audit Ledger**:
   - Tamper-evident activity logging in SQLite (`enrollment_logs`) recording logins, demographic entries, face captures, fingerprint simulations, and credential issuances with timestamps and IP records.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Bootstrap Icons |
| **Backend** | Python 3.10+, Flask 3.x, Werkzeug |
| **Database** | SQLite 3 (`vaultvote.db`) with relational integrity & indexes |
| **Computer Vision & Face Detection** | OpenCV (`cv2`) Haar Cascades, HUD overlay, 128-d biometric descriptor |
| **QR Code Engine** | `qrcode[pil]`, Pillow, OpenCV QR fallback |
| **Document Generation** | `reportlab`, `fpdf2` |
| **Operating System** | Windows 10 / Windows 11 |

---

## 📂 Project Directory Structure

```text
vaultvote/
├── app.py                      # Core Flask web server & administrative endpoints
├── config.py                   # Application settings, secret keys, directory paths
├── database.py                 # SQLite initialization, schema setup, CRUD & deduplication
├── sequence.py                 # Atomic thread-safe Voter ID generator (WRM2745001...)
├── face_service.py             # OpenCV webcam streaming, HUD bounding boxes, face encoding
├── fingerprint_service.py      # Simulated fingerprint enrollment, template generator, duplicate checks
├── qr_service.py               # Cryptographic QR token generator & image compiler
├── id_card_service.py          # ReportLab PDF Voter ID card generation
├── requirements.txt            # Python dependencies
├── static/
│   ├── css/
│   │   ├── style.css           # Custom dark navy theme, laser animations, HUD reticles
│   │   └── id_card.css         # Digital & print PVC voter ID card styling
│   ├── js/
│   │   ├── main.js             # Client-side age calculation, duplicate verification, formatting
│   │   ├── webcam.js           # Built-in webcam controller, canvas capture, retake logic
│   │   └── fingerprint.js      # Animated laser sweep, progress bar, audio cues
│   ├── img/
│   │   └── logo.svg            # VaultVote official biometric shield emblem
│   └── uploads/
│       ├── faces/              # Stored voter face photographs (.jpg)
│       ├── qrcodes/            # Stored QR code image matrices (.png)
│       └── cards/              # Generated printable PDF cards (.pdf)
└── templates/
    ├── base.html               # Master layout with sidebar navigation & topbar
    ├── login.html              # Admin authentication interface
    ├── dashboard.html          # Operational metrics, quick actions & activity feed
    ├── register_voter.html     # Voter demographic entry form with auto-age calculation
    ├── duplicate_alert.html    # Dedicated duplicate conflict blocker
    ├── biometric_enroll.html   # Face capture & simulated fingerprint workstation
    ├── voter_card.html         # Digital Voter ID Card preview & download portal
    ├── registered_voters.html  # Searchable & filterable directory of all voters
    ├── search_voter.html       # Fast voter lookup by ID, Aadhaar, or Name
    └── audit_logs.html         # Security & enrollment audit log ledger
```

---

## 🗄️ Database Architecture (SQLite)

The application initializes `vaultvote.db` with 7 structured tables:

1. `admin`: Administrator usernames, hashed credentials (`scrypt` / `pbkdf2`), full name, timestamps.
2. `voters`: Primary demographic ledger storing `voter_id`, `full_name`, `dob`, `age`, `gender`, `father_name`, `aadhaar_hash` (one-way SHA-256), `aadhaar_masked`, `mobile`, `address`, `district`, `state`, `pincode`, and enrollment status flags.
3. `face_biometrics`: High-resolution photograph path, 128-dimensional biometric encoding JSON, and confidence scores.
4. `fingerprint_biometrics`: Simulated enrollment reference (`FPSIM-...`), pattern type (`Whorl`, `Loop`, `Arch`), minutiae count, and simulation flag.
5. `voter_qr_tokens`: Cryptographic random QR token, QR image path, timestamp.
6. `voter_id_sequence`: Tracks the current serial number and prefix (`WRM2745`) for atomic auto-incrementing.
7. `enrollment_logs`: Audit logs capturing every system event with voter ID, action type, IP address, and timestamp.

---

## 🚀 Setup & Installation Instructions (Windows 10 / 11)

### 1. Prerequisites
- **Python 3.10+** (Python 3.10, 3.11, 3.12, or 3.13) installed with *"Add Python to PATH"* enabled.
- Built-in laptop webcam.

### 2. Open PowerShell or Command Prompt
Navigate to the project directory:
```powershell
cd C:\Users\ragul\.gemini\antigravity\scratch\vaultvote
```

### 3. Install Dependencies
Install all required libraries using pip:
```powershell
pip install -r requirements.txt
```

> **Note on `face_recognition` library**: The application automatically checks for `face_recognition`. If prebuilt Visual Studio C++ build tools are present, it uses `face_recognition`. If not, it seamlessly runs OpenCV's built-in Haar Cascade face detector and normalized 128-d biometric descriptor. Both modes run natively on Windows with zero setup hurdles!

### 4. Start the Application
Run the Flask server:
```powershell
python app.py
```

### 5. Access the Web Application
Open your browser (Chrome, Edge, Firefox) and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🔑 Default Administrator Credentials

| Field | Value |
|---|---|
| **Username** | `admin` |
| **Password** | `123` |

---

## 🔄 Complete Registration Workflow

```text
Admin Login
    ↓
Admin Dashboard (Review stats & Next Voter ID preview)
    ↓
Register Voter (Enter demographic details & synthetic Aadhaar)
    ↓
Duplicate Detection Engine
    ├─ If duplicate Aadhaar or Name/DOB exists ──> Block & Display Existing Voter ID
    └─ If unique ──> Automatically Allocate Voter ID (e.g. WRM2745001)
    ↓
Biometric Registration Portal:
    ├─ Step A: Face Registration (Laptop built-in webcam + OpenCV HUD bounding box)
    └─ Step B: Software Simulated Fingerprint (Laser sweep animation + Unique reference)
    ↓
QR Code Generation (Signed token matrix, Aadhaar-protected)
    ↓
Voter ID Card Generation (Official PDF card with ReportLab)
    ↓
Registration Completed (View, Download PDF, or Print Card)
```

---

## 🛡️ Data Protection & Privacy Notice
- Real Aadhaar numbers must **never** be entered. Use synthetic 12-digit test numbers (e.g. `556677889900`).
- Identity numbers are stored exclusively as one-way SHA-256 hashes and displayed with masking (e.g. `XXXX-XXXX-9900`).
- The generated QR code contains a verified verification token and does not leak private demographic or biometric numbers.
