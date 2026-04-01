window.appShell = {
  clearAuth() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_username');
    localStorage.removeItem('user_realname');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_function_permissions');
    localStorage.removeItem('user_room_scopes');
    localStorage.removeItem('user_access_all_rooms');
  },

  async logout(options = {}) {
    const redirect = options.redirect || '/login.html';
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (_) {
      // Ignore network/logout response issues and still clear local auth state.
    } finally {
      this.clearAuth();
      window.location.href = redirect;
    }
  },

  goHome() {
    window.location.href = '/home.html';
  },

  toast(message, type = 'info') {
    if (!message) return;
    const toast = document.createElement('div');
    const colors = {
      success: 'linear-gradient(135deg, #1fa37e, #2fd0a6)',
      error: 'linear-gradient(135deg, #c64f59, #f07c86)',
      warning: 'linear-gradient(135deg, #b68523, #e8b64b)',
      info: 'linear-gradient(135deg, #2f7de0, #54adff)',
    };
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.right = '24px';
    toast.style.top = '24px';
    toast.style.zIndex = '9999';
    toast.style.maxWidth = '360px';
    toast.style.padding = '12px 16px';
    toast.style.borderRadius = '12px';
    toast.style.color = '#fff';
    toast.style.fontSize = '14px';
    toast.style.lineHeight = '1.6';
    toast.style.boxShadow = '0 18px 36px rgba(0,0,0,0.26)';
    toast.style.border = '1px solid rgba(255,255,255,0.12)';
    toast.style.background = colors[type] || colors.info;
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    toast.style.transition = 'opacity 0.18s ease, transform 0.18s ease';
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });

    window.setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      window.setTimeout(() => toast.remove(), 180);
    }, 2200);
  },

  goBackOrHome() {
    const referrer = document.referrer || '';
    const sameOrigin = referrer && referrer.startsWith(window.location.origin);
    if (sameOrigin && window.history.length > 1) {
      window.history.back();
      return;
    }
    this.goHome();
  },

  handleUnauthorized(message, delay = 0) {
    this.clearAuth();
    if (message) {
      this.toast(message, 'warning');
    }
    window.setTimeout(() => {
      window.location.href = '/login.html';
    }, delay);
  },
};
