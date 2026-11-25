/**
 * VaultVote - Kiosk Voting Controller
 * Handles Fullscreen Kiosk Mode, Optical QR Scanner, jsQR Decoding,
 * Biometric Face & Fingerprint Verification, Digital EVM Ballot Unit,
 * and VVPAT Audit Confirmation.
 */

// ================= AUDIO & VOICE ANNOUNCEMENT SYSTEM =================
/**
 * Centralized Audio & Speech Synthesis Controller
 * Powers laptop built-in speaker playback using Web Audio API and Web Speech API.
 * Features Indian English female voice selection, speech queueing, tone synthesis,
 * autoplay restriction resolution, and duplicate announcement prevention.
 */
const VotingAudio = (function () {
  let audioCtx = null;
  let isUnlocked = false;
  let isAudioEnabled = true;
  let speechQueue = [];
  let isSpeaking = false;
  let currentAudio = null;
  let bestVoice = null;
  let hasAnnouncedWelcome = false;
  let lastAnnouncedState = null;
  let lastAnnouncementTime = 0;
  const audioPreloadCache = {};

  // Studio-Quality Neural Indian English (en-IN-NeerjaNeural) Audio Map
  const NEURAL_AUDIO_MAP = {
    'WELCOME': '/static/audio/welcome.mp3',
    'QR_SUCCESS': '/static/audio/qr_success.mp3',
    'QR_INVALID': '/static/audio/qr_invalid.mp3',
    'ALREADY_VOTED': '/static/audio/already_voted.mp3',
    'FACE_PROMPT': '/static/audio/face_prompt.mp3',
    'FACE_SUCCESS': '/static/audio/face_success.mp3',
    'FACE_FAILED': '/static/audio/face_failed.mp3',
    'CANDIDATE_PROMPT': '/static/audio/candidate_prompt.mp3',
    'VOTE_RECORDED': '/static/audio/vote_recorded.mp3'
  };

  // Preload audio assets into browser cache for instantaneous zero-latency playback
  function preloadNeuralAudio() {
    Object.entries(NEURAL_AUDIO_MAP).forEach(([key, src]) => {
      try {
        const audio = new Audio();
        audio.preload = 'auto';
        audio.src = src;
        audioPreloadCache[key] = audio;
      } catch (e) { }
    });
  }

  // 1. Get or create single persistent AudioContext
  function getAudioContext() {
    if (!audioCtx) {
      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      if (AudioCtxClass) {
        audioCtx = new AudioCtxClass();
      } else {
        console.warn("Web Audio API is not supported in this browser.");
      }
    }
    return audioCtx;
  }

  // 2. Initialize & unlock AudioContext on first user interaction
  async function initializeAudio() {
    const ctx = getAudioContext();
    if (!ctx) return false;

    if (ctx.state === 'suspended') {
      try {
        await ctx.resume();
      } catch (err) {
        console.warn("AudioContext resume failed:", err);
      }
    }

    if (ctx.state === 'running' && !isUnlocked) {
      try {
        // Play silent 1-sample buffer to warm up audio output to laptop speakers
        const buffer = ctx.createBuffer(1, 1, 22050);
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(ctx.destination);
        source.start(0);
        isUnlocked = true;
        console.log("ValutVote audio pipeline primed for laptop speakers.");
      } catch (err) {
        console.warn("Audio priming buffer error:", err);
      }
    }

    // Preload studio neural announcements
    preloadNeuralAudio();

    // Initialize Web Speech fallback voice selection
    initVoice();

    // Trigger welcome announcement if pending on Step 1
    if (!hasAnnouncedWelcome) {
      const sec1 = document.getElementById('sectionStep1');
      if (sec1 && !sec1.classList.contains('d-none')) {
        announceWelcome();
      }
    }

    updateAudioStatusUi();
    return true;
  }

  // 3. Select best Indian English Female voice (or natural female fallback)
  function initVoice() {
    if (!('speechSynthesis' in window)) {
      console.warn("Web Speech API speechSynthesis is not supported.");
      return;
    }

    function selectVoice() {
      const voices = window.speechSynthesis.getVoices();
      if (!voices || voices.length === 0) return;

      // 1. Priority: English (India) natural female voice
      let match = voices.find(v =>
        (v.lang === 'en-IN' || v.lang === 'en_IN') &&
        /female|natural|neerja|swara|heera|veena|ananya|priya|geeta|sunita/i.test(v.name)
      );

      // 2. Any English (India) voice
      if (!match) {
        match = voices.find(v => v.lang === 'en-IN' || v.lang === 'en_IN');
      }

      // 3. Any professional natural English female voice
      if (!match) {
        match = voices.find(v =>
          v.lang.toLowerCase().startsWith('en') &&
          /natural|neural|female|neerja|swara|heera|zira|samantha|karen|victoria|catherine|jenny|aria|google uk english female/i.test(v.name)
        );
      }

      // 4. Any English voice
      if (!match) {
        match = voices.find(v => v.lang.toLowerCase().startsWith('en'));
      }

      bestVoice = match || voices.find(v => v.default) || voices[0];
      if (bestVoice) {
        console.log("VotingAudio fallback speech voice:", `${bestVoice.name} (${bestVoice.lang})`);
      }
    }

    selectVoice();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = selectVoice;
    }
  }

  // 4. Speak Announcement with queueing, no overlap, and error handling
  function speakAnnouncement(text, options = {}) {
    if (!isAudioEnabled) return;
    if (!text || typeof text !== 'string') return;

    const {
      priority = false, // If true, clears current queue and speaks immediately
      onEnd = null,
      cooldown = 0,     // Min ms between identical announcements
      stateKey = null,  // State identifier to prevent webcam frame repetitive spam
      audioKey = null   // Override key into NEURAL_AUDIO_MAP
    } = options;

    const now = Date.now();
    if (stateKey && lastAnnouncedState === stateKey && cooldown > 0) {
      if (now - lastAnnouncementTime < cooldown) {
        return; // Suppress duplicate announcement in same state
      }
    }

    if (priority) {
      speechQueue = [];
      if (currentAudio) {
        try {
          currentAudio.pause();
          currentAudio.currentTime = 0;
        } catch (e) { }
        currentAudio = null;
      }
      if ('speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
        } catch (e) { }
      }
      isSpeaking = false;
    }

    const item = { text, onEnd, stateKey, audioKey, timestamp: now };

    if (isSpeaking && !priority) {
      const alreadyQueued = speechQueue.some(q => q.text === text);
      if (!alreadyQueued) {
        speechQueue.push(item);
      }
      return;
    }

    executeSpeak(item);
  }

  function executeSpeak(item) {
    if (!isAudioEnabled) return;

    isSpeaking = true;
    lastAnnouncedState = item.stateKey;
    lastAnnouncementTime = Date.now();

    // Primary: Play High-Quality Studio Neural Audio File
    const resolvedKey = item.audioKey || item.stateKey;
    const audioUrl = NEURAL_AUDIO_MAP[resolvedKey];

    if (audioUrl) {
      playNeuralAudio(audioUrl, item);
    } else {
      executeSpeechSynthesis(item);
    }
  }

  function playNeuralAudio(audioUrl, item) {
    try {
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      }

      const audio = new Audio(audioUrl);
      currentAudio = audio;
      audio.volume = 1.0; // Play cleanly at full volume through laptop speakers

      audio.onended = () => {
        isSpeaking = false;
        currentAudio = null;
        if (typeof item.onEnd === 'function') {
          try { item.onEnd(); } catch (e) { console.error(e); }
        }
        // Process next item in speech queue after a natural pause
        if (speechQueue.length > 0) {
          const nextItem = speechQueue.shift();
          setTimeout(() => executeSpeak(nextItem), 200);
        }
      };

      audio.onerror = (err) => {
        console.warn("Neural audio playback notice, falling back to speech synthesis:", err);
        currentAudio = null;
        executeSpeechSynthesis(item);
      };

      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.catch((err) => {
          console.warn("Neural audio play deferred, falling back to speech synthesis:", err);
          currentAudio = null;
          executeSpeechSynthesis(item);
        });
      }
    } catch (err) {
      console.warn("playNeuralAudio exception, falling back to speech synthesis:", err);
      currentAudio = null;
      executeSpeechSynthesis(item);
    }
  }

  // Phonetic text normalization for distinct "Valut Vote", "Q R", "Voter I D" pronunciation
  function getPhoneticSpeechText(raw) {
    if (!raw) return '';
    return raw
      .replace(/ValutVote/gi, "Valut Vote")
      .replace(/\bQR\b/g, "Q R")
      .replace(/\bVoter ID\b/gi, "Voter I D");
  }

  // Fallback: Web Speech API with calm Indian English female cadence
  function executeSpeechSynthesis(item) {
    if (!isAudioEnabled || !('speechSynthesis' in window)) {
      isSpeaking = false;
      return;
    }

    try {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
    } catch (e) { }

    const phoneticText = getPhoneticSpeechText(item.text);
    const utterance = new SpeechSynthesisUtterance(phoneticText);
    if (!bestVoice) initVoice();

    if (bestVoice) {
      utterance.voice = bestVoice;
      utterance.lang = bestVoice.lang || 'en-IN';
    } else {
      utterance.lang = 'en-IN';
    }

    // Professional female announcement cadence
    utterance.rate = 0.90;   // Calm, professional, government announcement pace
    utterance.pitch = 1.0;   // Natural, non-robotic, non-metallic tone
    utterance.volume = 1.0;  // Full laptop speaker volume

    utterance.onend = () => {
      isSpeaking = false;
      if (typeof item.onEnd === 'function') {
        try { item.onEnd(); } catch (e) { console.error(e); }
      }
      // Process next announcement in queue with a natural pause
      if (speechQueue.length > 0) {
        const nextItem = speechQueue.shift();
        setTimeout(() => executeSpeak(nextItem), 220);
      }
    };

    utterance.onerror = (err) => {
      console.warn("Speech synthesis notice:", err);
      isSpeaking = false;
      if (speechQueue.length > 0) {
        const nextItem = speechQueue.shift();
        setTimeout(() => executeSpeak(nextItem), 220);
      }
    };

    try {
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn("Failed to speak announcement:", err);
      isSpeaking = false;
    }
  }

  // 5. Stop all voice announcements and clear queue
  function stopAnnouncement() {
    speechQueue = [];
    isSpeaking = false;
    if (currentAudio) {
      try {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      } catch (e) { }
      currentAudio = null;
    }
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) { }
    }
  }

  // 6. Sound Effect: Success Beep (Single short, clean confirmation beep: 1000Hz, 140ms)
  function playSuccessBeep(frequency = 1000, duration = 140) {
    if (!isAudioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      if (ctx.state === 'suspended') ctx.resume();

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(frequency, now);

      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.linearRampToValueAtTime(0.32, now + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + (duration / 1000));

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + (duration / 1000) + 0.02);
    } catch (e) {
      console.warn("playSuccessBeep error:", e);
    }
  }

  // 7. Sound Effect: Error Sound (Distinct low-pitched descending tone: 280Hz -> 160Hz)
  function playErrorSound() {
    if (!isAudioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      if (ctx.state === 'suspended') ctx.resume();

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(280, now);
      osc.frequency.exponentialRampToValueAtTime(160, now + 0.26);

      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.linearRampToValueAtTime(0.28, now + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.28);

      const filter = ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(850, now);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.30);
    } catch (e) {
      console.warn("playErrorSound error:", e);
    }
  }

  // 8. Sound Effect: Already Voted Double Warning Alert (Two distinct short warning tones)
  function playAlreadyVotedAlert() {
    if (!isAudioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      if (ctx.state === 'suspended') ctx.resume();

      const now = ctx.currentTime;

      // Pulse 1: 440Hz -> 320Hz (0.00s to 0.12s)
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = 'sawtooth';
      osc1.frequency.setValueAtTime(440, now);
      osc1.frequency.linearRampToValueAtTime(320, now + 0.12);
      gain1.gain.setValueAtTime(0.0001, now);
      gain1.gain.linearRampToValueAtTime(0.32, now + 0.01);
      gain1.gain.exponentialRampToValueAtTime(0.0001, now + 0.12);

      const f1 = ctx.createBiquadFilter();
      f1.type = 'lowpass';
      f1.frequency.setValueAtTime(1100, now);
      osc1.connect(f1);
      f1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.13);

      // Pulse 2: 440Hz -> 260Hz after 60ms pause (0.18s to 0.32s)
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'sawtooth';
      osc2.frequency.setValueAtTime(440, now + 0.18);
      osc2.frequency.linearRampToValueAtTime(260, now + 0.32);
      gain2.gain.setValueAtTime(0.0001, now + 0.18);
      gain2.gain.linearRampToValueAtTime(0.34, now + 0.19);
      gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.32);

      const f2 = ctx.createBiquadFilter();
      f2.type = 'lowpass';
      f2.frequency.setValueAtTime(1100, now + 0.18);
      osc2.connect(f2);
      f2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(now + 0.18);
      osc2.stop(now + 0.33);

      // Low foundation alert sub-note (200Hz, 0.36s to 0.52s)
      const osc3 = ctx.createOscillator();
      const gain3 = ctx.createGain();
      osc3.type = 'sine';
      osc3.frequency.setValueAtTime(200, now + 0.36);
      gain3.gain.setValueAtTime(0.0001, now + 0.36);
      gain3.gain.linearRampToValueAtTime(0.24, now + 0.37);
      gain3.gain.exponentialRampToValueAtTime(0.0001, now + 0.52);

      osc3.connect(gain3);
      gain3.connect(ctx.destination);
      osc3.start(now + 0.36);
      osc3.stop(now + 0.53);
    } catch (e) {
      console.warn("playAlreadyVotedAlert error:", e);
    }
  }

  // 9. Sound Effect: Vote Success Chime (Pleasant two-note chime: C5 523Hz -> G5 784Hz)
  function playVoteSuccessChime() {
    if (!isAudioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      if (ctx.state === 'suspended') ctx.resume();

      const now = ctx.currentTime;

      // Note 1: C5 (523.25 Hz) bell sine
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(523.25, now);
      gain1.gain.setValueAtTime(0.0001, now);
      gain1.gain.linearRampToValueAtTime(0.28, now + 0.02);
      gain1.gain.exponentialRampToValueAtTime(0.0001, now + 0.30);
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.32);

      // Note 2: G5 (783.99 Hz) harmonious chime
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(783.99, now + 0.16);
      gain2.gain.setValueAtTime(0.0001, now + 0.16);
      gain2.gain.linearRampToValueAtTime(0.35, now + 0.18);
      gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.65);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(now + 0.16);
      osc2.stop(now + 0.68);
    } catch (e) {
      console.warn("playVoteSuccessChime error:", e);
    }
  }

  // 10. Sound Effect: EVM Continuous Buzzer Tone (950Hz)
  function playEvmBeep(duration = 800) {
    if (!isAudioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      if (ctx.state === 'suspended') ctx.resume();

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(950, now);
      gain.gain.setValueAtTime(0.22, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + (duration / 1000));
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + (duration / 1000) + 0.05);
    } catch (e) {
      console.warn("playEvmBeep error:", e);
    }
  }

  // 11. Sound Effect: Processing Chirp (Subtle 600-850Hz biometrics blip)
  function playProcessingChirp() {
    if (!isAudioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      if (ctx.state === 'suspended') ctx.resume();

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(600, now);
      osc.frequency.exponentialRampToValueAtTime(850, now + 0.08);
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.linearRampToValueAtTime(0.12, now + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.10);
    } catch (e) { }
  }

  // Pre-configured workflow announcements:
  function announceWelcome() {
    hasAnnouncedWelcome = true;
    speakAnnouncement("Welcome to ValutVote. Please scan your Voter ID QR code.", {
      priority: true,
      stateKey: 'WELCOME',
      cooldown: 6000
    });
  }

  function announceQrSuccess() {
    speakAnnouncement("QR code verified successfully.", {
      priority: true,
      stateKey: 'QR_SUCCESS',
      cooldown: 2000
    });
  }

  function announceInvalidQr() {
    speakAnnouncement("Invalid QR code. Please try again.", {
      priority: true,
      stateKey: 'QR_INVALID',
      cooldown: 3500
    });
  }

  function announceAlreadyVoted() {
    speakAnnouncement("Alert! This voter has already cast their vote.", {
      priority: true,
      stateKey: 'ALREADY_VOTED',
      cooldown: 4000
    });
  }

  function announceLookAtCamera() {
    speakAnnouncement("Please look at the camera for face verification.", {
      priority: false, // Queued after QR success
      stateKey: 'FACE_PROMPT',
      cooldown: 3000
    });
  }

  function announceFaceSuccess() {
    speakAnnouncement("Face verification successful.", {
      priority: true,
      stateKey: 'FACE_SUCCESS',
      cooldown: 2000
    });
  }

  function announceFaceFailed() {
    speakAnnouncement("Face verification failed. Please try again.", {
      priority: true,
      stateKey: 'FACE_FAILED',
      cooldown: 3500
    });
  }

  function announceSelectCandidate() {
    speakAnnouncement("Identity verified. Please select your preferred candidate.", {
      priority: false, // Queued after Face success
      stateKey: 'CANDIDATE_PROMPT',
      cooldown: 3000
    });
  }

  function announceVoteRecorded() {
    speakAnnouncement("Your vote has been recorded successfully. Thank you for voting.", {
      priority: true,
      stateKey: 'VOTE_RECORDED',
      cooldown: 5000
    });
  }

  function resetWelcomeFlag() {
    hasAnnouncedWelcome = false;
    lastAnnouncedState = null;
    lastAnnouncementTime = 0;
  }

  function toggleAudio() {
    isAudioEnabled = !isAudioEnabled;
    if (!isAudioEnabled) {
      stopAnnouncement();
    } else {
      initializeAudio();
    }
    updateAudioStatusUi();
    return isAudioEnabled;
  }

  function updateAudioStatusUi() {
    const icon = document.getElementById('audioIcon');
    const text = document.getElementById('audioText');
    if (icon && text) {
      if (isAudioEnabled) {
        icon.className = 'bi bi-volume-up-fill text-success fs-6';
        text.textContent = 'Voice Active';
      } else {
        icon.className = 'bi bi-volume-mute-fill text-secondary fs-6';
        text.textContent = 'Voice Muted';
      }
    }
  }

  return {
    initializeAudio,
    speakAnnouncement,
    stopAnnouncement,
    playSuccessBeep,
    playErrorSound,
    playAlreadyVotedAlert,
    playVoteSuccessChime,
    playEvmBeep,
    playProcessingChirp,
    announceWelcome,
    announceQrSuccess,
    announceInvalidQr,
    announceAlreadyVoted,
    announceLookAtCamera,
    announceFaceSuccess,
    announceFaceFailed,
    announceSelectCandidate,
    announceVoteRecorded,
    resetWelcomeFlag,
    toggleAudio
  };
})();

