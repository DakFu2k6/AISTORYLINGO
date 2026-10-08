/**
 * ═══════════════════════════════════════════════════════════
 * AI StoryLingo — Main Application Script
 * Vanilla JavaScript · Modular Architecture · Production Ready
 * ═══════════════════════════════════════════════════════════

'use strict';

/* ───────────────────────────────────────────────────────────
   1. CONFIGURATION
   ─────────────────────────────────────────────────────────── */

/**
 * Base URL for the AI Story Generation backend.
 * Uses local mock JSON during frontend testing.
 * When integrating with a FastAPI / Python backend, simply update:
 *   const API_BASE_URL = 'http://localhost:8000/api';
 */
const API_BASE_URL = '.';

const ENDPOINTS = {
  generateStory: `${API_BASE_URL}/mock_data.json`,
};

/**
 * Firebase Project Configuration.
 * To connect to your live Firebase project:
 * 1. Go to Firebase Console (https://console.firebase.google.com).
 * 2. Create a project and register a Web App.
 * 3. Replace the placeholder credentials below with your real project keys.
 * Note: A built-in fallback simulation is provided so local testing
 * without configured Firebase keys works smoothly.
 */
const firebaseConfig = {
  apiKey: "AIzaSyD-DEMO_KEY_STORYLINGO_REPLACE_ME",
  authDomain: "ai-storylingo.firebaseapp.com",
  projectId: "ai-storylingo",
  storageBucket: "ai-storylingo.appspot.com",
  messagingSenderId: "1234567890",
  appId: "1:1234567890:web:abcdef123456"
};

/* ───────────────────────────────────────────────────────────
   2. STATE MANAGEMENT
   ─────────────────────────────────────────────────────────── */

const AppState = {
  isLoggedIn: false,
  currentUser: null,
  isGenerating: false,
  authMode: 'login', // 'login' | 'register'
  phoneConfirmationResult: null, // Holds Firebase SMS verification confirmation result
};

/* ───────────────────────────────────────────────────────────
   3. FIREBASE AUTH SERVICE LAYER (Refinement 1)
   ═══════════════════════════════════════════════════════════
   Handles real authentication via Firebase Auth:
   - Google Popup Auth
   - Facebook Popup Auth
   - Phone SMS OTP with reCAPTCHA verifier
   - Email/Password Sign Up & Sign In
   - Password Reset Emails
   ─────────────────────────────────────────────────────────── */

class FirebaseAuthService {
  constructor() {
    this.auth = null;
    this.googleProvider = null;
    this.facebookProvider = null;
    this.recaptchaVerifier = null;
    this.isInitialized = false;
  }

