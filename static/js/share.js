/** Share modal, Web Share API, clipboard fallback, reading mode, offline bookmarks */
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

  async function copyText(text) {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'absolute';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  }

  function toast(msg) {
    let el = document.getElementById('wiki-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'wiki-toast';
      el.className =
        'fixed bottom-20 left-1/2 -translate-x-1/2 z-[100] px-4 py-2 rounded-lg bg-foreground text-background text-sm shadow-lg';
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
    const exitBtn = document.getElementById('reading-mode-exit');
    if (exitBtn) exitBtn.hidden = !on;
  }

  function initReadingMode() {
    let exitBtn = document.getElementById('reading-mode-exit');
    if (!exitBtn) {
      exitBtn = document.createElement('button');
      exitBtn.id = 'reading-mode-exit';
      exitBtn.type = 'button';
      exitBtn.className = 'reading-mode-exit';
      exitBtn.setAttribute('aria-label', 'Exit reading view');
      exitBtn.innerHTML = '<span aria-hidden="true">✕</span> Exit reading view';
      exitBtn.hidden = true;
      document.body.appendChild(exitBtn);
    }

    const on = localStorage.getItem(READING_KEY) === '1';
    setReadingMode(on);

    exitBtn.addEventListener('click', () => setReadingMode(false));
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && document.body.classList.contains('reading-mode')) {
        setReadingMode(false);
      }
    });

    document.querySelectorAll('[data-reading-toggle]').forEach((btn) => {
      btn.addEventListener('click', () => {
        setReadingMode(!document.body.classList.contains('reading-mode'));
      });
    });
  }

  function initShareModal(root, apiUrl) {
    const modal = document.getElementById('wiki-share-modal');
    if (!modal) return;

    const urlInput = modal.querySelector('[data-share-url-input]');
    const titleEl = modal.querySelector('[data-share-title]');
    let shareData = null;

    async function loadShareData() {
      if (shareData) return shareData;
      shareData = await fetchSharePayload(apiUrl);
      if (urlInput) urlInput.value = shareData.url;
      if (titleEl) titleEl.textContent = shareData.title;
      return shareData;
    }

    function openModal() {
      modal.showModal();
      loadShareData().catch(() => toast('Could not load share data'));
    }

    function closeModal() {
      modal.close();
    }

    root.querySelector('[data-share-open]')?.addEventListener('click', openModal);
    modal.querySelector('[data-share-close]')?.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });

    modal.querySelector('[data-share-native]')?.addEventListener('click', async () => {
      try {
        const data = await loadShareData();
        if (navigator.share) {
          await navigator.share({ title: data.title, text: data.text, url: data.url });
          toast('Shared!');
          closeModal();
        } else {
          await copyText(data.url);
          toast('Link copied (Web Share not available)');
        }
      } catch (err) {
        if (err?.name !== 'AbortError') toast('Could not share');
      }
    });

    modal.querySelector('[data-copy-link]')?.addEventListener('click', async () => {
      try {
        const data = await loadShareData();
        await copyText(data.url);
        toast('Link copied');
      } catch {
        toast('Could not copy link');
      }
    });

    modal.querySelector('[data-copy-url-input]')?.addEventListener('click', async () => {
      try {
        const data = await loadShareData();
        await copyText(data.url);
        toast('Link copied');
      } catch {
        toast('Could not copy link');
      }
    });
  }

  function initShare() {
    document.querySelectorAll('[data-page-actions]').forEach((root) => {
      const apiUrl = root.dataset.shareUrl;
      if (!apiUrl) return;
      initShareModal(root, apiUrl);
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

    document.querySelectorAll('[data-bookmark-form]').forEach((form) => {
      form.addEventListener('submit', () => {
        setTimeout(syncBookmarkCache, 500);
      });
    });
  });

  window.WikiWonderShare = { syncBookmarkCache, copyText };
})();
