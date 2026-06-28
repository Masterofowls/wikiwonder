/** Mobile UX: nav drawer, safe areas, touch scrollers, viewport height */
(function () {
  'use strict';

  const root = document.documentElement;
  const OPEN_CLASS = 'mobile-nav-open';
  const DRAWER_OPEN_CLASS = 'is-open';

  function setViewportHeight() {
    root.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
  }

  function markTouchDevice() {
    if (window.matchMedia('(hover: none) and (pointer: coarse)').matches) {
      root.classList.add('is-touch');
    }
  }

  function initScrollers() {
    document.querySelectorAll('[data-scroller]').forEach((scroller) => {
      scroller.classList.add('scroll-scroller--touch');
    });
  }

  function initMobileNav() {
    const drawer = document.getElementById('mobile-nav-drawer');
    const openBtn = document.getElementById('mobile-nav-open');
    const panel = document.getElementById('mobile-nav-panel');
    if (!drawer || !openBtn || !panel) return;

    let startX = 0;
    let startY = 0;

    function openNav() {
      drawer.hidden = false;
      drawer.setAttribute('aria-hidden', 'false');
      drawer.classList.add(DRAWER_OPEN_CLASS);
      document.body.classList.add(OPEN_CLASS);
      openBtn.setAttribute('aria-expanded', 'true');
      panel.focus({ preventScroll: true });
    }

    function closeNav() {
      drawer.classList.remove(DRAWER_OPEN_CLASS);
      drawer.setAttribute('aria-hidden', 'true');
      document.body.classList.remove(OPEN_CLASS);
      openBtn.setAttribute('aria-expanded', 'false');
      openBtn.focus({ preventScroll: true });
      window.setTimeout(() => {
        if (!drawer.classList.contains(DRAWER_OPEN_CLASS)) {
          drawer.hidden = true;
        }
      }, 220);
    }

    openBtn.addEventListener('click', () => {
      if (drawer.classList.contains(DRAWER_OPEN_CLASS)) {
        closeNav();
      } else {
        openNav();
      }
    });

    drawer.querySelectorAll('[data-mobile-nav-close]').forEach((el) => {
      el.addEventListener('click', closeNav);
    });

    drawer.querySelectorAll('.mobile-nav a.mobile-nav-link').forEach((link) => {
      link.addEventListener('click', closeNav);
    });

    drawer.querySelectorAll('.mobile-nav button[type="submit"]').forEach((btn) => {
      btn.addEventListener('click', () => {
        window.setTimeout(closeNav, 0);
      });
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && drawer.classList.contains(DRAWER_OPEN_CLASS)) {
        closeNav();
      }
    });

    panel.addEventListener(
      'touchstart',
      (e) => {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
      },
      { passive: true }
    );

    panel.addEventListener(
      'touchend',
      (e) => {
        const dx = e.changedTouches[0].clientX - startX;
        const dy = Math.abs(e.changedTouches[0].clientY - startY);
        if (dx > 72 && dy < 48) closeNav();
      },
      { passive: true }
    );
  }

  function initMobilePageBar() {
    if (document.querySelector('.mobile-page-bar')) {
      document.body.classList.add('has-mobile-page-bar');
    }
  }

  setViewportHeight();
  markTouchDevice();
  initScrollers();
  initMobileNav();
  initMobilePageBar();

  window.addEventListener('resize', setViewportHeight);
  window.addEventListener('orientationchange', () => {
    window.setTimeout(setViewportHeight, 100);
  });
})();
