/**
 * Empire & Ink — Shared client-side utilities
 * Auth, fetch wrapper, download helper, logout, global modals
 */

// ── Auth helpers ─────────────────────────────────────────────────────────────
const Auth = {
  getToken:  () => localStorage.getItem('ei_token'),
  getUserId: () => localStorage.getItem('ei_user_id'),
  getEmail:  () => localStorage.getItem('ei_email'),

  setSession: (token, userId, email) => {
    localStorage.setItem('ei_token',   token);
    localStorage.setItem('ei_user_id', userId);
    localStorage.setItem('ei_email',   email);
  },

  clearSession: () => {
    ['ei_token', 'ei_user_id', 'ei_email'].forEach(k => localStorage.removeItem(k));
  },

  requireAuth: () => {
    if (!Auth.getToken()) {
      window.location.href = '/login';
      return false;
    }
    return true;
  },

  initNavbar: () => {
    const el = document.getElementById('nav-email');
    if (el) el.textContent = Auth.getEmail() || '';
  },
};

// ── Global modal ─────────────────────────────────────────────────────────────
/**
 * showModal(type, message, opts)
 *   type    : 'error' | 'warning' | 'info' | 'success'
 *   message : string to display
 *   opts    : { title, actions: [{label, primary, onclick}] }
 */
function showModal(type, message, opts = {}) {
  const modal   = document.getElementById('g-modal');
  const box     = document.getElementById('g-modal-box');
  const iconEl  = document.getElementById('g-modal-icon');
  const titleEl = document.getElementById('g-modal-title');
  const msgEl   = document.getElementById('g-modal-msg');
  const actEl   = document.getElementById('g-modal-actions');
  if (!modal) return;

  const config = {
    error:   { icon: '✕', title: 'Something went wrong',   border: 'rgba(139,26,42,0.6)',  iconColor: '#fca5a5' },
    warning: { icon: '⚠', title: 'Heads up',               border: 'rgba(180,120,20,0.6)', iconColor: '#fcd34d' },
    info:    { icon: 'ℹ', title: 'Notice',                  border: '#3a2e1a',              iconColor: '#93c5fd' },
    success: { icon: '✦', title: 'Done',                    border: 'rgba(20,120,80,0.6)',  iconColor: '#6ee7b7' },
  }[type] || config.error;

  iconEl.textContent  = config.icon;
  iconEl.style.color  = config.iconColor;
  titleEl.textContent = opts.title   || config.title;
  msgEl.textContent   = message;
  box.style.borderColor = config.border;

  // Rebuild action buttons
  actEl.innerHTML = '';
  const actions = opts.actions || [{ label: 'Dismiss', primary: false }];
  actions.forEach(a => {
    const btn = document.createElement('button');
    btn.textContent = a.label;
    btn.className   = 'px-4 py-2 rounded-lg font-display text-sm font-semibold transition-colors duration-200';
    if (a.primary) {
      btn.style.cssText = 'background:linear-gradient(135deg,#a07a18,#d4a82a);color:#0d0a07;';
    } else {
      btn.style.cssText = 'border:1px solid #3a2e1a;color:#c8b898;background:transparent;';
      btn.onmouseover = () => { btn.style.borderColor = '#5a4a1a'; btn.style.color = '#f0e4c8'; };
      btn.onmouseout  = () => { btn.style.borderColor = '#3a2e1a'; btn.style.color = '#c8b898'; };
    }
    btn.onclick = () => { closeModal(); if (a.onclick) a.onclick(); };
    actEl.appendChild(btn);
  });

  // Re-trigger animation
  box.classList.remove('modal-enter');
  void box.offsetWidth;
  box.classList.add('modal-enter');

  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const modal = document.getElementById('g-modal');
  if (modal) modal.classList.add('hidden');
  document.body.style.overflow = '';
}

function showSessionExpired() {
  const modal = document.getElementById('session-modal');
  if (modal) {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  } else {
    // Fallback if session modal not in DOM (shouldn't happen on base.html pages)
    window.location.href = '/login';
  }
}

// ESC key closes modal
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeModal();
});

// ── Authenticated fetch wrapper ──────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const token   = Auth.getToken();
  const headers = {
    'Authorization': `Bearer ${token}`,
    ...(opts.headers || {}),
  };

  let resp;
  try {
    resp = await fetch(path, { ...opts, headers });
  } catch (networkErr) {
    showModal('error', 'Could not reach the server. Please check your connection and try again.', {
      title: 'Network Error',
    });
    return null;
  }

  if (resp.status === 401) {
    Auth.clearSession();
    showSessionExpired();
    return null;
  }

  return resp;
}

// ── Download image as blob (no new tab) ─────────────────────────────────────
async function downloadImage(url, filename) {
  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error('fetch failed');
    const blob      = await resp.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href     = objectUrl;
    a.download = filename || 'mughal-art.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(objectUrl), 100);
  } catch (err) {
    showModal('error', 'The download could not be completed. Try right-clicking the image and saving manually.', {
      title: 'Download Failed',
    });
  }
}

// ── Logout ───────────────────────────────────────────────────────────────────
async function logout() {
  try {
    await apiFetch('/api/auth/logout', { method: 'POST' });
  } catch (e) {
    // Non-critical — clear session regardless
  }
  Auth.clearSession();
  window.location.href = '/login';
}