// Backward-compatible global wrappers delegating to VotingAudio
function playSingleBeep(frequency = 1000, duration = 140) {
  VotingAudio.playSuccessBeep(frequency, duration);
}

function playWarningAlertSound() {
  VotingAudio.playAlreadyVotedAlert();
}

function playEvmBeep(duration = 800) {
  VotingAudio.playEvmBeep(duration);
}

// Global convenience exposure
window.VotingAudio = VotingAudio;

// State Variables & Persistent Kiosk Session State
const KIOSK_STORAGE_KEY = 'vaultvote_kiosk_state';
let kioskCurrentStep = 0;
let currentVoter = null;
let selectedCandidate = null;
let currentAuthMode = 'qr';
let currentVvpatReceipt = null;
let videoStream = null;
let qrStream = null;
let qrScanInterval = null;
let isProcessingQr = false;
let barcodeDetector = null;

// ================= KIOSK SESSION PERSISTENCE & NAVIGATION CONTROLLER =================
function saveKioskState(stepNumber, additionalData = {}) {
  try {
    const step = (typeof stepNumber === 'number') ? stepNumber : kioskCurrentStep;
    kioskCurrentStep = step;
    const existing = getSavedKioskState() || {};
    const inputEl = document.getElementById('voterInput');
    const stateToSave = {
      ...existing,
      currentStep: step,
      currentVoter: currentVoter || existing.currentVoter || null,
      authMode: currentAuthMode || existing.authMode || 'qr',
      selectedCandidate: (step === 3) ? (selectedCandidate || existing.selectedCandidate || null) : null,
      vvpatReceipt: (step === 4) ? (currentVvpatReceipt || existing.vvpatReceipt || null) : null,
      manualVoterInput: (inputEl ? inputEl.value : '') || existing.manualVoterInput || '',
      timestamp: Date.now(),
      ...additionalData
    };
    localStorage.setItem(KIOSK_STORAGE_KEY, JSON.stringify(stateToSave));
  } catch (err) {
    console.warn("Unable to save kiosk state:", err);
  }
}

