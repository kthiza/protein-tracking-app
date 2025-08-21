// KthizaTrack Pro - Enhanced Mobile App Framework
(function () {
  'use strict';
  
  const detectedOrigin = window.location.origin || '';
  const defaultBase = 'http://127.0.0.1:8000';
  const storageKey = 'apiBase';

  // Enhanced configuration
  const CONFIG = {
    API_BASE: defaultBase,
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
    IMAGE_QUALITY: 0.8,
    MAX_IMAGE_WIDTH: 1280
  };

  function readBaseURL() {
    const manual = localStorage.getItem(storageKey);
    if (manual && /^https?:\/\//i.test(manual)) return stripTrailingSlash(manual);
    if (detectedOrigin && detectedOrigin.startsWith('http')) return stripTrailingSlash(detectedOrigin);
    return defaultBase;
  }

  function stripTrailingSlash(url) {
    return url.replace(/\/$/, '');
  }

  function setBaseURL(url) {
    if (!/^https?:\/\//i.test(url)) throw new Error('Invalid URL');
    localStorage.setItem(storageKey, stripTrailingSlash(url));
    window.location.reload();
  }

  function getCurrentUser() {
    try {
      const raw = localStorage.getItem('currentUser');
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  }

  async function fetchJSON(path, options = {}, opts = {}) {
    const { requireAuth = false, timeoutMs = 10000 } = opts;
    const url = path.startsWith('http') ? path : `${AppAPI.baseURL}${path}`;

    const headers = new Headers(options.headers || {});
    if (requireAuth) {
      const user = getCurrentUser();
      if (!user || !user.token) {
        showToast('Please log in again.', 'error');
        window.location.href = 'login.html';
        throw new Error('Unauthenticated');
      }
      headers.set('Authorization', `Bearer ${user.token}`);
    }

    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...options, headers, signal: controller.signal });
      const contentType = res.headers.get('content-type') || '';
      const body = contentType.includes('application/json') ? await res.json() : await res.text();
      if (!res.ok) {
        const message = (body && (body.detail || body.message)) || `HTTP ${res.status}`;
        throw new Error(message);
      }
      return body;
    } finally {
      clearTimeout(id);
    }
  }

  function ensureToastContainer() {
    let el = document.getElementById('toast-container');
    if (!el) {
      el = document.createElement('div');
      el.id = 'toast-container';
      el.style.position = 'fixed';
      el.style.right = '20px';
      el.style.bottom = '20px';
      el.style.zIndex = '9999';
      document.body.appendChild(el);
      const style = document.createElement('style');
      style.innerHTML = `
        .toast{min-width:260px;max-width:360px;margin-top:10px;padding:12px 14px;border-radius:10px;color:#fff;font-weight:600;box-shadow:0 10px 25px rgba(0,0,0,.25);backdrop-filter:blur(8px);opacity:0;transform:translateY(10px);transition:all .25s ease}
        .toast.show{opacity:1;transform:translateY(0)}
        .toast.success{background:linear-gradient(135deg,#2ed573,#20bf6b)}
        .toast.error{background:linear-gradient(135deg,#ff4757,#ff6b6b)}
        .toast.warning{background:linear-gradient(135deg,#ffa502,#ff7f50)}
      `;
      document.head.appendChild(style);
    }
    return el;
  }

  function showToast(message, type = 'success') {
    const container = ensureToastContainer();
    const div = document.createElement('div');
    div.className = `toast ${type}`;
    div.innerHTML = message;
    container.appendChild(div);
    requestAnimationFrame(() => div.classList.add('show'));
    setTimeout(() => {
      div.classList.remove('show');
      setTimeout(() => div.remove(), 300);
    }, 4000);
  }

  window.AppAPI = {
    baseURL: readBaseURL(),
    setBaseURL,
    fetchJSON,
    getCurrentUser,
    showToast
  };
  // Expose for existing pages using API_BASE
  window.API_BASE = window.AppAPI.baseURL;

  // Network status toasts
  window.addEventListener('offline', () => showToast('You are offline', 'warning'));
  window.addEventListener('online', () => showToast('Back online', 'success'));
})();


