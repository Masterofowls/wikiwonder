/** AJAX bookmark toggle without page reload */
(function () {
  'use strict';

  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function setBookmarkUi(form, bookmarked) {
    form.querySelectorAll('[data-bookmark-btn]').forEach((btn) => {
      btn.classList.toggle('bookmark-btn--active', bookmarked);
      const label = btn.querySelector('[data-bookmark-label]');
      const mobileLabel = btn.querySelector('[data-bookmark-mobile-label]');
      if (label) {
        label.textContent = bookmarked ? 'Bookmarked' : 'Bookmark';
      }
      if (mobileLabel) {
        mobileLabel.textContent = bookmarked ? 'Saved' : 'Save';
      }
      btn.setAttribute('aria-pressed', bookmarked ? 'true' : 'false');
    });
  }

  document.querySelectorAll('[data-bookmark-form]').forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const btn = form.querySelector('[data-bookmark-btn]');
      if (btn) btn.disabled = true;
      try {
        const body = new FormData(form);
        const response = await fetch(form.action, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
          },
          body,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Bookmark failed');
        setBookmarkUi(form, Boolean(data.bookmarked));
      } catch (_) {
        /* keep current state */
      } finally {
        if (btn) btn.disabled = false;
      }
    });
  });
})();