function clearKioskState() {
  try {
    localStorage.removeItem(KIOSK_STORAGE_KEY);
  } catch (err) {
    console.warn("Unable to clear kiosk state:", err);
  }
}

function getSavedKioskState() {
  try {
    const raw = localStorage.getItem(KIOSK_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (err) {
    console.warn("Unable to read saved kiosk state:", err);
    return null;
  }
}

function setKioskHeaderControls(step) {
  const topControls = document.getElementById('kioskTopControls');
  const activeBadge = document.getElementById('kioskActiveBadge');

  if (step === 0) {
    document.body.classList.add('is-step-leading');
    if (topControls) {
      topControls.classList.remove('d-none');
      topControls.classList.add('d-flex');
    }
    if (activeBadge) {
      activeBadge.classList.add('d-none');
      activeBadge.classList.remove('d-flex');
    }
  } else {
    document.body.classList.remove('is-step-leading');
    if (topControls) {
      topControls.classList.remove('d-flex');
      topControls.classList.add('d-none');
    }
    if (activeBadge) {
      activeBadge.classList.remove('d-none');
      activeBadge.classList.add('d-flex');
    }
  }
}

function populateVoterProfile(voter) {
  if (!voter) return;
  const nameEl = document.getElementById('voterProfileName');
  if (nameEl) nameEl.textContent = voter.full_name || 'Voter';
  const idEl = document.getElementById('voterProfileId');
  if (idEl) idEl.textContent = voter.voter_id || '';
  const genEl = document.getElementById('voterProfileGender');
  if (genEl) genEl.textContent = voter.gender || '';
  const ageEl = document.getElementById('voterProfileAge');
  if (ageEl) ageEl.textContent = voter.age || '';
  const locEl = document.getElementById('voterProfileLocation');
  if (locEl) locEl.textContent = `${voter.district || ''}, ${voter.state || ''} - ${voter.pincode || ''}`;

  const photoEl = document.getElementById('voterProfilePhoto');
  if (photoEl) {
    if (voter.photo_path) {
      photoEl.src = '/static/' + voter.photo_path;
    } else {
      photoEl.src = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='70' height='85' fill='%2394a3b8'><rect width='70' height='85' fill='%23f1f5f9'/></svg>";
    }
  }
}

function handleLogoClick(event) {
  const state = getSavedKioskState();
  const step = (state && typeof state.currentStep === 'number') ? state.currentStep : kioskCurrentStep;
  if (step > 0) {
    if (event) event.preventDefault();
    console.log("VaultVote logo clicked - session in progress, maintaining active step:", step);
    restoreKioskState();
    return false;
  }
  // On step 0 (Start Screen), stay on step 0 without unnecessary reload
  if (event) event.preventDefault();
}
window.handleLogoClick = handleLogoClick;

function restoreKioskState() {
  const state = getSavedKioskState();
  const secLeading = document.getElementById('sectionLeading');
  const sec1 = document.getElementById('sectionStep1');
  const sec2 = document.getElementById('sectionStep2');
  const sec3 = document.getElementById('sectionStep3');
  const sec4 = document.getElementById('sectionStep4');

  const hideAllSections = () => {
    if (secLeading) secLeading.classList.add('d-none');
    if (sec1) sec1.classList.add('d-none');
    if (sec2) sec2.classList.add('d-none');
    if (sec3) sec3.classList.add('d-none');
    if (sec4) sec4.classList.add('d-none');
  };

  if (!state || typeof state.currentStep !== 'number' || state.currentStep === 0) {
    kioskCurrentStep = 0;
    currentVoter = null;
    selectedCandidate = null;
    currentVvpatReceipt = null;
    hideAllSections();
    if (secLeading) secLeading.classList.remove('d-none');
    setKioskHeaderControls(0);
    return;
  }

  kioskCurrentStep = state.currentStep;
  setKioskHeaderControls(kioskCurrentStep);

  if (state.currentVoter) {
    currentVoter = state.currentVoter;
  }
  if (state.vvpatReceipt) {
    currentVvpatReceipt = state.vvpatReceipt;
  }

  hideAllSections();

  if (state.currentStep === 1) {
    if (sec1) sec1.classList.remove('d-none');
    const mode = state.authMode || 'qr';
    currentAuthMode = mode;
    switchAuthMode(mode);
    if (mode === 'manual' && state.manualVoterInput) {
      const input = document.getElementById('voterInput');
      if (input) input.value = state.manualVoterInput;
    }
  } else if (state.currentStep === 2) {
    if (!currentVoter || !currentVoter.voter_id) {
      saveKioskState(1);
      restoreKioskState();
      return;
    }
    if (sec2) sec2.classList.remove('d-none');
    populateVoterProfile(currentVoter);
    stopQrScanner();
    startKioskCamera();
  } else if (state.currentStep === 3) {
    if (!currentVoter || !currentVoter.voter_id) {
      saveKioskState(1);
      restoreKioskState();
      return;
    }
    if (sec3) sec3.classList.remove('d-none');
    stopKioskCamera();
    stopQrScanner();

    // Reopen confirmation modal if was open
    if (state.isConfirmModalOpen && state.selectedCandidate) {
      const sc = state.selectedCandidate;
      setTimeout(() => {
        promptCastVote(sc.id, sc.name, sc.party, sc.symbol, sc.banner || '', sc.symbolImg || '');
      }, 150);
    }
  } else if (state.currentStep === 4) {
    if (sec4) sec4.classList.remove('d-none');
    stopKioskCamera();
    stopQrScanner();
    if (state.vvpatReceipt) {
      showStep4Confirmation(state.vvpatReceipt);
    }
  }
}

// ================= [DEV ONLY] STEP BACK CONTROLLER =================
// Temporary development helper: remove once product is complete
function devGoBack() {
  console.log("[DEV] Moving back from step", kioskCurrentStep);
  hideKioskAlert();

  if (kioskCurrentStep === 4) {
    saveKioskState(3, { isConfirmModalOpen: false, selectedCandidate: null });
    restoreKioskState();
  } else if (kioskCurrentStep === 3) {
    saveKioskState(2);
    restoreKioskState();
  } else if (kioskCurrentStep === 2) {
    stopKioskCamera();
    saveKioskState(1);
    restoreKioskState();
  } else if (kioskCurrentStep === 1) {
    stopQrScanner();
    saveKioskState(0);
    restoreKioskState();
  }
}
window.devGoBack = devGoBack;

// Check Native BarcodeDetector API in Chromium
if ('BarcodeDetector' in window) {
  try {
    barcodeDetector = new BarcodeDetector({ formats: ['qr_code'] });
  } catch (e) {
    barcodeDetector = null;
  }
}

// ================= FULLSCREEN KIOSK MODE CONTROLLER =================
function requestKioskFullscreen() {
  if (!document.fullscreenElement && !document.webkitFullscreenElement) {
    const el = document.documentElement;
    if (el.requestFullscreen) {
      el.requestFullscreen().catch(err => {
        console.log("Automatic fullscreen deferred until user interaction:", err);
      });
    } else if (el.webkitRequestFullscreen) {
      el.webkitRequestFullscreen().catch(err => { });
    }
  }
}

function toggleKioskFullscreen() {
  if (!document.fullscreenElement && !document.webkitFullscreenElement) {
    const el = document.documentElement;
    if (el.requestFullscreen) el.requestFullscreen();
    else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
  } else {
    if (document.exitFullscreen) document.exitFullscreen();
    else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
  }
}

function updateFullscreenUi() {
  const isFs = !!(document.fullscreenElement || document.webkitFullscreenElement);
  const fsIcon = document.getElementById('fsIcon');
  const fsText = document.getElementById('fsText');
  if (fsIcon && fsText) {
    if (isFs) {
      fsIcon.className = 'bi bi-fullscreen-exit';
      fsIcon.className = 'bi bi-fullscreen-exit fs-6';
      fsText.textContent = 'Exit Fullscreen';
    } else {
      fsIcon.className = 'bi bi-arrows-fullscreen';
      fsIcon.className = 'bi bi-arrows-fullscreen fs-6';
      fsText.textContent = 'Fullscreen';
    }
  }
}

document.addEventListener('fullscreenchange', updateFullscreenUi);
document.addEventListener('webkitfullscreenchange', updateFullscreenUi);

// Auto-enter fullscreen upon user landing & initialize audio pipeline and persistent session
window.addEventListener('DOMContentLoaded', () => {
  requestKioskFullscreen();
  VotingAudio.initializeAudio();
  setupEventListeners();
  restoreKioskState();
});

// Restore state from back-forward cache (bfcache) or navigation
window.addEventListener('pageshow', () => {
  restoreKioskState();
});

// Unlock audio and fullscreen on any user gesture (resolving browser autoplay restrictions)
['click', 'touchstart', 'keydown', 'pointerdown'].forEach(evt => {
  document.addEventListener(evt, () => {
    requestKioskFullscreen();
    VotingAudio.initializeAudio();
  }, { passive: true });
});

// UI Helper: Show alert banner
function showKioskAlert(type, message, iconClass = 'bi-info-circle-fill') {
  const banner = document.getElementById('kioskAlert');
  const icon = document.getElementById('kioskAlertIcon');
  const msg = document.getElementById('kioskAlertMsg');
  if (!banner || !icon || !msg) return;
  banner.className = `alert alert-${type} d-flex align-items-center gap-2 shadow-sm mb-4`;
  icon.className = `bi ${iconClass} fs-4`;
  msg.innerHTML = message;
  banner.classList.remove('d-none');
}

function hideKioskAlert() {
  const banner = document.getElementById('kioskAlert');
  if (banner) banner.classList.add('d-none');
}

// ================= STEP 0: START VOTING SESSION FROM LEADING PAGE =================
function startVotingSession() {
  requestKioskFullscreen();
  VotingAudio.initializeAudio();

  kioskCurrentStep = 1;
  currentAuthMode = 'qr';
  saveKioskState(1, { authMode: 'qr' });

  // Hide leading page and reveal Step 1
  const secLeading = document.getElementById('sectionLeading');
  const sec1 = document.getElementById('sectionStep1');
  if (secLeading) secLeading.classList.add('d-none');
  if (sec1) sec1.classList.remove('d-none');

  setKioskHeaderControls(1);

  // Play professional female welcome announcement
  VotingAudio.announceWelcome();

  // Activate QR scanner camera
  startQrScanner();
}

// ================= OPTICAL QR SCANNER LOGIC =================
function switchAuthMode(mode) {
  currentAuthMode = mode;
  const paneQr = document.getElementById('authModeQr');
  const paneManual = document.getElementById('authModeManual');
  const btnQr = document.getElementById('btnModeQr');
  const btnManual = document.getElementById('btnModeManual');

  if (mode === 'qr') {
    if (paneQr) paneQr.classList.remove('d-none');
    if (paneManual) paneManual.classList.add('d-none');
    if (btnQr) btnQr.classList.add('active');
    if (btnManual) btnManual.classList.remove('active');
    startQrScanner();
  } else {
    if (paneQr) paneQr.classList.add('d-none');
    if (paneManual) paneManual.classList.remove('d-none');
    if (btnQr) btnQr.classList.remove('active');
    if (btnManual) btnManual.classList.add('active');
    stopQrScanner();
    const input = document.getElementById('voterInput');
    if (input) input.focus();
  }

  if (kioskCurrentStep === 1) {
    const input = document.getElementById('voterInput');
    saveKioskState(1, { authMode: mode, manualVoterInput: (input ? input.value : '') });
  }
}

function updateQrCameraStatus(state) {
  const badge = document.getElementById('qrCameraStatusBadge');
  const label = document.getElementById('qrStatusBadge');
  const dot = document.getElementById('qrStatusDot');
  if (!label) return;

  if (state === 'active') {
    if (badge) badge.className = 'badge bg-light text-success border border-success-subtle px-3 py-1.5 rounded-pill d-inline-flex align-items-center gap-2';
    if (dot) {
      dot.style.background = '#16a34a';
      dot.style.boxShadow = '0 0 0 2px rgba(22, 163, 74, 0.25)';
      dot.style.display = 'inline-block';
      dot.style.marginRight = '6px';
    }
    label.textContent = 'Camera Active';
  } else if (state === 'starting') {
    if (badge) badge.className = 'badge bg-light text-primary border border-primary-subtle px-3 py-1.5 rounded-pill d-inline-flex align-items-center gap-2';
    if (dot) {
      dot.style.background = '#2563eb';
      dot.style.boxShadow = '0 0 0 2px rgba(37, 99, 235, 0.25)';
      dot.style.display = 'inline-block';
      dot.style.marginRight = '6px';
    }
    label.textContent = 'Connecting...';
  } else if (state === 'detected') {
    if (badge) badge.className = 'badge bg-light text-success border border-success-subtle px-3 py-1.5 rounded-pill d-inline-flex align-items-center gap-2';
    if (dot) {
      dot.style.background = '#16a34a';
      dot.style.boxShadow = '0 0 0 2px rgba(22, 163, 74, 0.25)';
      dot.style.display = 'inline-block';
      dot.style.marginRight = '6px';
    }
    label.textContent = 'QR Detected';
  } else if (state === 'inactive') {
    if (badge) badge.className = 'badge bg-light text-secondary border border-secondary-subtle px-3 py-1.5 rounded-pill d-inline-flex align-items-center gap-2';
    if (dot) {
      dot.style.background = '#94a3b8';
      dot.style.boxShadow = 'none';
      dot.style.display = 'inline-block';
      dot.style.marginRight = '6px';
    }
    label.textContent = 'Camera Inactive';
  } else if (state === 'error') {
    if (badge) badge.className = 'badge bg-light text-danger border border-danger-subtle px-3 py-1.5 rounded-pill d-inline-flex align-items-center gap-2';
    if (dot) {
      dot.style.background = '#dc2626';
      dot.style.boxShadow = '0 0 0 2px rgba(220, 38, 38, 0.25)';
      dot.style.display = 'inline-block';
      dot.style.marginRight = '6px';
    }
    label.textContent = 'Camera Offline';
  }
}

function handleScannerBoxClick() {
  const video = document.getElementById('qrScannerVideo');
  if (!qrStream || !video || video.paused || video.readyState < 2) {
    startQrScanner();
  }
}

async function startQrScanner() {
  stopQrScanner();
  isProcessingQr = false;
  const video = document.getElementById('qrScannerVideo');
  const feedbackMsg = document.getElementById('qrFeedbackMsg');
  const reticle = document.getElementById('qrTargetReticle');

  updateQrCameraStatus('starting');
  if (reticle) reticle.classList.remove('success', 'warning');
  const qrPrompt = document.getElementById('qrPromptText');
  if (qrPrompt) {
    qrPrompt.textContent = 'Hold Voter ID QR inside frame';
  }
  if (feedbackMsg) {
    feedbackMsg.innerHTML = '<span class="spinner-grow spinner-grow-sm text-primary"></span> <span>Position your Voter ID QR code in front of the camera</span>';
  }

  if (!video) return;

  try {
    // Progressive camera constraints (HD ideal for sharp QR detection)
    try {
      qrStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280, min: 640 },
          height: { ideal: 720, min: 480 },
          facingMode: 'user'
        },
        audio: false
      });
    } catch (e1) {
      console.warn("HD constraint failed, falling back to standard video device", e1);
      qrStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false
      });
    }

    video.srcObject = qrStream;
    video.muted = true;
    video.playsInline = true;

    video.onloadedmetadata = () => {
      video.play().then(() => {
        updateQrCameraStatus('active');
      }).catch(err => {
        console.log("Autoplay deferred:", err);
      });
    };

    try {
      await video.play();
      updateQrCameraStatus('active');
    } catch (playErr) {
      console.log("video.play() deferred:", playErr);
    }

    // Continuous scanning loop (every 260ms)
    qrScanInterval = setInterval(scanQrVideoFrame, 260);
  } catch (err) {
    console.warn("QR Camera scanner unavailable:", err);
    updateQrCameraStatus('error');
    if (feedbackMsg) {
      feedbackMsg.innerHTML = '<i class="bi bi-camera-video-off text-danger"></i> <span>Camera permission needed. Click restart or use Manual EPIC Input.</span>';
    }
  }
}

