/** Sticky mobile table of contents for long wiki pages */
(function () {
  'use strict';

  const toc = document.querySelector('.notion-toc');
  if (!toc || window.matchMedia('(min-width: 1024px)').matches) return;

  const shell = document.createElement('div');
  shell.className = 'notion-toc-mobile';
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'notion-toc-mobile-toggle';
  toggle.setAttribute('aria-expanded', 'false');
  toggle.innerHTML = 'On this page ▾';
  const panel = document.createElement('div');
  panel.className = 'notion-toc-mobile-panel hidden';
  panel.innerHTML = toc.innerHTML;
  shell.appendChild(toggle);
  shell.appendChild(panel);

  const layout = document.querySelector('.notion-page-layout');
  if (layout) layout.prepend(shell);

  toggle.addEventListener('click', () => {
    panel.classList.toggle('hidden');
    const open = !panel.classList.contains('hidden');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.innerHTML = open ? 'On this page ▴' : 'On this page ▾';
  });

  panel.querySelectorAll('a').forEach((a) => {
    a.addEventListener('click', () => {
      panel.classList.add('hidden');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.innerHTML = 'On this page ▾';
    });
  });
})();