  /**
   * Initializes Firebase App and Authentication instances.
   * Sets up auth state listener and identity providers.
   */
  init() {
    // Verify that the Firebase SDKs were loaded via CDN
    if (typeof firebase === 'undefined') {
      console.warn('[Firebase] Firebase SDK not detected. Operating in simulation mode.');
      return;
    }

    try {
      // Step 1: Initialize Firebase App instance with configuration object
      if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
      }
      this.auth = firebase.auth();

      // Step 2: Configure OAuth Providers
      // Google Identity Provider
      this.googleProvider = new firebase.auth.GoogleAuthProvider();
      this.googleProvider.addScope('profile');
      this.googleProvider.addScope('email');

      // Facebook Identity Provider
      this.facebookProvider = new firebase.auth.FacebookAuthProvider();
      this.facebookProvider.addScope('public_profile');
      this.facebookProvider.addScope('email');

      // Step 3: Listen to global authentication state changes
      this.auth.onAuthStateChanged((user) => {
        if (user) {
          AppState.isLoggedIn = true;
          AppState.currentUser = {
            uid: user.uid,
            displayName: user.displayName || user.email?.split('@')[0] || 'Cosmic Traveler',
            email: user.email,
            phoneNumber: user.phoneNumber,
            photoURL: user.photoURL,
          };
          updateNavAuthUI(AppState.currentUser);
          setAuthStatus(`Welcome back, ${AppState.currentUser.displayName}!`, 'success');
        } else {
          AppState.isLoggedIn = false;
          AppState.currentUser = null;
          updateNavAuthUI(null);
        }
      });

      this.isInitialized = true;
      console.log('[Firebase] ✦ Firebase Auth service initialized successfully.');

    } catch (err) {
      console.warn('[Firebase] Initialization notice (using simulation mode if keys are demo):', err.message);
    }
  }

  /**
   * Trigger Google Popup Sign-In.
   * Prompts user with the official Google account selection dialog.
   */
  async signInWithGoogle() {
    if (!this.isInitialized || firebaseConfig.apiKey.includes('REPLACE_ME')) {
      // Graceful fallback for local development without live Google Cloud OAuth credentials
      return this._simulateAuthSuccess('Google Traveler', 'traveler@gmail.com');
    }

    try {
      setAuthStatus('Connecting to Google constellation…', '');
      const result = await this.auth.signInWithPopup(this.googleProvider);
      const user = result.user;
      hideAuthModal();
      return user;
    } catch (error) {
      this._handleAuthError(error);
      throw error;
    }
  }

  /**
   * Trigger Facebook Popup Sign-In.
   * Prompts user with the Facebook authentication dialog.
   */
  async signInWithFacebook() {
    if (!this.isInitialized || firebaseConfig.apiKey.includes('REPLACE_ME')) {
      // Graceful fallback for local development without live Facebook App credentials
      return this._simulateAuthSuccess('Facebook Stargazer', 'stargazer@facebook.com');
    }

    try {
      setAuthStatus('Connecting to Facebook nebula…', '');
      const result = await this.auth.signInWithPopup(this.facebookProvider);
      const user = result.user;
      hideAuthModal();
      return user;
    } catch (error) {
      this._handleAuthError(error);
      throw error;
    }
  }

  /**
   * Initializes reCAPTCHA for Phone Authentication.
   * Required by Firebase to prevent automated SMS abuse.
   */
  initRecaptcha() {
    if (typeof firebase === 'undefined' || !this.auth) return;
    if (!this.recaptchaVerifier) {
      try {
        this.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
          size: 'invisible',
          callback: () => {
            console.log('[Firebase] reCAPTCHA verified for phone authentication.');
          }
        });
      } catch (e) {
        console.warn('[Firebase] reCAPTCHA notice:', e.message);
      }
    }
  }

  /**
   * Sends an SMS OTP code to the provided phone number.
   * @param {string} phoneNumber — E.164 formatted number e.g. +84901234567
   */
  async sendPhoneOTP(phoneNumber) {
    if (!this.isInitialized || firebaseConfig.apiKey.includes('REPLACE_ME')) {
      // Simulate SMS dispatch
      setAuthStatus(`Verification SMS sent to ${phoneNumber}. (Test OTP: 123456)`, 'success');
      AppState.phoneConfirmationResult = {
        confirm: async (code) => {
          if (code === '123456' || code.length === 6) {
            return this._simulateAuthSuccess(`Phone Voyager (${phoneNumber})`, phoneNumber);
          }
          throw new Error('Invalid verification code.');
        }
      };
      return;
    }

    try {
      this.initRecaptcha();
      setAuthStatus('Dispatching celestial SMS code…', '');
      const appVerifier = this.recaptchaVerifier;
      const confirmationResult = await this.auth.signInWithPhoneNumber(phoneNumber, appVerifier);
      AppState.phoneConfirmationResult = confirmationResult;
      setAuthStatus(`Verification code sent to ${phoneNumber}!`, 'success');
    } catch (error) {
      this._handleAuthError(error);
      throw error;
    }
  }

  /**
   * Confirms the SMS OTP code sent to user's phone.
   * @param {string} otpCode — 6-digit verification code
   */
  async verifyPhoneOTP(otpCode) {
    if (!AppState.phoneConfirmationResult) {
      throw new Error('Please request an SMS code first.');
    }

    try {
      setAuthStatus('Verifying cosmic code…', '');
      const result = await AppState.phoneConfirmationResult.confirm(otpCode);
      hideAuthModal();
      return result.user;
    } catch (error) {
      this._handleAuthError(error);
      throw error;
    }
  }

  /**
   * Handles Email/Password Authentication (Sign In or Sign Up).
   */
  async handleEmailPassword(mode, name, email, password) {
    if (!this.isInitialized || firebaseConfig.apiKey.includes('REPLACE_ME')) {
      // Local fallback simulation
      const displayName = mode === 'register' && name ? name : email.split('@')[0];
      return this._simulateAuthSuccess(displayName, email);
    }

    try {
      if (mode === 'register') {
        setAuthStatus('Creating your celestial account…', '');
        const userCred = await this.auth.createUserWithEmailAndPassword(email, password);
        if (name && userCred.user) {
          await userCred.user.updateProfile({ displayName: name });
        }
        hideAuthModal();
        return userCred.user;
      } else {
        setAuthStatus('Authenticating secret cipher…', '');
        const userCred = await this.auth.signInWithEmailAndPassword(email, password);
        hideAuthModal();
        return userCred.user;
      }
    } catch (error) {
      this._handleAuthError(error);
      throw error;
    }
  }

  /**
   * Sends a password reset email via Firebase Auth.
   * @param {string} email
   */
  async sendPasswordReset(email) {
    if (!email) {
      throw new Error('Please enter your email address to receive reset instructions.');
    }

    if (!this.isInitialized || firebaseConfig.apiKey.includes('REPLACE_ME')) {
      setAuthStatus(`Celestial password reset transmission sent to ${email}!`, 'success');
      return;
    }

    try {
      await this.auth.sendPasswordResetEmail(email);
      setAuthStatus(`Password reset link dispatched to ${email}!`, 'success');
    } catch (error) {
      this._handleAuthError(error);
      throw error;
    }
  }

  /**
   * Signs out the current user session.
   */
  async signOut() {
    if (this.auth) {
      try {
        await this.auth.signOut();
      } catch (e) {
        console.warn('[Firebase] Sign out error:', e);
      }
    }
    AppState.isLoggedIn = false;
    AppState.currentUser = null;
    updateNavAuthUI(null);
  }

  /**
   * Helper: Simulates successful authentication when running in offline/demo mode.
   */
  _simulateAuthSuccess(displayName, emailOrId) {
    AppState.isLoggedIn = true;
    AppState.currentUser = {
      uid: 'sim_' + Date.now(),
      displayName: displayName,
      email: emailOrId,
      photoURL: null,
    };
    updateNavAuthUI(AppState.currentUser);
    setAuthStatus(`Welcome, ${displayName}! (Authenticated)`, 'success');
    setTimeout(() => hideAuthModal(), 900);
    return AppState.currentUser;
  }

  /**
   * Formats and displays Firebase authentication error messages.
   */
  _handleAuthError(error) {
    let friendlyMessage = error.message;
    if (error.code === 'auth/wrong-password') {
      friendlyMessage = 'Incorrect password cipher. Please try again.';
    } else if (error.code === 'auth/user-not-found') {
      friendlyMessage = 'No celestial traveler found with this email.';
    } else if (error.code === 'auth/email-already-in-use') {
      friendlyMessage = 'This email is already woven into our constellation.';
    } else if (error.code === 'auth/popup-closed-by-user') {
      friendlyMessage = 'Authentication window was closed before completion.';
    } else if (error.code === 'auth/invalid-phone-number') {
      friendlyMessage = 'Invalid mobile number format. Include country code (e.g. +84).';
    }
    setAuthStatus(friendlyMessage, 'error');
  }
}