function stopQrScanner() {
  if (qrScanInterval) {
    clearInterval(qrScanInterval);
    qrScanInterval = null;
  }
  if (qrStream) {
    qrStream.getTracks().forEach(track => track.stop());
    qrStream = null;
  }
  const video = document.getElementById('qrScannerVideo');
  if (video) video.srcObject = null;
  updateQrCameraStatus('inactive');
}

async function scanQrVideoFrame() {
  if (isProcessingQr) return;
  const video = document.getElementById('qrScannerVideo');
  if (!video || video.readyState < 2 || video.videoWidth === 0) return;

  // 1. Try Native BarcodeDetector (instant 0ms in supported Chromium)
  if (barcodeDetector) {
    try {
      const codes = await barcodeDetector.detect(video);
      if (codes && codes.length > 0) {
        isProcessingQr = true;
        handleScannedQrToken(codes[0].rawValue);
        return;
      }
    } catch (e) { }
  }

  // 2. High-speed client-side jsQR (0ms sub-pixel local decoding)
  const vW = video.videoWidth || 640;
  const vH = video.videoHeight || 480;
  const scanCanvas = document.createElement('canvas');
  const targetW = Math.min(vW, 800);
  const targetH = Math.round(targetW * (vH / vW));
  scanCanvas.width = targetW;
  scanCanvas.height = targetH;
  const sCtx = scanCanvas.getContext('2d');
  sCtx.drawImage(video, 0, 0, targetW, targetH);

  if (window.jsQR) {
    try {
      const imgData = sCtx.getImageData(0, 0, targetW, targetH);
      const qrCode = jsQR(imgData.data, targetW, targetH, {
        inversionAttempts: "attemptBoth"
      });
      if (qrCode && qrCode.data) {
        isProcessingQr = true;
        handleScannedQrToken(qrCode.data);
        return;
      }
    } catch (e) { }
  }

  // 3. Multi-pass de-blur OpenCV backend fallback
  try {
    isProcessingQr = true;
    const b64 = scanCanvas.toDataURL('image/jpeg', 0.88);

    const res = await fetch('/api/voting/scan_qr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: b64 })
    });
    const data = await res.json();
    if (data.found && data.token) {
      handleScannedQrToken(data.token);
    } else {
      isProcessingQr = false;
    }
  } catch (err) {
    isProcessingQr = false;
  }
}

