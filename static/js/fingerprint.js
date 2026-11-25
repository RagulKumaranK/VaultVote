// VaultVote Biometric Fingerprint Enrollment Module

function initFingerprintSimulation(voterId) {
  const btnStartScan = document.getElementById('btn-start-fp-scan');
  const sensorPlate = document.getElementById('fp-sensor-plate');
  const progressBar = document.getElementById('fp-progress-bar');
  const progressContainer = document.getElementById('fp-progress-container');
  const statusStageText = document.getElementById('fp-status-stage-text');
  const resultPanel = document.getElementById('fp-result-panel');
  const resultRef = document.getElementById('fp-result-ref');
  const resultPattern = document.getElementById('fp-result-pattern');
  const resultMinutiae = document.getElementById('fp-result-minutiae');
  const resultQuality = document.getElementById('fp-result-quality');

  if (!btnStartScan) return;

  btnStartScan.addEventListener('click', function () {
    btnStartScan.disabled = true;
    btnStartScan.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Scanning Fingerprint...';
    
    // Start visual scanning state
    if (sensorPlate) sensorPlate.classList.add('scanning');
    if (progressContainer) progressContainer.style.display = 'block';
    if (resultPanel) resultPanel.style.display = 'none';

    // Play subtle audio tone
    playBiometricScanTone();

    // Multi-stage progress
    updateProgress(20, "Detecting fingerprint on sensor...", () => {
      setTimeout(() => {
        updateProgress(55, "Analyzing ridge pattern and minutiae...", () => {
          setTimeout(() => {
            updateProgress(85, "Generating biometric template...", () => {
              setTimeout(() => {
                callFingerprintApi();
              }, 350);
            });
          }, 450);
        });
      }, 450);
    });
  });

  function updateProgress(percent, stageText, callback) {
    if (progressBar) {
      progressBar.style.width = `${percent}%`;
      progressBar.setAttribute('aria-valuenow', percent);
    }
    if (statusStageText) {
      statusStageText.textContent = stageText;
    }
    if (callback) callback();
  }

  function callFingerprintApi() {
    fetch(`/api/fingerprint/enroll/${voterId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
      .then(res => res.json())
      .then(data => {
        if (sensorPlate) sensorPlate.classList.remove('scanning');
        
        if (data.success) {
          updateProgress(100, "Fingerprint enrolled successfully.", null);
          playSuccessTone();

          btnStartScan.style.display = 'none';

          // Display biometric template details
          if (resultRef) resultRef.textContent = data.reference;
          if (resultPattern) resultPattern.textContent = data.pattern_type;
          if (resultMinutiae) resultMinutiae.textContent = `${data.minutiae_count} minutiae points`;
          if (resultQuality) resultQuality.textContent = `${data.quality_score}%`;
          if (resultPanel) resultPanel.style.display = 'block';

          // Update step badge
          const fpStepBadge = document.getElementById('badge-fp-step');
          if (fpStepBadge) {
            fpStepBadge.className = 'badge bg-success';
            fpStepBadge.textContent = 'Enrolled (Simulated)';
          }

          checkBiometricReadiness();
        } else {
          btnStartScan.disabled = false;
          btnStartScan.innerHTML = '<i class="bi bi-fingerprint me-2"></i>Scan Fingerprint (Simulated)';
          alert("Scan error: " + data.message);
        }
      })
      .catch(err => {
        if (sensorPlate) sensorPlate.classList.remove('scanning');
        btnStartScan.disabled = false;
        btnStartScan.innerHTML = '<i class="bi bi-fingerprint me-2"></i>Scan Fingerprint (Simulated)';
        alert("Network communication error: " + err.message);
      });
  }

  // Audio feedback
  function playBiometricScanTone() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.35);
    } catch (e) {
      // Audio optional
    }
  }

  function playSuccessTone() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime);
      osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.15);
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.45);
    } catch (e) {}
  }
}

// Helper to check if both Face and Fingerprint steps are complete
function checkBiometricReadiness() {
  const faceBadge = document.getElementById('badge-face-step');
  const fpBadge = document.getElementById('badge-fp-step');
  const btnFinalize = document.getElementById('btn-finalize-registration');
  const finalizeNotice = document.getElementById('finalize-status-notice');

  const faceDone = faceBadge && (faceBadge.textContent.includes('Enrolled') || faceBadge.classList.contains('bg-success'));
  const fpDone = fpBadge && (fpBadge.textContent.includes('Enrolled') || fpBadge.classList.contains('bg-success'));

  if (faceDone && fpDone) {
    if (btnFinalize) {
      btnFinalize.disabled = false;
      btnFinalize.classList.remove('btn-secondary');
      btnFinalize.classList.add('btn-vv-success');
    }
    if (finalizeNotice) {
      finalizeNotice.innerHTML = `
        <div class="alert alert-success d-flex align-items-center justify-content-center shadow-sm">
          <i class="bi bi-shield-check fs-3 me-3 text-success"></i>
          <div class="text-start">
            <strong class="d-block">Biometrics Completed</strong>
            <span class="small text-muted">Facial photo and fingerprint enrollment verified. You can now generate the official Voter ID card.</span>
          </div>
        </div>
      `;
    }
  }
}