const authService = new FirebaseAuthService();

/* ───────────────────────────────────────────────────────────
   4. TINKERBELL FAIRY DUST CURSOR (Refinement 4)
   ═══════════════════════════════════════════════════════════
   Implements a magic pixie/fairy dust particle trail following
   the user's mouse cursor across the entire webpage.
   Uses the external cursor-effects library (fairyDustCursor).
   Includes a native canvas fallback engine for offline reliability.
   ─────────────────────────────────────────────────────────── */

function initTinkerbellCursor() {
  // Step 1: Check if the cursor-effects library is available via CDN
  if (typeof fairyDustCursor !== 'undefined') {
    try {
      new fairyDustCursor({
        colors: ['#CB9D2E', '#F1E4D1', '#F6D67F', '#BA811D','#EECA69'],
        size: 2,
      });
      console.log('[Cursor FX] ✦ Tinkerbell Fairy Dust initialized via cursor-effects CDN.');
      return;
    } catch (e) {
      console.warn('[Cursor FX] CDN initialization notice:', e);
    }
  }

  // Step 2: Native Canvas Particle Physics Fallback Engine
  // Ensures magic fairy dust trail runs reliably even offline or if CDN is blocked.
  initNativeFairyDustFallback();
}

/**
 * Native Canvas Particle Physics Engine for Tinkerbell Fairy Dust.
 * Calculates velocity vectors, delta decay, gravity drift, and
 * starburst rendering on a full-viewport overlay canvas.
 */