function handleScannedQrToken(rawToken) {
  if (!rawToken) {
    isProcessingQr = false;
    return;
  }

  const reticle = document.getElementById('qrTargetReticle');
  const feedbackMsg = document.getElementById('qrFeedbackMsg');
  const qrPrompt = document.getElementById('qrPromptText');

  // Visual acquisition indicators (Do NOT beep here until eligibility is verified)
  if (reticle) reticle.classList.add('success');
  updateQrCameraStatus('detected');
  if (qrPrompt) {
    qrPrompt.textContent = 'QR code detected — verifying eligibility...';
  }
  if (feedbackMsg) {
    feedbackMsg.innerHTML = '<span class="spinner-border spinner-border-sm text-primary"></span> <strong class="text-primary">QR Code Detected:</strong> Checking voter eligibility...';
  }

  // Verify voter with election backend
  setTimeout(() => {
    executeVoterVerification(rawToken);
  }, 200);
}

async function handleQrFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const feedbackMsg = document.getElementById('qrFeedbackMsg');
  if (feedbackMsg) {
    feedbackMsg.innerHTML = '<span class="spinner-border spinner-border-sm text-info"></span> Decoding uploaded QR image...';
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/voting/scan_qr', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.found && data.token) {
      handleScannedQrToken(data.token);
    } else {
      VotingAudio.playErrorSound();
      VotingAudio.announceInvalidQr();
      showKioskAlert('warning', 'No QR code could be detected in the uploaded image. Please try a clearer picture.', 'bi-qr-code');
      if (feedbackMsg) {
        feedbackMsg.innerHTML = '<i class="bi bi-exclamation-triangle-fill text-warning"></i> QR not detected in uploaded file.';
      }
    }
  } catch (e) {
    VotingAudio.playErrorSound();
    showKioskAlert('danger', 'Error processing QR file: ' + e.message, 'bi-x-circle-fill');
  }
}

