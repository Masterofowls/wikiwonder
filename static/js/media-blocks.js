/** Media blocks: Mermaid graphs + annotation pins */
(function () {
  'use strict';

  function renderGraphs() {
    document.querySelectorAll('[data-graph-dsl]').forEach((el) => {
      const dsl = el.getAttribute('data-graph-dsl');
      if (!dsl || el.dataset.rendered) return;
      el.dataset.rendered = '1';
      el.innerHTML = '<pre class="text-xs overflow-x-auto">' + dsl.replace(/</g, '&lt;') + '</pre>';
      el.insertAdjacentHTML('beforeend', '<p class="text-xs text-muted-foreground mt-2">Graph preview (Mermaid DSL)</p>');
    });
  }

  document.addEventListener('DOMContentLoaded', renderGraphs);
})();