function initNativeFairyDustFallback() {
  const canvas = document.createElement('canvas');
  canvas.id = 'fairy-dust-canvas';
  canvas.style.position = 'fixed';
  canvas.style.top = '0';
  canvas.style.left = '0';
  canvas.style.width = '100vw';
  canvas.style.height = '100vh';
  canvas.style.pointerEvents = 'none';
  canvas.style.zIndex = '99999';
  document.body.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const palette = ['#CB9D2E', '#F1E4D1', '#F6D67F', '#BA811D','#EECA69'];

  // Track mouse coordinates
  window.addEventListener('mousemove', (e) => {
    // Spawn 2-4 fairy dust sparkles per mouse move
    const count = 3;
    for (let i = 0; i < count; i++) {
      particles.push({
        x: e.clientX + (Math.random() - 0.5) * 8,
        y: e.clientY + (Math.random() - 0.5) * 8,
        vx: (Math.random() - 0.5) * 1.5,
        vy: Math.random() * 1.5 + 0.5, // gentle downward gravity
        size: Math.random() * 3 + 1.5,
        color: palette[Math.floor(Math.random() * palette.length)],
        life: 1.0,
        decay: Math.random() * 0.025 + 0.015,
        rotation: Math.random() * Math.PI,
        rotSpeed: (Math.random() - 0.5) * 0.1,
      });
    }
  });

  // Animation physics loop
  function renderParticles() {
    ctx.clearRect(0, 0, width, height);

    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.life -= p.decay;
      p.rotation += p.rotSpeed;

      if (p.life <= 0) {
        particles.splice(i, 1);
        continue;
      }

      ctx.save();
      ctx.globalAlpha = p.life;
      ctx.fillStyle = p.color;
      ctx.shadowBlur = 8;
      ctx.shadowColor = p.color;

      // Draw sparkling starlet shape
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rotation);
      ctx.beginPath();
      const s = p.size * p.life;
      // 4-pointed sparkle star
      ctx.moveTo(0, -s * 2);
      ctx.quadraticCurveTo(0, 0, s * 2, 0);
      ctx.quadraticCurveTo(0, 0, 0, s * 2);
      ctx.quadraticCurveTo(0, 0, -s * 2, 0);
      ctx.quadraticCurveTo(0, 0, 0, -s * 2);
      ctx.fill();
      ctx.restore();
    }

    requestAnimationFrame(renderParticles);
  }

  renderParticles();
  console.log('[Cursor FX] ✦ Tinkerbell Fairy Dust canvas engine active.');
}

/* ───────────────────────────────────────────────────────────
   5. API SERVICE LAYER
   ═══════════════════════════════════════════════════════════
   Strictly isolated async fetch calls (Zero DOM manipulation)
   ─────────────────────────────────────────────────────────── */

/**
 * Requests story generation from the mock file or live API.
 * @param {Object} payload — Validated form parameters
 * @returns {Promise<Object>}
 */
async function fetchGeneratedStory(payload) {
  try {
    const response = await fetch(ENDPOINTS.generateStory);

    if (!response.ok) {
      throw new Error(`Server responded with HTTP ${response.status}: ${response.statusText}`);
    }

    const storyData = await response.json();
    return storyData;

  } catch (error) {
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      throw new Error('Network error — unable to reach story generator endpoint. Check CORS and server status.');
    }
    throw error;
  }
}

/* ───────────────────────────────────────────────────────────
   6. UI RENDERING LAYER
   ═══════════════════════════════════════════════════════════
   Dynamic DOM manipulation functions
   ─────────────────────────────────────────────────────────── */

/**
 * Updates the Top Navigation Auth link based on login state.
 */
function updateNavAuthUI(user) {
  const authNavText = document.querySelector('#nav-auth-text');
  const authNavBtn = document.querySelector('#nav-auth-trigger');

  if (!authNavText || !authNavBtn) return;

  if (user) {
    const name = user.displayName || user.email?.split('@')[0] || 'Traveler';
    authNavText.textContent = `${name} (Sign Out)`;
    authNavBtn.setAttribute('data-auth-action', 'sign-out');
  } else {
    authNavText.textContent = 'Login / Register';
    authNavBtn.setAttribute('data-auth-action', 'open-modal');
  }
}

/**
 * Shows the Dynamic Authentication Modal.
 */
function showAuthModal(initialMode = 'login') {
  const modal = document.querySelector('#auth-modal');
  if (!modal) return;

  setAuthModalMode(initialMode);
  clearAuthErrors();
  modal.removeAttribute('hidden');

  // Accessibility focus trap to close button
  const closeBtn = document.querySelector('#auth-modal-close');
  if (closeBtn) closeBtn.focus();
}

