// VaultVote Webcam & Face Registration Module

let currentVoterId = null;
let clientStream = null;
let isDirectWebRTCMode = false;

function initFaceRegistration(voterId) {
  currentVoterId = voterId;

  const btnCapture = document.getElementById('btn-capture-face');
  const btnRetake = document.getElementById('btn-retake-face');
  const btnToggleSource = document.getElementById('btn-toggle-cam-source');
  const imgStream = document.getElementById('opencv-stream-img');
  const videoElem = document.getElementById('webrtc-video');
  const canvasElem = document.getElementById('face-canvas');
  const capturedPreview = document.getElementById('captured-face-preview');
  const faceStatusMsg = document.getElementById('face-status-alert');

  // Handle Capture button click
  if (btnCapture) {
    btnCapture.addEventListener('click', function () {
      btnCapture.disabled = true;
      btnCapture.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Capturing Photo...';

      let payload = {};

      if (isDirectWebRTCMode && videoElem && clientStream) {
        // Grab frame from client HTML5 video element
        const ctx = canvasElem.getContext('2d');
        canvasElem.width = videoElem.videoWidth || 640;
        canvasElem.height = videoElem.videoHeight || 480;
        ctx.drawImage(videoElem, 0, 0, canvasElem.width, canvasElem.height);
        const dataUrl = canvasElem.toDataURL('image/jpeg', 0.92);
        payload.image_base64 = dataUrl;
        sendFaceCaptureRequest(payload);
      } else {
        // Backend captures directly from OpenCV VideoCapture(0)
        sendFaceCaptureRequest(payload);
      }
    });
  }

  // Handle Retake button click
  if (btnRetake) {
    btnRetake.addEventListener('click', function () {
      if (capturedPreview) capturedPreview.style.display = 'none';
      if (isDirectWebRTCMode) {
        if (videoElem) videoElem.style.display = 'block';
      } else {
        if (imgStream) {
          imgStream.style.display = 'block';
          imgStream.src = `/video_feed?t=${Date.now()}`;
        }
      }
      btnRetake.style.display = 'none';
      if (btnCapture) {
        btnCapture.style.display = 'inline-block';
        btnCapture.disabled = false;
        btnCapture.innerHTML = '<i class="bi bi-camera-fill me-2"></i>Capture Photo';
      }
      if (faceStatusMsg) {
        faceStatusMsg.style.display = 'none';
      }
    });
  }

  // Handle WebRTC Browser Mode toggle
  if (btnToggleSource) {
    btnToggleSource.addEventListener('click', function () {
      if (!isDirectWebRTCMode) {
        startBrowserWebRTC();
      } else {
        stopBrowserWebRTC();
      }
    });
  }

  function startBrowserWebRTC() {
    navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
      .then(stream => {
        clientStream = stream;
        videoElem.srcObject = stream;
        videoElem.play();
        videoElem.style.display = 'block';
        if (imgStream) imgStream.style.display = 'none';
        isDirectWebRTCMode = true;
        btnToggleSource.textContent = "Switch to Backend Camera";
      })
      .catch(err => {
        console.error("Webcam access error:", err);
        showCameraError("Camera permission denied or camera device in use by another application.");
      });
  }

  function stopBrowserWebRTC() {
    if (clientStream) {
      clientStream.getTracks().forEach(track => track.stop());
      clientStream = null;
    }
    if (videoElem) videoElem.style.display = 'none';
    if (imgStream) {
      imgStream.style.display = 'block';
      imgStream.src = `/video_feed?t=${Date.now()}`;
    }
    isDirectWebRTCMode = false;
    btnToggleSource.textContent = "Switch to WebRTC Camera";
  }

  function sendFaceCaptureRequest(payload) {
    fetch(`/api/face/capture/${currentVoterId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        btnCapture.disabled = false;
        if (data.success) {
          // Hide live video, show frozen preview
          if (imgStream) imgStream.style.display = 'none';
          if (videoElem) videoElem.style.display = 'none';
          if (capturedPreview) {
            capturedPreview.src = `${data.photo_url}?t=${Date.now()}`;
            capturedPreview.style.display = 'block';
          }

          // Show clean success message
          if (faceStatusMsg) {
            faceStatusMsg.className = "alert alert-success d-flex align-items-center mt-3 shadow-sm";
            faceStatusMsg.innerHTML = `
              <i class="bi bi-check-circle-fill fs-3 text-success me-3"></i>
              <div>
                <strong class="fs-6">Photo Captured Successfully</strong>
                <div class="small text-muted">Facial biometric template recorded and linked to Voter ID: <strong>${currentVoterId}</strong></div>
              </div>
            `;
            faceStatusMsg.style.display = 'flex';
          }

          // Swap buttons
          btnCapture.style.display = 'none';
          if (btnRetake) btnRetake.style.display = 'inline-block';

          // Update step indicator and check overall completion
          const faceStepBadge = document.getElementById('badge-face-step');
          if (faceStepBadge) {
            faceStepBadge.className = 'badge bg-success';
            faceStepBadge.textContent = 'Enrolled';
          }
          checkBiometricReadiness();
        } else {
          btnCapture.innerHTML = '<i class="bi bi-camera-fill me-2"></i>Capture Photo';
          showCameraError(data.message || "Failed to capture face photograph.");
        }
      })
      .catch(err => {
        btnCapture.disabled = false;
        btnCapture.innerHTML = '<i class="bi bi-camera-fill me-2"></i>Capture Photo';
        showCameraError("Network error while communicating with face biometric service: " + err.message);
      });
  }

  function showCameraError(msg) {
    if (faceStatusMsg) {
      faceStatusMsg.className = "alert alert-danger d-flex align-items-center mt-3 shadow-sm";
      faceStatusMsg.innerHTML = `
        <i class="bi bi-exclamation-octagon-fill fs-3 text-danger me-3"></i>
        <div>
          <strong>Camera Notice:</strong> ${msg}
          <div class="small text-muted">Please verify your laptop webcam permissions or try switching camera mode.</div>
        </div>
      `;
      faceStatusMsg.style.display = 'flex';
    }
  }
}
