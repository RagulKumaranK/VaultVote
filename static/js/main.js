// VaultVote General JavaScript Utilities

document.addEventListener('DOMContentLoaded', function () {
  // 1. Calculate Age automatically from DOB input
  const dobInput = document.getElementById('dob');
  const ageInput = document.getElementById('age');

  if (dobInput && ageInput) {
    const updateAge = () => {
      if (!dobInput.value) {
        ageInput.value = '';
        return;
      }
      const dob = new Date(dobInput.value);
      const today = new Date();
      let age = today.getFullYear() - dob.getFullYear();
      const m = today.getMonth() - dob.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
        age--;
      }
      ageInput.value = age > 0 ? age : 0;

      // Visual warning if under 18
      const ageFeedback = document.getElementById('age-feedback');
      if (age < 18) {
        ageInput.classList.add('is-invalid');
        ageInput.classList.remove('is-valid');
        if (ageFeedback) {
          ageFeedback.innerHTML = `<span class="text-danger fw-semibold"><i class="bi bi-x-circle me-1"></i> Voter must be at least 18 years old (Current: ${age} yrs)</span>`;
          ageFeedback.style.display = 'block';
        }
      } else {
        ageInput.classList.remove('is-invalid');
        ageInput.classList.add('is-valid');
        if (ageFeedback) {
          ageFeedback.innerHTML = `<span class="text-success fw-semibold"><i class="bi bi-check-circle me-1"></i> Eligible to register (${age} years old)</span>`;
          ageFeedback.style.display = 'block';
        }
      }
    };

    dobInput.addEventListener('change', updateAge);
    dobInput.addEventListener('input', updateAge);
  }

  // 2. Real-time Aadhaar duplicate check & formatting
  const aadhaarInput = document.getElementById('aadhaar');
  const duplicateAlertBox = document.getElementById('duplicate-alert-banner');
  let checkDebounceTimer = null;

  if (aadhaarInput) {
    aadhaarInput.addEventListener('input', function (e) {
      // Remove non-digit characters
      let digits = this.value.replace(/\D/g, '').substring(0, 12);
      
      // Auto-format as XXXX XXXX XXXX for cleaner presentation if needed
      this.value = digits;

      // Trigger duplicate check when 12 digits are reached
      if (digits.length === 12) {
        clearTimeout(checkDebounceTimer);
        checkDebounceTimer = setTimeout(() => {
          checkDuplicateAadhaar(digits);
        }, 300);
      } else {
        if (duplicateAlertBox) duplicateAlertBox.style.display = 'none';
        aadhaarInput.classList.remove('is-invalid');
      }
    });
  }

  function checkDuplicateAadhaar(aadhaarNumber) {
    fetch('/api/check_duplicate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aadhaar: aadhaarNumber })
    })
      .then(res => res.json())
      .then(data => {
        if (data.duplicate) {
          aadhaarInput.classList.add('is-invalid');
          if (duplicateAlertBox) {
            duplicateAlertBox.innerHTML = `
              <div class="alert alert-danger d-flex align-items-center mb-0 shadow-sm rounded-3 border-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill fs-4 me-3 text-danger flex-shrink-0"></i>
                <div>
                  <strong>Duplicate Record Detected:</strong> This Aadhaar number is already enrolled under 
                  <span class="badge bg-dark font-monospace">${data.existing_voter.voter_id}</span> 
                  (Name: <strong>${data.existing_voter.full_name}</strong>). Duplicate registrations are strictly prevented.
                </div>
              </div>
            `;
            duplicateAlertBox.style.display = 'block';
          }
        } else {
          aadhaarInput.classList.remove('is-invalid');
          aadhaarInput.classList.add('is-valid');
          if (duplicateAlertBox) duplicateAlertBox.style.display = 'none';
        }
      })
      .catch(err => console.error("Duplicate check error:", err));
  }

  // 3. Format Mobile Number (digits only)
  const mobileInput = document.getElementById('mobile');
  if (mobileInput) {
    mobileInput.addEventListener('input', function () {
      this.value = this.value.replace(/\D/g, '').substring(0, 10);
    });
  }

  // 4. Format Pincode (6 digits) & Auto-fill Location
  const pincodeInput = document.getElementById('pincode');
  const districtInput = document.getElementById('district');
  const stateInput = document.getElementById('state');
  const locationBanner = document.getElementById('location-autofill-banner');
  const districtDatalist = document.getElementById('district-suggestions');

  // Populate district datalist from dataset if available
  if (districtDatalist && typeof INDIA_LOCATIONS !== 'undefined') {
    INDIA_LOCATIONS.forEach(loc => {
      const opt = document.createElement('option');
      opt.value = loc.district;
      opt.label = `${loc.district}, ${loc.state} (${loc.pincode})`;
      districtDatalist.appendChild(opt);
    });
  }

  // Auto-fill State & PIN Code from District
  if (districtInput) {
    let districtTimer = null;

    const processDistrictChange = () => {
      const query = districtInput.value.trim();
      if (!query || typeof findLocationByDistrict !== 'function') {
        if (locationBanner) locationBanner.style.display = 'none';
        return;
      }

      const match = findLocationByDistrict(query);
      if (match) {
        // Auto-fill State
        if (stateInput) {
          stateInput.value = match.state;
          stateInput.classList.remove('is-invalid');
          stateInput.classList.add('is-valid');
          // Brief pulse animation
          stateInput.style.transition = 'background-color 0.3s ease';
          stateInput.style.backgroundColor = '#ecfdf5';
          setTimeout(() => { stateInput.style.backgroundColor = ''; }, 700);
        }

        // Auto-fill PIN Code if empty or previously auto-filled
        if (pincodeInput && (!pincodeInput.value || pincodeInput.dataset.autofilled === 'true')) {
          pincodeInput.value = match.pincode;
          pincodeInput.dataset.autofilled = 'true';
          pincodeInput.classList.remove('is-invalid');
          pincodeInput.classList.add('is-valid');
          pincodeInput.style.transition = 'background-color 0.3s ease';
          pincodeInput.style.backgroundColor = '#ecfdf5';
          setTimeout(() => { pincodeInput.style.backgroundColor = ''; }, 700);
        }

        districtInput.classList.remove('is-invalid');
        districtInput.classList.add('is-valid');

        // Show confirmation badge
        if (locationBanner) {
          locationBanner.innerHTML = `
            <div class="alert alert-success d-flex align-items-center py-2 px-3 mb-0 rounded-3 border-success-subtle bg-success-subtle shadow-sm" role="alert">
              <i class="bi bi-geo-alt-fill text-success fs-5 me-2 flex-shrink-0"></i>
              <div class="small text-success-emphasis">
                Auto-detected: <strong>${match.district}</strong> &rarr; State: <strong>${match.state}</strong> | PIN: <strong>${match.pincode}</strong>
                <span class="text-muted d-block" style="font-size: 0.76rem;">You can adjust the PIN code if your specific locality has a different one.</span>
              </div>
            </div>
          `;
          locationBanner.style.display = 'block';
        }
      } else {
        if (locationBanner) locationBanner.style.display = 'none';
      }
    };

    districtInput.addEventListener('input', function () {
      clearTimeout(districtTimer);
      districtTimer = setTimeout(processDistrictChange, 150);
    });
    districtInput.addEventListener('change', processDistrictChange);
    districtInput.addEventListener('blur', processDistrictChange);

    // Initial check if form has pre-filled district
    if (districtInput.value) {
      setTimeout(processDistrictChange, 200);
    }
  }

  // Format Pincode and support reverse lookup
  if (pincodeInput) {
    pincodeInput.addEventListener('input', function () {
      const clean = this.value.replace(/\D/g, '').substring(0, 6);
      this.value = clean;
      
      // If user typed PIN manually, mark as user-edited
      if (clean.length === 6) {
        if (typeof findLocationByPincode === 'function') {
          const match = findLocationByPincode(clean);
          if (match) {
            if (stateInput && !stateInput.value) {
              stateInput.value = match.state;
              stateInput.classList.add('is-valid');
            }
            if (districtInput && !districtInput.value) {
              districtInput.value = match.district;
              districtInput.classList.add('is-valid');
            }
          }
        }
      }
    });

    // If user manually types into pincode, don't overwrite blindly
    pincodeInput.addEventListener('keydown', function () {
      this.dataset.autofilled = 'false';
    });
  }

  // 5. Voter Registration Form Draft Auto-Save & Recovery (Local Cache)
  const voterForm = document.getElementById('voter-form');
  const DRAFT_KEY = 'vaultvote_voter_form_draft';

  if (voterForm) {
    const fieldIds = [
      'full_name', 'father_name', 'dob', 'gender',
      'aadhaar', 'mobile', 'address', 'district', 'state', 'pincode'
    ];

    let draftDebounceTimer = null;

    // Helper: Save current form values to localStorage
    const saveDraft = () => {
      clearTimeout(draftDebounceTimer);
      draftDebounceTimer = setTimeout(() => {
        const data = {};
        let hasContent = false;

        fieldIds.forEach(id => {
          const el = document.getElementById(id);
          if (el) {
            const val = el.value.trim();
            data[id] = el.value;
            if (val) hasContent = true;
          }
        });

        if (hasContent) {
          try {
            localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
          } catch (e) {
            console.warn("Could not save voter draft to localStorage:", e);
          }
        }
      }, 150);
    };

    // Helper: Restore saved draft from localStorage
    const restoreDraft = () => {
      try {
        const raw = localStorage.getItem(DRAFT_KEY);
        if (!raw) return;
        const data = JSON.parse(raw);
        if (!data || typeof data !== 'object') return;

        let restoredCount = 0;
        fieldIds.forEach(id => {
          const el = document.getElementById(id);
          // Only restore if the field is currently empty (avoids clobbering server-flashed values)
          if (el && !el.value && data[id]) {
            el.value = data[id];
            restoredCount++;
          }
        });

        if (restoredCount > 0) {
          // Re-calculate age if DOB was restored
          const dobEl = document.getElementById('dob');
          if (dobEl && dobEl.value) {
            dobEl.dispatchEvent(new Event('change'));
          }

          // Trigger duplicate check if Aadhaar has 12 digits
          const aadhaarEl = document.getElementById('aadhaar');
          if (aadhaarEl && aadhaarEl.value && aadhaarEl.value.length === 12) {
            aadhaarEl.dispatchEvent(new Event('input'));
          }

          // Trigger district location match if district was restored
          const distEl = document.getElementById('district');
          if (distEl && distEl.value) {
            distEl.dispatchEvent(new Event('change'));
          }

          // Show friendly "Draft Restored" alert banner with Clear button
          const bannerContainer = document.getElementById('draft-restored-container');
          if (bannerContainer) {
            bannerContainer.innerHTML = `
              <div class="alert alert-primary d-flex align-items-center justify-content-between py-2 px-3 mb-0 rounded-3 border-primary-subtle bg-primary-subtle shadow-sm" role="alert">
                <div class="d-flex align-items-center small text-primary-emphasis">
                  <i class="bi bi-clock-history fs-5 me-2 text-primary flex-shrink-0"></i>
                  <span><strong>Draft Restored:</strong> Your previously entered form data has been recovered from browser cache.</span>
                </div>
                <button type="button" id="btn-clear-draft" class="btn btn-sm btn-outline-primary py-0.5 px-2.5 ms-3 fw-semibold flex-shrink-0" style="font-size: 0.78rem;">
                  <i class="bi bi-trash3 me-1"></i>Clear Form
                </button>
              </div>
            `;
            bannerContainer.style.display = 'block';

            // Clear draft handler
            const clearBtn = document.getElementById('btn-clear-draft');
            if (clearBtn) {
              clearBtn.addEventListener('click', function () {
                fieldIds.forEach(id => {
                  const el = document.getElementById(id);
                  if (el) {
                    el.value = '';
                    el.classList.remove('is-valid', 'is-invalid');
                  }
                });
                const ageEl = document.getElementById('age');
                if (ageEl) ageEl.value = '';
                const ageFeedback = document.getElementById('age-feedback');
                if (ageFeedback) ageFeedback.innerHTML = 'Computed from birth date.';
                const locBanner = document.getElementById('location-autofill-banner');
                if (locBanner) locBanner.style.display = 'none';
                const dupBanner = document.getElementById('duplicate-alert-banner');
                if (dupBanner) dupBanner.style.display = 'none';

                localStorage.removeItem(DRAFT_KEY);
                bannerContainer.style.display = 'none';
              });
            }
          }
        }
      } catch (e) {
        console.error("Error restoring voter form draft:", e);
      }
    };

    // Auto-save on every input or change
    voterForm.addEventListener('input', saveDraft);
    voterForm.addEventListener('change', saveDraft);

    // On form submit, clear the saved draft so next voter registration starts clean
    voterForm.addEventListener('submit', function () {
      localStorage.removeItem(DRAFT_KEY);
    });

    // Execute restore on load
    restoreDraft();
  }
});