// ================= UNIFIED VOTER VERIFICATION =================
async function executeVoterVerification(voterIdentifier) {
  hideKioskAlert();
  const btn = document.getElementById('btnVerifyVoter');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Verifying...';
  }

  try {
    const res = await fetch('/api/voting/verify_voter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ voter_id: voterIdentifier })
    });
    const data = await res.json();

    if (!data.eligible) {
      const reticle = document.getElementById('qrTargetReticle');
      if (reticle) {
        reticle.classList.remove('success');
        reticle.classList.add('warning');
        setTimeout(() => reticle.classList.remove('warning'), 3000);
      }
      const statusBadge = document.getElementById('qrStatusBadge');
      const feedbackMsg = document.getElementById('qrFeedbackMsg');
      const qrPrompt = document.getElementById('qrPromptText');

      if (data.has_voted) {
        // DISTINCT WARNING ALERT SOUND & ANNOUNCEMENT: Already voted
        VotingAudio.playAlreadyVotedAlert();
        VotingAudio.announceAlreadyVoted();

        if (statusBadge) {
          statusBadge.textContent = 'Vote Already Cast';
        }
        if (qrPrompt) {
          qrPrompt.textContent = 'Alert: Voter has already cast ballot';
        }
        if (feedbackMsg) {
          feedbackMsg.innerHTML = '<i class="bi bi-shield-x text-danger"></i> Double voting strictly prohibited';
        }

        showKioskAlert(
          'danger',
          `<strong>VOTE ALREADY RECORDED:</strong> Voter <strong>${data.voter ? data.voter.voter_id : ''}</strong> has already cast their ballot on <strong>${data.voted_at}</strong>. Double voting is strictly prohibited under election laws.`,
          'bi-shield-fill-x'
        );

        // Cooldown before unlocking QR scanner frame processing to avoid repetitive spam
        setTimeout(() => {
          isProcessingQr = false;
          updateQrCameraStatus('active');
          if (qrPrompt) qrPrompt.textContent = 'Hold Voter ID QR inside frame';
        }, 4000);
      } else {
        // INVALID QR CODE: Distinct error alert sound & announcement
        VotingAudio.playErrorSound();
        VotingAudio.announceInvalidQr();

        if (qrPrompt) {
          qrPrompt.textContent = 'Invalid QR code — please try again';
        }
        if (feedbackMsg) {
          feedbackMsg.innerHTML = '<i class="bi bi-exclamation-triangle-fill text-warning"></i> Invalid Voter ID / QR Code';
        }

        // Show clean, professional alert without raw base64 or payload strings
        const cleanMsg = (data.reason && data.reason.length < 100 && !data.reason.includes('==') && !data.reason.startsWith('{'))
          ? data.reason
          : 'No matching record found in the election registry. Please check your Voter ID or scan a valid card QR.';

        showKioskAlert('warning', `<strong>INVALID VOTER:</strong> ${cleanMsg}`, 'bi-exclamation-triangle-fill');

        setTimeout(() => {
          isProcessingQr = false;
          updateQrCameraStatus('active');
          if (qrPrompt) qrPrompt.textContent = 'Hold Voter ID QR inside frame';
        }, 3000);
      }
      return;
    }

    // VOTER IS ELIGIBLE & PROCEEDING TO NEXT STEP:
    // Play ONE single confirmation beep & voice announcement
    VotingAudio.playSuccessBeep(1000, 140);
    VotingAudio.announceQrSuccess();

    const reticle = document.getElementById('qrTargetReticle');
    if (reticle) reticle.classList.add('success');

    // Advance to Step 2
    stopQrScanner();
    currentVoter = data.voter;
    loadStep2(currentVoter);
  } catch (err) {
    isProcessingQr = false;
    VotingAudio.playErrorSound();
    showKioskAlert('danger', 'System network error while verifying voter. Please check server connection.', 'bi-x-circle-fill');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = 'Verify Voter <i class="bi bi-arrow-right ms-1"></i>';
    }
  }
}

function quickFillVoter(voterId) {
  const input = document.getElementById('voterInput');
  if (input) input.value = voterId;
  executeVoterVerification(voterId);
}

// Helper to safely update kiosk step indicator (if present)
function updateStepIndicator(stepNum) {
  // Stepper bar removed from UI for a streamlined kiosk experience
}

// ================= STEP 2: BIOMETRIC VERIFICATION =================
function loadStep2(voter) {
  try {
    currentVoter = voter;
    kioskCurrentStep = 2;
    saveKioskState(2, { currentVoter: voter });

    stopQrScanner(); // Stop QR scanner camera before activating Face camera
    const sec1 = document.getElementById('sectionStep1');
    const sec2 = document.getElementById('sectionStep2');
    if (sec1) sec1.classList.add('d-none');
    if (sec2) sec2.classList.remove('d-none');
    setKioskHeaderControls(2);
    updateStepIndicator(2);
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Announce face verification prompt (queued after QR confirmation)
    VotingAudio.announceLookAtCamera();

    const promptEl = document.getElementById('scanPrompt');
    if (promptEl) {
      promptEl.textContent = 'Position your face inside frame';
      promptEl.style.background = 'rgba(15, 23, 42, 0.75)';
    }
    const reticle = document.getElementById('faceTargetReticle');
    if (reticle) {
      reticle.classList.remove('success', 'warning');
    }

    populateVoterProfile(voter);
    startKioskCamera();
  } catch (e) {
    console.error("Error loading step 2:", e);
  }
}

// Camera Access & HUD Overlay Drawing
function clearHudCanvas() {
  const canvas = document.getElementById('kioskFaceCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function drawHudFaceBox(box, isMatch) {
  const canvas = document.getElementById('kioskFaceCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!box || box.length < 4) return;
  const [x, y, w, h] = box;

  // Clean professional indicator color: green for verified match, red for mismatch, blue for scanning
  const strokeColor = isMatch ? '#16a34a' : (isMatch === null ? '#2563eb' : '#dc2626');

  ctx.save();
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 2.5;

  // Clean, realistic rounded rectangle around detected face (no glowing neon, no crosshairs, no mirrored text)
  const r = Math.min(14, w / 4, h / 4);
  ctx.beginPath();
  if (ctx.roundRect) {
    ctx.roundRect(x, y, w, h, [r]);
  } else {
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }
  ctx.stroke();

  // Subtle clean corner indicators
  const cLen = Math.min(w, h) * 0.18;
  ctx.lineWidth = 3.5;
  // Top-Left
  ctx.beginPath();
  ctx.moveTo(x, y + cLen);
  ctx.lineTo(x, y);
  ctx.lineTo(x + cLen, y);
  ctx.stroke();
  // Top-Right
  ctx.beginPath();
  ctx.moveTo(x + w - cLen, y);
  ctx.lineTo(x + w, y);
  ctx.lineTo(x + w, y + cLen);
  ctx.stroke();
  // Bottom-Left
  ctx.beginPath();
  ctx.moveTo(x, y + h - cLen);
  ctx.lineTo(x, y + h);
  ctx.lineTo(x + cLen, y + h);
  ctx.stroke();
  // Bottom-Right
  ctx.beginPath();
  ctx.moveTo(x + w - cLen, y + h);
  ctx.lineTo(x + w, y + h);
  ctx.lineTo(x + w, y + h - cLen);
  ctx.stroke();

  ctx.restore();
}

async function startKioskCamera() {
  const video = document.getElementById('kioskVideo');
  const canvas = document.getElementById('kioskFaceCanvas');
  try {
    try {
      videoStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false
      });
    } catch (e1) {
      videoStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false
      });
    }
    video.srcObject = videoStream;
    video.muted = true;
    video.playsInline = true;

    video.onloadedmetadata = () => {
      if (canvas) {
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
      }
      video.play().catch(e => console.log('Kiosk video play deferred:', e));
    };
    await video.play().catch(e => console.log('Kiosk video play error:', e));
  } catch (err) {
    console.warn("Direct webcam access unavailable, falling back to simulated verification", err);
  }
}

