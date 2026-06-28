/** Media blocks: Mermaid graphs + Chart.js + annotation pins */
(function () {
  'use strict';

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }
      const s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  async function renderGraphs() {
    const nodes = document.querySelectorAll('.wiki-graph-render[data-graph-dsl]');
    if (!nodes.length) return;

    await loadScript('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js');
    if (window.mermaid) {
      window.mermaid.initialize({ startOnLoad: false, theme: document.documentElement.classList.contains('dark') ? 'dark' : 'default' });
    }

    nodes.forEach(async (el, idx) => {
      if (el.dataset.rendered) return;
      const dsl = el.getAttribute('data-graph-dsl');
      if (!dsl) return;
      el.dataset.rendered = '1';
      const id = `wiki-graph-${idx}-${Date.now()}`;
      try {
        const { svg } = await window.mermaid.render(id, dsl);
        el.innerHTML = svg;
      } catch (_) {
        el.innerHTML = `<pre class="text-xs overflow-x-auto p-2 bg-muted rounded">${dsl.replace(/</g, '&lt;')}</pre>`;
      }
    });
  }

  function initAnnotations() {
    const root = document.querySelector('[data-can-annotate]');
    if (!root) return;

    root.querySelectorAll('.wiki-media--image, .wiki-media--gif').forEach((figure) => {
      const blockId = figure.closest('[data-block-id]')?.dataset.blockId;
      if (!blockId) return;
      figure.style.position = 'relative';
      figure.addEventListener('click', (e) => {
        if (!e.altKey) return;
        const rect = figure.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        const body = window.prompt('Annotation note (Alt+click to pin):');
        if (!body) return;
        const label = window.prompt('Short label (optional):') || '';
        const csrf = document.cookie.match(/csrftoken=([^;]+)/);
        fetch(`/wiki/api/blocks/${blockId}/annotate/`, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf ? decodeURIComponent(csrf[1]) : '',
          },
          body: JSON.stringify({ body, label, x_percent: x, y_percent: y }),
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.error) throw new Error(data.error);
            const pin = document.createElement('span');
            pin.className = 'wiki-annotation-pin';
            pin.style.left = `${x}%`;
            pin.style.top = `${y}%`;
            pin.title = data.body;
            pin.textContent = data.label || '●';
            figure.appendChild(pin);
          })
          .catch((err) => alert(err.message || 'Could not save annotation'));
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    renderGraphs();
    initAnnotations();
  });
})();