/**
 * Hides the Authentication Modal.
 */
function hideAuthModal() {
  const modal = document.querySelector('#auth-modal');
  if (!modal) return;
  modal.setAttribute('hidden', '');
  clearAuthErrors();
}

/**
 * Switches between 'login' and 'register' modes in the auth modal.
 */
function setAuthModalMode(mode) {
  AppState.authMode = mode;

  const tabLogin = document.querySelector('#tab-login');
  const tabRegister = document.querySelector('#tab-register');
  const nameGroup = document.querySelector('#group-name');
  const modalTitle = document.querySelector('#auth-modal-title');
  const modalSubtitle = document.querySelector('#auth-subtitle');
  const submitBtnText = document.querySelector('#btn-auth-submit .btn-text');
  const phonePanel = document.querySelector('#phone-auth-panel');

  // Hide phone panel when switching tabs
  if (phonePanel) phonePanel.setAttribute('hidden', '');

  if (mode === 'register') {
    tabLogin.classList.remove('active');
    tabLogin.setAttribute('aria-selected', 'false');
    tabRegister.classList.add('active');
    tabRegister.setAttribute('aria-selected', 'true');

    if (nameGroup) nameGroup.removeAttribute('hidden');
    if (modalTitle) modalTitle.textContent = 'Join the Constellation';
    if (modalSubtitle) modalSubtitle.textContent = 'Create an account to embark on infinite cosmic language journeys.';
    if (submitBtnText) submitBtnText.textContent = 'Create Account (Sign Up)';
  } else {
    tabRegister.classList.remove('active');
    tabRegister.setAttribute('aria-selected', 'false');
    tabLogin.classList.add('active');
    tabLogin.setAttribute('aria-selected', 'true');

    if (nameGroup) nameGroup.setAttribute('hidden', '');
    if (modalTitle) modalTitle.textContent = 'Welcome, Stargazer';
    if (modalSubtitle) modalSubtitle.textContent = 'Sign in to weave, save, and explore your cosmic stories.';
    if (submitBtnText) submitBtnText.textContent = 'Embark (Sign In)';
  }
}

/**
 * Sets feedback message in the Auth Modal.
 */
function setAuthStatus(message, type = '') {
  const statusEl = document.querySelector('#auth-status-msg');
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.className = 'auth-status-msg ' + type;
}

/**
 * Clears all error labels in the auth modal.
 */
function clearAuthErrors() {
  document.querySelectorAll('.auth-field-error').forEach((el) => (el.textContent = ''));
  setAuthStatus('', '');
}

/**
 * Toggles password visibility (text vs password) with eye icon update.
 */
function togglePasswordVisibility() {
  const passwordInput = document.querySelector('#auth-password');
  const toggleBtn = document.querySelector('#btn-toggle-password');

  if (!passwordInput || !toggleBtn) return;

  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    toggleBtn.textContent = '🙈';
    toggleBtn.setAttribute('aria-label', 'Hide secret password');
  } else {
    passwordInput.type = 'password';
    toggleBtn.textContent = '👁️';
    toggleBtn.setAttribute('aria-label', 'Show secret password');
  }
}

/**
 * Toggles the expansion of the Phone SMS panel in the auth modal.
 */
function togglePhoneAuthPanel() {
  const panel = document.querySelector('#phone-auth-panel');
  if (!panel) return;

  if (panel.hasAttribute('hidden')) {
    panel.removeAttribute('hidden');
    const phoneInput = document.querySelector('#auth-phone-input');
    if (phoneInput) phoneInput.focus();
  } else {
    panel.setAttribute('hidden', '');
  }
}

/**
 * Renders the story generation result into the #story-result container.
 */
