/* WikiWonder — PWA, previews, scrollers, link cards */
(function () {
  'use strict';

  // Service worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/js/sw.js', { scope: '/' })
        .then(() => {
          const status = document.getElementById('offline-status');
          if (status) status.classList.remove('hidden');
        })
        .catch((err) => console.warn('SW registration failed:', err));
    });
  }

  // Horizontal scrollers
  document.querySelectorAll('[data-scroller]').forEach((scroller) => {
    const track = scroller.querySelector('[data-scroll-track]');
    const leftBtn = scroller.querySelector('[data-scroll-left]');
    const rightBtn = scroller.querySelector('[data-scroll-right]');
    if (!track) return;

    const scrollAmount = () => Math.min(track.clientWidth * 0.8, 400);

    leftBtn?.addEventListener('click', () => {
      track.scrollBy({ left: -scrollAmount(), behavior: 'smooth' });
    });
    rightBtn?.addEventListener('click', () => {
      track.scrollBy({ left: scrollAmount(), behavior: 'smooth' });
    });

    // Drag to scroll
    let isDown = false;
    let startX = 0;
    let scrollLeft = 0;

    track.addEventListener('mousedown', (e) => {
      isDown = true;
      startX = e.pageX - track.offsetLeft;
      scrollLeft = track.scrollLeft;
      track.style.cursor = 'grabbing';
    });
    track.addEventListener('mouseleave', () => { isDown = false; track.style.cursor = ''; });
    track.addEventListener('mouseup', () => { isDown = false; track.style.cursor = ''; });
    track.addEventListener('mousemove', (e) => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - track.offsetLeft;
      track.scrollLeft = scrollLeft - (x - startX) * 1.5;
    });
  });

  // Wiki page preview tooltip
  let tooltip = document.getElementById('preview-tooltip');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.id = 'preview-tooltip';
    document.body.appendChild(tooltip);
  }

  let linkTooltip = document.getElementById('link-preview-tooltip');
  if (!linkTooltip) {
    linkTooltip = document.createElement('div');
    linkTooltip.id = 'link-preview-tooltip';
    document.body.appendChild(linkTooltip);
  }

  let hoverTimer = null;

  function positionTooltip(el, e) {
    const x = Math.min(e.clientX + 16, window.innerWidth - 360);
    const y = Math.min(e.clientY + 16, window.innerHeight - 220);
    el.style.left = x + 'px';
    el.style.top = y + 'px';
  }

  document.querySelectorAll('[data-preview-url]').forEach((card) => {
    card.addEventListener('mouseenter', (e) => {
      const url = card.dataset.previewUrl;
      if (!url) return;
      hoverTimer = setTimeout(async () => {
        try {
          const resp = await fetch(url);
          const html = await resp.text();
          const doc = new DOMParser().parseFromString(html, 'text/html');
          tooltip.innerHTML = doc.body.innerHTML;
          tooltip.classList.add('visible');
          positionTooltip(tooltip, e);
        } catch (_) { /* ignore */ }
      }, 350);
    });
    card.addEventListener('mousemove', (e) => positionTooltip(tooltip, e));
    card.addEventListener('mouseleave', () => {
      clearTimeout(hoverTimer);
      tooltip.classList.remove('visible');
    });
  });

  // Shared link preview tooltip
  document.querySelectorAll('[data-link-preview-url]').forEach((card) => {
    card.addEventListener('mouseenter', (e) => {
      const url = card.dataset.linkPreviewUrl;
      if (!url) return;
      hoverTimer = setTimeout(async () => {
        try {
          const resp = await fetch(url);
          const html = await resp.text();
          linkTooltip.innerHTML = html;
          linkTooltip.classList.add('visible');
          positionTooltip(linkTooltip, e);
        } catch (_) { /* ignore */ }
      }, 300);
    });
    card.addEventListener('mousemove', (e) => positionTooltip(linkTooltip, e));
    card.addEventListener('mouseleave', () => {
      clearTimeout(hoverTimer);
      linkTooltip.classList.remove('visible');
    });
  });

  // Online/offline
  window.addEventListener('offline', () => document.body.classList.add('is-offline'));
  window.addEventListener('online', () => document.body.classList.remove('is-offline'));

  // Instant search typeahead (header)
  document.addEventListener('alpine:init', () => {
    window.Alpine.data('instantSearch', (searchPageUrl = '/search/') => ({
      query: '',
      results: [],
      open: false,
      searchPageUrl,
      async fetchResults() {
        const q = this.query.trim();
        if (q.length < 2) {
          this.results = [];
          this.open = false;
          return;
        }
        try {
          const resp = await fetch(`/api/search/?q=${encodeURIComponent(q)}&limit=6`);
          const data = await resp.json();
          this.results = data.results || [];
          this.open = this.results.length > 0;
        } catch (_) {
          this.results = [];
          this.open = false;
        }
      },
    }));
  });
})();
