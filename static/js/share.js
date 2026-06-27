/** Share, copy-link, reading view, cookie consent, bookmark offline sync */
(function () {
  const COOKIE_NAME = 'wikiwonder_cookie_consent';
  const READING_KEY = 'wikiwonder_reading_mode';

  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  async function fetchSharePayload(url) {
    const res = await fetch(url, { credentials: 'same-origin' });
    if (!res.ok) throw new Error('Share unavailable');
    return res.json();
  }

  async function sharePage(apiUrl) {
    const data = await fetchSharePayload(apiUrl);
    const payload = { title: data.title, text: data.text, url: data.url };
    if (navigator.share) {
      await navigator.share(payload);
      return 'shared';
    }
    await navigator.clipboard.writeText(data.url);
    return 'copied';
  }

  async function copyLink(apiUrl) {
    const data = await fetchSharePayload(apiUrl);
    await navigator.clipboard.writeText(data.url);
    return data.url;
  }

  function toast(msg) {
    let el = document.getElementById('wiki-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'wiki-toast';
      el.className =
        'fixed bottom-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-lg bg-foreground text-background text-sm shadow-lg';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.hidden = false;
    setTimeout(() => {
      el.hidden = true;
    }, 2200);
  }

  function setReadingMode(on) {
    document.body.classList.toggle('reading-mode', on);
    localStorage.setItem(READING_KEY, on ? '1' : '0');
    document.querySelectorAll('[data-reading-label]').forEach((n) => {
      n.textContent = on ? 'Exit reading view' : 'Reading view';
    });
  }

  function initReadingMode() {
    const on = localStorage.getItem(READING_KEY) === '1';
    setReadingMode(on);
    document.querySelectorAll('[data-reading-toggle]').forEach((btn) => {
      btn.addEventListener('click', () => {
        setReadingMode(!document.body.classList.contains('reading-mode'));
      });
    });
  }

  function initShare() {
    document.querySelectorAll('[data-page-actions]').forEach((root) => {
      const apiUrl = root.dataset.shareUrl;
      if (!apiUrl) return;
      root.querySelector('[data-share-native]')?.addEventListener('click', async () => {
        try {
          const mode = await sharePage(apiUrl);
          toast(mode === 'shared' ? 'Shared!' : 'Link copied to clipboard');
        } catch {
          toast('Could not share');
        }
      });
      root.querySelector('[data-copy-link]')?.addEventListener('click', async () => {
        try {
          await copyLink(apiUrl);
          toast('Link copied');
        } catch {
          toast('Could not copy link');
        }
      });
    });
  }

  function setCookieConsent(value) {
    document.cookie = `${COOKIE_NAME}=${value};path=/;max-age=${365 * 24 * 3600};SameSite=Lax`;
    document.getElementById('cookie-consent')?.remove();
  }

  function initCookieConsent() {
    document.querySelector('[data-cookie-accept]')?.addEventListener('click', () => {
      setCookieConsent('accepted');
      syncBookmarkCache();
    });
    document.querySelector('[data-cookie-decline]')?.addEventListener('click', () => {
      setCookieConsent('essential');
    });
  }

  async function syncBookmarkCache() {
    if (!('serviceWorker' in navigator)) return;
    try {
      const res = await fetch('/api/bookmarks/offline/', { credentials: 'same-origin' });
      if (!res.ok) return;
      const { urls } = await res.json();
      const reg = await navigator.serviceWorker.ready;
      reg.active?.postMessage({ type: 'SYNC_BOOKMARKS', urls });
    } catch {
      /* offline or anonymous */
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    initReadingMode();
    initShare();
    initCookieConsent();
    syncBookmarkCache();
  });

  window.WikiWonderShare = { sharePage, copyLink, syncBookmarkCache };
})();
