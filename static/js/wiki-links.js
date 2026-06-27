/** Hover previews for external links inside wiki article content */
(function () {
  'use strict';

  const containers = document.querySelectorAll('.wiki-content');
  if (!containers.length) return;

  let tooltip = document.getElementById('link-preview-tooltip');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.id = 'link-preview-tooltip';
    document.body.appendChild(tooltip);
  }

  const cache = new Map();
  let hoverTimer = null;
  let activeLink = null;

  function positionTooltip(e) {
    const x = Math.min(e.clientX + 16, window.innerWidth - 360);
    const y = Math.min(e.clientY + 16, window.innerHeight - 240);
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
  }

  function renderPreview(data) {
    const title = data.title || data.site_name || 'Link';
    const desc = data.description
      ? `<p class="text-xs text-muted-foreground line-clamp-3 mt-1">${escapeHtml(data.description)}</p>`
      : '';
    const img = data.image_url
      ? `<img src="${escapeHtml(data.image_url)}" alt="" class="w-full h-28 object-cover rounded-md mb-2" loading="lazy">`
      : '';
    const site = data.site_name
      ? `<span class="text-xs text-muted-foreground">${escapeHtml(data.site_name)}</span>`
      : '';
    return `
      <div class="p-3">
        ${img}
        ${site}
        <p class="text-sm font-semibold leading-snug">${escapeHtml(title)}</p>
        ${desc}
      </div>
    `;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  async function showPreview(link, e) {
    const url = link.dataset.url || link.getAttribute('href');
    if (!url || !/^https?:\/\//i.test(url)) return;

    let data = cache.get(url);
    if (!data) {
      tooltip.innerHTML = '<div class="p-3 text-xs text-muted-foreground">Loading preview…</div>';
      tooltip.classList.add('visible');
      positionTooltip(e);
      try {
        const resp = await fetch(`/api/link-preview/?url=${encodeURIComponent(url)}`);
        data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Preview failed');
        cache.set(url, data);
      } catch (_) {
        tooltip.innerHTML = `<div class="p-3 text-xs">${escapeHtml(url)}</div>`;
        positionTooltip(e);
        return;
      }
    }

    if (activeLink !== link) return;
    tooltip.innerHTML = renderPreview(data);
    tooltip.classList.add('visible');
    positionTooltip(e);
  }

  containers.forEach((root) => {
    root.querySelectorAll('a.wiki-ext-link[data-url], a.wiki-url-highlight[href^="http"]').forEach((link) => {
      if (!link.dataset.url) {
        link.dataset.url = link.getAttribute('href') || '';
      }
      link.addEventListener('mouseenter', (e) => {
        activeLink = link;
        hoverTimer = setTimeout(() => showPreview(link, e), 350);
      });
      link.addEventListener('mousemove', (e) => {
        if (tooltip.classList.contains('visible')) positionTooltip(e);
      });
      link.addEventListener('mouseleave', () => {
        activeLink = null;
        clearTimeout(hoverTimer);
        tooltip.classList.remove('visible');
      });
    });
  });
})();
