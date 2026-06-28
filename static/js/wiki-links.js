/** Hover previews for wiki and external links inside article content */
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

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderWikiPreview(html) {
    tooltip.innerHTML = html;
  }

  function renderExternalPreview(data) {
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
    tooltip.innerHTML = `
      <div class="p-3">
        ${img}
        ${site}
        <p class="text-sm font-semibold leading-snug">${escapeHtml(title)}</p>
        ${desc}
      </div>
    `;
  }

  function renderLocalWikiPreview(data) {
    tooltip.innerHTML = `
      <div class="p-3">
        <p class="text-xs font-semibold text-primary">Open on WikiWonder</p>
        <p class="text-sm font-semibold leading-snug mt-1">${escapeHtml(data.title || data.slug)}</p>
        <p class="text-xs text-muted-foreground mt-1">${escapeHtml(data.url || '')}</p>
      </div>
    `;
  }

  const WIKI_URL_RE = /^https?:\/\/([a-z]{2,3})\.wikipedia\.org\/wiki\//i;

  function wikiPreviewUrl(href) {
    if (!href.startsWith('/wiki/')) return null;
    const parts = href.replace(/\/$/, '').split('/');
    const slug = parts[parts.length - 1];
    if (!slug || slug === 'wiki') return null;
    return `/wiki/${encodeURIComponent(slug)}/preview/`;
  }

  async function showPreview(link, e) {
    const href = link.getAttribute('href') || '';
    const url = link.dataset.url || href;
    if (!url) return;

    const wikiPreview = wikiPreviewUrl(href);
    tooltip.innerHTML = '<div class="p-3 text-xs text-muted-foreground">Loading preview…</div>';
    tooltip.classList.add('visible');
    positionTooltip(e);

    try {
      if (link.classList.contains('wiki-cite-ref') && href.startsWith('#')) {
        const target = document.querySelector(href);
        const previewText = target
          ? target.textContent.trim().slice(0, 320)
          : `Citation ${link.dataset.cite || ''}`;
        tooltip.innerHTML = `<div class="p-3"><p class="text-xs font-semibold">Reference ${escapeHtml(link.dataset.cite || '')}</p><p class="text-xs text-muted-foreground mt-1 line-clamp-5">${escapeHtml(previewText)}</p></div>`;
        positionTooltip(e);
        return;
      }
      if (wikiPreview) {
        let html = cache.get(wikiPreview);
        if (!html) {
          const resp = await fetch(wikiPreview);
          if (!resp.ok) throw new Error('Preview failed');
          html = await resp.text();
          cache.set(wikiPreview, html);
        }
        if (activeLink !== link) return;
        renderWikiPreview(html);
      } else if (/^https?:\/\//i.test(url)) {
        if (WIKI_URL_RE.test(url)) {
          const localKey = `local:${url}`;
          let local = cache.get(localKey);
          if (local === undefined) {
            const resp = await fetch(`/wiki/api/local-page/?url=${encodeURIComponent(url)}`);
            local = await resp.json();
            cache.set(localKey, local);
          }
          if (activeLink !== link) return;
          if (local && local.local) {
            renderLocalWikiPreview(local);
            tooltip.classList.add('visible');
            positionTooltip(e);
            return;
          }
        }
        let data = cache.get(url);
        if (!data) {
          const resp = await fetch(`/api/link-preview/?url=${encodeURIComponent(url)}`);
          data = await resp.json();
          if (!resp.ok) throw new Error(data.error || 'Preview failed');
          cache.set(url, data);
        }
        if (activeLink !== link) return;
        renderExternalPreview(data);
      } else {
        return;
      }
      tooltip.classList.add('visible');
      positionTooltip(e);
    } catch (_) {
      if (activeLink === link) {
        tooltip.innerHTML = `<div class="p-3 text-xs">${escapeHtml(url)}</div>`;
        positionTooltip(e);
      }
    }
  }

  containers.forEach((root) => {
    root.querySelectorAll('a.wiki-int-link, a.wiki-ext-link, a.wiki-url-highlight, a.wiki-cite-ref').forEach((link) => {
      const href = link.getAttribute('href') || '';
      if (!link.dataset.url && /^https?:\/\//i.test(href)) {
        link.dataset.url = href;
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