function stopKioskCamera() {
  clearHudCanvas();
  if (videoStream) {
    videoStream.getTracks().forEach(track => track.stop());
    videoStream = null;
  }
}

// ================= STEP 3: EVM BALLOT & VOTE CASTING =================
function unlockBallot() {
  kioskCurrentStep = 3;
  saveKioskState(3, { currentVoter: currentVoter, selectedCandidate: null, isConfirmModalOpen: false });

  stopKioskCamera();
  hideKioskAlert(); // Never show top verified alert banner above EVM
  const sec2 = document.getElementById('sectionStep2');
  const sec3 = document.getElementById('sectionStep3');
  if (sec2) sec2.classList.add('d-none');
  if (sec3) sec3.classList.remove('d-none');
  setKioskHeaderControls(3);
  updateStepIndicator(3);

  // Announce candidate selection prompt (queued after face verification success)
  VotingAudio.announceSelectCandidate();
}

let modalInstance = null;
function promptCastVoteFromButton(btn) {
  const id = parseInt(btn.getAttribute('data-id'), 10);
  const name = btn.getAttribute('data-name');
  const party = btn.getAttribute('data-party');
  const symbol = btn.getAttribute('data-symbol');
  const banner = btn.getAttribute('data-banner') || '';
  const symbolImg = btn.getAttribute('data-symbol-img') || '';
  promptCastVote(id, name, party, symbol, banner, symbolImg);
}

function promptCastVote(candidateId, name, party, symbol, banner = '', symbolImg = '') {
  selectedCandidate = { id: candidateId, name: name, party: party, symbol: symbol, banner: banner, symbolImg: symbolImg };
  
  if (kioskCurrentStep === 3) {
    saveKioskState(3, { currentVoter: currentVoter, selectedCandidate: selectedCandidate, isConfirmModalOpen: true });
  }

  const snoEl = document.getElementById('modalCandSno');
  if (snoEl) snoEl.textContent = String(candidateId).padStart(2, '0');

  const nameEl = document.getElementById('modalCandName');
  if (nameEl) nameEl.textContent = name;

  const partyEl = document.getElementById('modalCandParty');
  if (partyEl) partyEl.textContent = party;

  const symImgEl = document.getElementById('modalCandSymbolImg');
  if (symImgEl) {
    if (symbolImg) {
      symImgEl.src = symbolImg;
      symImgEl.style.display = 'block';
    } else {
      symImgEl.style.display = 'none';
    }
  }

  const modalEl = document.getElementById('confirmVoteModal');
  modalInstance = new bootstrap.Modal(modalEl);
  modalInstance.show();
}

// ================= STEP 4: VVPAT CONFIRMATION =================
function showStep4Confirmation(receipt) {
  kioskCurrentStep = 4;
  currentVvpatReceipt = receipt;
  saveKioskState(4, { vvpatReceipt: receipt, currentVoter: currentVoter });

  stopKioskCamera();
  stopQrScanner();

  const sec3 = document.getElementById('sectionStep3');
  const sec4 = document.getElementById('sectionStep4');
  if (sec3) sec3.classList.add('d-none');
  if (sec4) sec4.classList.remove('d-none');
  setKioskHeaderControls(4);
  updateStepIndicator(4);

  const vId = document.getElementById('vvpatVoterId');
  if (vId) vId.textContent = receipt.voter_id;
  const cName = document.getElementById('vvpatCandidateName');
  if (cName) cName.textContent = receipt.candidate_name;
  const cParty = document.getElementById('vvpatCandidateParty');
  if (cParty) cParty.textContent = receipt.candidate_party;
  const cSym = document.getElementById('vvpatCandidateSymbol');
  if (cSym) cSym.textContent = receipt.candidate_symbol;
  const ts = document.getElementById('vvpatTimestamp');
  if (ts) ts.textContent = receipt.timestamp;
}

// Reset Kiosk for next voter (returns to leading start page)
function resetKiosk() {
  clearKioskState();
  kioskCurrentStep = 0;
  currentVoter = null;
  selectedCandidate = null;
  currentVvpatReceipt = null;

  stopKioskCamera();
  stopQrScanner();
  hideKioskAlert();

  // Stop active voice announcements and reset speech queue
  VotingAudio.stopAnnouncement();
  VotingAudio.resetWelcomeFlag();

  // Reset EVM lamps
  document.querySelectorAll('.evm-lamp').forEach(l => l.classList.remove('lit'));

  const sec4 = document.getElementById('sectionStep4');
  const sec3 = document.getElementById('sectionStep3');
  const sec2 = document.getElementById('sectionStep2');
  const sec1 = document.getElementById('sectionStep1');
  const secLeading = document.getElementById('sectionLeading');

  if (sec4) sec4.classList.add('d-none');
  if (sec3) sec3.classList.add('d-none');
  if (sec2) sec2.classList.add('d-none');
  if (sec1) sec1.classList.add('d-none');

  // Return to Leading / Start Page
  if (secLeading) secLeading.classList.remove('d-none');

  setKioskHeaderControls(0);
  switchAuthMode('qr');

  const input = document.getElementById('voterInput');
  if (input) {
    input.value = '';
  }
}

