// StockPredict front-end: theme toggle + 3D background + tilt + scroll reveal
(function () {
  const root = document.documentElement;

  // ----- Theme -----
  const saved = localStorage.getItem('theme');
  if (saved) root.setAttribute('data-bs-theme', saved);

  function isDark() { return root.getAttribute('data-bs-theme') === 'dark'; }

  // ----- Vanta 3D animated background -----
  let vanta = null;
  function vantaColors() {
    return isDark()
      ? { color: 0xa855f7, backgroundColor: 0x0d0b1f }
      : { color: 0x6366f1, backgroundColor: 0xf3f4ff };
  }
  function initVanta() {
    const el = document.getElementById('vanta-hero');
    if (!el || typeof VANTA === 'undefined' || !VANTA.NET) return;
    if (vanta) vanta.destroy();
    const c = vantaColors();
    vanta = VANTA.NET({
      el: el,
      mouseControls: true,
      touchControls: true,
      gyroControls: false,
      minHeight: 200.0,
      minWidth: 200.0,
      scale: 1.0,
      scaleMobile: 1.0,
      points: 11.0,
      maxDistance: 22.0,
      spacing: 16.0,
      showDots: true,
      color: c.color,
      backgroundColor: c.backgroundColor,
      backgroundAlpha: 0.0
    });
  }

  // ----- Theme toggle -----
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', function () {
      const next = isDark() ? 'light' : 'dark';
      root.setAttribute('data-bs-theme', next);
      localStorage.setItem('theme', next);
      const icon = btn.querySelector('.theme-icon');
      if (icon) icon.textContent = next === 'dark' ? '🌙' : '☀️';
      initVanta(); // re-init with theme-matched colors
    });
    const icon = btn.querySelector('.theme-icon');
    if (icon) icon.textContent = isDark() ? '🌙' : '☀️';
  }

  // ----- 3D tilt on cards -----
  function initTilt() {
    if (typeof VanillaTilt !== 'undefined') {
      VanillaTilt.init(document.querySelectorAll('[data-tilt]'), {
        speed: 600, glare: true, 'max-glare': 0.25, scale: 1.03
      });
    }
  }

  // ----- Scroll reveal -----
  function initReveal() {
    const items = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) {
      items.forEach(function (i) { i.classList.add('revealed'); });
      return;
    }
    const obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('revealed'); obs.unobserve(e.target); }
      });
    }, { threshold: 0.15 });
    items.forEach(function (i) { obs.observe(i); });
  }

  window.addEventListener('DOMContentLoaded', function () {
    initVanta();
    initTilt();
    initReveal();
  });
})();