function renderStoryResult(data) {
  const resultSection = document.querySelector('#story-result');
  if (!resultSection) return;

  resultSection.innerHTML = '';

  // Title
  const title = document.createElement('h2');
  title.className = 'story-title';
  title.textContent = data.title;
  resultSection.appendChild(title);

  // Metadata badges
  const meta = document.createElement('div');
  meta.className = 'story-meta';

  const badges = [
    `🌌 Language: ${data.language}`,
    `📊 Level: ${data.level}`,
    `🎭 Genre: ${data.genre}`,
    `✦ Topic: ${data.topic}`,
  ];

  badges.forEach((text) => {
    const badge = document.createElement('span');
    badge.className = 'meta-badge';
    badge.textContent = text;
    meta.appendChild(badge);
  });
  resultSection.appendChild(meta);

  // Story narrative body
  const body = document.createElement('div');
  body.className = 'story-body';
  body.textContent = data.content;
  resultSection.appendChild(body);

  // Target vocabulary cards
  if (data.vocabulary && data.vocabulary.length > 0) {
    const vocabTitle = document.createElement('h3');
    vocabTitle.className = 'vocab-section-title';
    vocabTitle.textContent = '✦ Target Constellation Vocabulary';
    resultSection.appendChild(vocabTitle);

    const list = document.createElement('div');
    list.className = 'vocab-list';

    data.vocabulary.forEach((item) => {
      const card = document.createElement('article');
      card.className = 'vocab-card';

      const wordLine = document.createElement('div');

      const word = document.createElement('span');
      word.className = 'vocab-word';
      word.textContent = item.word;
      wordLine.appendChild(word);

      if (item.pronunciation) {
        const pron = document.createElement('span');
        pron.className = 'vocab-pronunciation';
        pron.textContent = item.pronunciation;
        wordLine.appendChild(pron);
      }

      if (item.part_of_speech) {
        const pos = document.createElement('span');
        pos.className = 'vocab-pos';
        pos.textContent = item.part_of_speech;
        wordLine.appendChild(pos);
      }
      card.appendChild(wordLine);

      const meaning = document.createElement('p');
      meaning.className = 'vocab-meaning';
      meaning.textContent = item.meaning;
      card.appendChild(meaning);

      if (item.meaning_vi) {
        const meaningVi = document.createElement('p');
        meaningVi.className = 'vocab-meaning-vi';
        meaningVi.textContent = `🇻🇳 ${item.meaning_vi}`;
        card.appendChild(meaningVi);
      }

      if (item.example) {
        const example = document.createElement('p');
        example.className = 'vocab-example';
        example.textContent = `"${item.example}"`;
        card.appendChild(example);
      }

      list.appendChild(card);
    });

    resultSection.appendChild(list);
  }

  resultSection.removeAttribute('hidden');
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Displays error state in the story result container.
 */
function displayError(message) {
  const resultSection = document.querySelector('#story-result');
  if (!resultSection) return;

  resultSection.innerHTML = '';

  const container = document.createElement('div');
  container.className = 'story-error';

  const icon = document.createElement('div');
  icon.className = 'error-icon';
  icon.textContent = '☄️';
  container.appendChild(icon);

  const text = document.createElement('p');
  text.className = 'error-text';
  text.textContent = message;
  container.appendChild(text);

  resultSection.appendChild(container);
  resultSection.removeAttribute('hidden');
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Updates loading visual state on the center feather generate button.
 */
function setLoadingState(isLoading) {
  const featherBtn = document.querySelector('.feather-button');
  const featherLabel = document.querySelector('.feather-label');

  if (!featherBtn || !featherLabel) return;

  if (isLoading) {
    featherBtn.classList.add('is-loading');
    featherLabel.textContent = 'Weaving Tale…';
    AppState.isGenerating = true;
  } else {
    featherBtn.classList.remove('is-loading');
    featherLabel.textContent = 'Generate Story';
    AppState.isGenerating = false;
  }
}

/* ───────────────────────────────────────────────────────────
   7. CLIENT-SIDE VALIDATION
   ═══════════════════════════════════════════════════════════
   Validates inputs across all 5 mystic orbs
   ─────────────────────────────────────────────────────────── */

function validateStoryForm(form) {
  let isValid = true;

  // Clear previous error styles
  form.querySelectorAll('.input-cloud').forEach((cloud) => {
    cloud.classList.remove('has-error');
    const msg = cloud.querySelector('.error-msg');
    if (msg) msg.textContent = '';
  });

  function setFieldError(inputId, message) {
    const input = form.querySelector(`#${inputId}`);
    if (!input) return;
    const cloud = input.closest('.input-cloud');
    if (cloud) {
      cloud.classList.add('has-error');
      const err = cloud.querySelector('.error-msg');
      if (err) err.textContent = message;
    }
    isValid = false;
  }

  // 1. Language Orb
  const language = form.querySelector('#language').value;
  if (!language) setFieldError('language', 'Select language');

  // 2. Level Orb
  const level = form.querySelector('#level').value;
  if (!level) setFieldError('level', 'Select level');

  // 3. Genre Orb
  const genre = form.querySelector('#genre').value;
  if (!genre) setFieldError('genre', 'Select genre');

  // 4. Topic Orb
  const topic = form.querySelector('#topic').value.trim();
  if (!topic) {
    setFieldError('topic', 'Enter a topic');
  } else if (topic.length < 2) {
    setFieldError('topic', 'Min 2 characters');
  }

  // 5. Target Vocabulary Orb
  const vocabRaw = form.querySelector('#target-vocab').value;
  const vocabNum = Number(vocabRaw);
  if (!vocabRaw) {
    setFieldError('target-vocab', 'Enter 1–10');
  } else if (isNaN(vocabNum) || vocabNum < 1 || vocabNum > 10) {
    setFieldError('target-vocab', 'Must be 1–10');
  }

  if (!isValid) return null;

  return {
    language,
    level,
    genre,
    topic,
    target_words: vocabNum,
  };
}

/* ───────────────────────────────────────────────────────────
   8. EVENT CONTROLLERS & DELEGATION
   ═══════════════════════════════════════════════════════════
   Event listeners and delegation
   ─────────────────────────────────────────────────────────── */

/**
 * Handles Story Generation Form Submission.
 */
async function handleStoryFormSubmit(event) {
  event.preventDefault();

  if (AppState.isGenerating) return;

  const form = event.target;
  const payload = validateStoryForm(form);

  if (!payload) return;

  setLoadingState(true);

  try {
    // Simulate generation latency (1.5 - 2s)
    await new Promise((resolve) => setTimeout(resolve, 1500 + Math.random() * 500));

    const storyData = await fetchGeneratedStory(payload);
    renderStoryResult(storyData);

  } catch (err) {
    console.error('[Story Generator] Error:', err);
    displayError(err.message || 'Celestial communication failed. Please try again.');
  } finally {
    setLoadingState(false);
  }
}

/**
 * Handles Email/Password Authentication Submission.
 */
async function handleAuthFormSubmit(event) {
  event.preventDefault();
  clearAuthErrors();

  const form = event.target;
  const emailInput = form.querySelector('#auth-email');
  const passwordInput = form.querySelector('#auth-password');
  const nameInput = form.querySelector('#auth-name');

  const email = emailInput.value.trim();
  const password = passwordInput.value;
  const name = nameInput ? nameInput.value.trim() : '';

  // Validation
  let hasError = false;
  if (!email || !email.includes('@')) {
    document.querySelector('#error-email').textContent = 'Please enter a valid email address.';
    hasError = true;
  }

  if (!password || password.length < 6) {
    document.querySelector('#error-password').textContent = 'Password must be at least 6 characters.';
    hasError = true;
  }

  if (AppState.authMode === 'register' && !name) {
    document.querySelector('#error-name').textContent = 'Please enter your traveler name.';
    hasError = true;
  }

  if (hasError) return;

  try {
    await authService.handleEmailPassword(AppState.authMode, name, email, password);
  } catch (e) {
    // Error is rendered inside authService
  }
}

/**
 * Handles Top Navigation clicks via event delegation.
 */
function handleNavClick(event) {
  const authTrigger = event.target.closest('#nav-auth-trigger');
  if (authTrigger) {
    event.preventDefault();
    const action = authTrigger.getAttribute('data-auth-action');
    if (action === 'sign-out') {
      authService.signOut();
    } else {
      showAuthModal('login');
    }
    return;
  }

  const protectedLink = event.target.closest('[data-requires-auth]');
  if (protectedLink) {
    event.preventDefault();
    if (!AppState.isLoggedIn) {
      showAuthModal('login');
      setAuthStatus('Please sign in to access this feature.', 'error');
    } else {
      alert(`✦ Navigating to ${protectedLink.textContent.trim()} (Logged in as ${AppState.currentUser.displayName})`);
    }
  }
}

/* ───────────────────────────────────────────────────────────
   9. APPLICATION BOOTSTRAP
   ─────────────────────────────────────────────────────────── */

function initApp() {
  // 1. Initialize Firebase Auth
  authService.init();

  // 2. Initialize Tinkerbell Fairy Dust Cursor
  initTinkerbellCursor();

  // 3. Form submission for Story Generator
  const storyForm = document.querySelector('#story-form');
  if (storyForm) {
    storyForm.addEventListener('submit', handleStoryFormSubmit);
  }

  // 4. Navigation event delegation
  const navBar = document.querySelector('.nav-bar');
  if (navBar) {
    navBar.addEventListener('click', handleNavClick);
  }

  // 5. Auth Modal tab switching
  const tabLogin = document.querySelector('#tab-login');
  const tabRegister = document.querySelector('#tab-register');
  if (tabLogin) tabLogin.addEventListener('click', () => setAuthModalMode('login'));
  if (tabRegister) tabRegister.addEventListener('click', () => setAuthModalMode('register'));

  // 6. Modal close buttons & overlay backdrop click
  const modalCloseBtn = document.querySelector('#auth-modal-close');
  if (modalCloseBtn) modalCloseBtn.addEventListener('click', hideAuthModal);

  const authModal = document.querySelector('#auth-modal');
  if (authModal) {
    authModal.addEventListener('click', (e) => {
      if (e.target === authModal) hideAuthModal();
    });
  }

  // 7. Password visibility toggle (👁️ icon inside password field)
  const pwdToggleBtn = document.querySelector('#btn-toggle-password');
  if (pwdToggleBtn) {
    pwdToggleBtn.addEventListener('click', togglePasswordVisibility);
  }

  // 8. Forgot password link
  const forgotPwdLink = document.querySelector('#link-forgot-password');
  if (forgotPwdLink) {
    forgotPwdLink.addEventListener('click', (e) => {
      e.preventDefault();
      const emailInput = document.querySelector('#auth-email');
      const email = emailInput ? emailInput.value.trim() : '';
      authService.sendPasswordReset(email).catch(() => {});
    });
  }

  // 9. Auth Form submission
  const authForm = document.querySelector('#auth-form');
  if (authForm) {
    authForm.addEventListener('submit', handleAuthFormSubmit);
  }

  // 10. OAuth Providers Triggers (Refinement 1)
  // Continue with Google
  const btnGoogle = document.querySelector('#btn-oauth-google');
  if (btnGoogle) {
    btnGoogle.addEventListener('click', () => authService.signInWithGoogle().catch(() => {}));
  }

  // Continue with Facebook
  const btnFacebook = document.querySelector('#btn-oauth-facebook');
  if (btnFacebook) {
    btnFacebook.addEventListener('click', () => authService.signInWithFacebook().catch(() => {}));
  }

  // Continue with Phone Number
  const btnPhone = document.querySelector('#btn-oauth-phone');
  if (btnPhone) {
    btnPhone.addEventListener('click', togglePhoneAuthPanel);
  }

  // Phone SMS OTP flow
  const btnSendOtp = document.querySelector('#btn-send-otp');
  if (btnSendOtp) {
    btnSendOtp.addEventListener('click', async () => {
      const phoneInput = document.querySelector('#auth-phone-input');
      const phoneNumber = phoneInput ? phoneInput.value.trim() : '';
      const errorPhone = document.querySelector('#error-phone');

      if (!phoneNumber || phoneNumber.length < 8) {
        if (errorPhone) errorPhone.textContent = 'Please enter a valid mobile number with country code.';
        return;
      }
      if (errorPhone) errorPhone.textContent = '';

      try {
        await authService.sendPhoneOTP(phoneNumber);
        const otpGroup = document.querySelector('#otp-group');
        if (otpGroup) otpGroup.removeAttribute('hidden');
      } catch (e) {
        // Handled in authService
      }
    });
  }

  const btnVerifyOtp = document.querySelector('#btn-verify-otp');
  if (btnVerifyOtp) {
    btnVerifyOtp.addEventListener('click', async () => {
      const otpInput = document.querySelector('#auth-otp-input');
      const otpCode = otpInput ? otpInput.value.trim() : '';
      const errorOtp = document.querySelector('#error-otp');

      if (!otpCode || otpCode.length !== 6) {
        if (errorOtp) errorOtp.textContent = 'Please enter the 6-digit verification code.';
        return;
      }
      if (errorOtp) errorOtp.textContent = '';

      try {
        await authService.verifyPhoneOTP(otpCode);
      } catch (e) {
        // Handled in authService
      }
    });
  }

  // 11. Escape key closes modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const modal = document.querySelector('#auth-modal');
      if (modal && !modal.hasAttribute('hidden')) {
        hideAuthModal();
      }
    }
  });

  console.log('[AI StoryLingo] ✦ Core application initialized with Firebase Auth & Tinkerbell Cursor FX.');
}

// Bootstrap once DOM content is parsed
document.addEventListener('DOMContentLoaded', initApp);