// Setup Event Listeners
function setupEventListeners() {
  // Manual Form Submit
  const btnManualVerify = document.getElementById('btnVerifyVoter');
  if (btnManualVerify) {
    btnManualVerify.addEventListener('click', function () {
      const val = document.getElementById('voterInput').value.trim();
      if (!val) {
        showKioskAlert('warning', 'Please enter a Voter ID or scan a card QR token.', 'bi-exclamation-circle-fill');
        return;
      }
      executeVoterVerification(val);
    });
  }

  const voterInputEl = document.getElementById('voterInput');
  if (voterInputEl) {
    voterInputEl.addEventListener('input', function () {
      if (kioskCurrentStep === 1) {
        saveKioskState(1, { manualVoterInput: this.value });
      }
    });
    voterInputEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        const val = this.value.trim();
        if (val) executeVoterVerification(val);
      }
    });
  }

  // Verify Face Button
  const btnFace = document.getElementById('btnVerifyFace');
  if (btnFace) {
    btnFace.addEventListener('click', async function () {
      hideKioskAlert();
      this.disabled = true;
      this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Verifying Face...';

      // Play subtle biometric processing sound
      VotingAudio.playProcessingChirp();

      const statusBadge = document.getElementById('scanStatusBadge');
      const promptEl = document.getElementById('scanPrompt');
      const faceReticle = document.getElementById('faceTargetReticle');

      if (statusBadge) {
        statusBadge.textContent = 'Verifying...';
      }
      if (promptEl) {
        promptEl.textContent = 'Verifying face match...';
      }

      // Capture frame from video if available
      let base64Image = null;
      const video = document.getElementById('kioskVideo');
      const faceCanvas = document.getElementById('kioskFaceCanvas');
      if (video && video.videoWidth > 0) {
        const offCanvas = document.createElement('canvas');
        offCanvas.width = video.videoWidth;
        offCanvas.height = video.videoHeight;
        const ctx = offCanvas.getContext('2d');
        ctx.drawImage(video, 0, 0, offCanvas.width, offCanvas.height);
        base64Image = offCanvas.toDataURL('image/jpeg', 0.88);
        if (faceCanvas) {
          faceCanvas.width = video.videoWidth;
          faceCanvas.height = video.videoHeight;
        }
      }

      try {
        const res = await fetch(`/api/voting/verify_biometric/${currentVoter.voter_id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ method: 'face', image: base64Image })
        });
        const data = await res.json();

        if (data.match) {
          if (data.face_box) {
            drawHudFaceBox(data.face_box, true);
          }
          if (faceReticle) {
            faceReticle.classList.add('success');
          }
          if (statusBadge) {
            statusBadge.textContent = 'Face Match Successful';
          }
          if (promptEl) {
            promptEl.textContent = 'Face Match Successful';
            promptEl.style.background = 'rgba(22, 101, 52, 0.9)';
          }
          hideKioskAlert();

          // SCENARIO A: Face Verification Success
          // Single confirmation beep + announcement
          VotingAudio.playSuccessBeep(1000, 140);
          VotingAudio.announceFaceSuccess();

          setTimeout(() => unlockBallot(), 1400);
        } else {
          // SCENARIO B: Face Verification Failed
          // Error sound + failure announcement
          VotingAudio.playErrorSound();
          VotingAudio.announceFaceFailed();

          if (data.face_detected && data.face_box) {
            drawHudFaceBox(data.face_box, false);
          } else {
            clearHudCanvas();
          }
          if (faceReticle) {
            faceReticle.classList.add('warning');
            setTimeout(() => faceReticle.classList.remove('warning'), 3000);
          }
          if (statusBadge) {
            statusBadge.textContent = data.face_detected ? 'Face Match Failed' : 'No Face Detected';
          }
          if (promptEl) {
            promptEl.textContent = data.face_detected ? 'Face Match Failed' : 'Position face inside frame';
            promptEl.style.background = data.face_detected ? 'rgba(185, 28, 28, 0.9)' : 'rgba(15, 23, 42, 0.75)';
          }
          showKioskAlert('danger', `<strong>Face Match Failed:</strong> ${data.message}`, 'bi-shield-x');
        }
      } catch (err) {
        VotingAudio.playErrorSound();
        showKioskAlert('danger', 'Error during biometric face match: ' + err.message, 'bi-x-circle-fill');
      } finally {
        this.disabled = false;
        this.innerHTML = '<i class="bi bi-camera-fill fs-6 me-1"></i> <span>Verify Face Match</span>';
      }
    });
  }

  // Fingerprint Button Handling (Disabled on cursor hover - hardware unavailable)
  const fpWrapper = document.getElementById('fingerprintWrapper');
  const btnFingerprint = document.getElementById('btnVerifyFingerprint');

  if (fpWrapper || btnFingerprint) {
    const handleFpDisabled = function () {
      if (btnFingerprint) {
        btnFingerprint.disabled = true;
        btnFingerprint.classList.add('disabled');
      }
      showKioskAlert(
        'warning',
        '<strong>Fingerprint Sensor Unavailable:</strong> Hardware scanner not connected. Please verify identity using Face Match.',
        'bi-exclamation-triangle-fill'
      );
    };

    if (fpWrapper) {
      fpWrapper.addEventListener('mouseenter', handleFpDisabled);
      fpWrapper.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        VotingAudio.playErrorSound();
        handleFpDisabled();
      });
    }

    if (btnFingerprint) {
      btnFingerprint.addEventListener('mouseenter', handleFpDisabled);
      btnFingerprint.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        VotingAudio.playErrorSound();
        handleFpDisabled();
      });
    }
  }

  // Presiding Officer Manual Alternative Verification Handler (ECI Rule 49V)
  const btnOfficerOverride = document.getElementById('btnOfficerOverride');
  if (btnOfficerOverride) {
    btnOfficerOverride.addEventListener('click', function () {
      if (!currentVoter || !currentVoter.voter_id) {
        showKioskAlert('warning', 'Please scan or enter Voter ID before manual verification.', 'bi-exclamation-triangle');
        return;
      }
      const pinInput = document.getElementById('officerOverridePin');
      if (pinInput) pinInput.value = '';
      const errEl = document.getElementById('officerOverrideError');
      if (errEl) errEl.classList.add('d-none');
      const modalEl = document.getElementById('officerOverrideModal');
      if (modalEl && typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
      }
    });
  }

  const btnConfirmOverride = document.getElementById('btnConfirmOfficerOverride');
  if (btnConfirmOverride) {
    btnConfirmOverride.addEventListener('click', async function () {
      const pinInput = document.getElementById('officerOverridePin');
      const pin = pinInput ? pinInput.value.trim() : '';
      const reasonEl = document.getElementById('officerOverrideReason');
      const reason = reasonEl ? reasonEl.value : 'ECI Rule 49V: Presiding Officer Physical Verification';
      const errEl = document.getElementById('officerOverrideError');

      if (!pin) {
        if (errEl) {
          errEl.textContent = 'Please enter Polling Officer PIN.';
          errEl.classList.remove('d-none');
        }
        return;
      }

      this.disabled = true;
      this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Verifying...';

      try {
        const res = await fetch(`/api/voting/manual_override/${currentVoter.voter_id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ officer_pin: pin, reason: reason })
        });
        const data = await res.json();
        if (data.success && data.match) {
          const modalEl = document.getElementById('officerOverrideModal');
          if (modalEl && typeof bootstrap !== 'undefined') {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
          }
          showKioskAlert('success', `<strong>Manual Verification Approved:</strong> ${data.message}`, 'bi-check-circle-fill');
          VotingAudio.playSuccessBeep(1000, 140);
          VotingAudio.announceFaceSuccess();
          setTimeout(() => unlockBallot(), 1400);
        } else {
          if (errEl) {
            errEl.textContent = data.message || 'Authorization failed. Invalid PIN.';
            errEl.classList.remove('d-none');
          }
        }
      } catch (e) {
        if (errEl) {
          errEl.textContent = 'Network or server error: ' + e.message;
          errEl.classList.remove('d-none');
        }
      } finally {
        this.disabled = false;
        this.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Approve & Unlock Ballot';
      }
    });
  }

  // Confirm and Cast Vote Button in Modal
  const btnConfirmVote = document.getElementById('btnConfirmCastVote');
  if (btnConfirmVote) {
    btnConfirmVote.addEventListener('click', async function () {
      if (!selectedCandidate || !currentVoter) return;

      this.disabled = true;
      this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Casting Vote...';

      try {
        const res = await fetch('/api/voting/cast_vote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            voter_id: currentVoter.voter_id,
            candidate_id: selectedCandidate.id
          })
        });
        const data = await res.json();

        if (modalInstance) modalInstance.hide();

        if (data.success) {
          // Illuminate red LED lamp on EVM row
          const lamp = document.getElementById(`lamp${selectedCandidate.id}`);
          if (lamp) lamp.classList.add('lit');

          // 1. Play EVM continuous tone
          VotingAudio.playEvmBeep(800);

          // 2. Play pleasant two-note success chime
          setTimeout(() => {
            VotingAudio.playVoteSuccessChime();
          }, 850);

          // 3. Announce: "Your vote has been recorded successfully. Thank you for voting."
          VotingAudio.announceVoteRecorded();

          setTimeout(() => {
            showStep4Confirmation(data.receipt);
          }, 1200);
        } else {
          VotingAudio.playErrorSound();
          showKioskAlert('danger', data.message, 'bi-exclamation-triangle-fill');
        }
      } catch (err) {
        VotingAudio.playErrorSound();
        showKioskAlert('danger', 'Failed to communicate with election server.', 'bi-x-circle-fill');
      } finally {
        this.disabled = false;
        this.innerHTML = '<i class="bi bi-hand-thumbs-up-fill me-1"></i> Confirm & Cast Vote';
      }
    });
  }

  // Handle Modal dismissal / cancel selection: sync state
  const confirmModalEl = document.getElementById('confirmVoteModal');
  if (confirmModalEl) {
    confirmModalEl.addEventListener('hidden.bs.modal', function () {
      if (kioskCurrentStep === 3) {
        selectedCandidate = null;
        saveKioskState(3, { currentVoter: currentVoter, selectedCandidate: null, isConfirmModalOpen: false });
      }
    });
  }
}
