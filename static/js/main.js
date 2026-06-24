// StockPredict — front-end: theme, 3D background, tilt, scroll reveal, loading overlay
(function () {
  'use strict';

  const root = document.documentElement;

  // ---- Theme ----
  const saved = localStorage.getItem('theme');
  if (saved) root.setAttribute('data-bs-theme', saved);
  function isDark() { return root.getAttribute('data-bs-theme') === 'dark'; }

  // ---- Topbar progress ----
  const topbar = document.getElementById('topbar');
  function showProgress() {
    if (!topbar) return;
    topbar.style.width = '0';
    topbar.style.transition = 'none';
    requestAnimationFrame(function () {
      topbar.style.transition = 'width 2.5s cubic-bezier(0.1,0.8,0.2,1)';
      topbar.style.width = '85%';
    });
  }
  function finishProgress() {
    if (!topbar) return;
    topbar.style.transition = 'width 0.25s ease';
    topbar.style.width = '100%';
    setTimeout(function () { topbar.style.width = '0'; topbar.style.transition = 'none'; }, 350);
  }

  // ---- Loading overlay ----
  const overlay = document.getElementById('loading-overlay');
  function showLoading() { if (overlay) overlay.classList.add('active'); showProgress(); }

  // Attach to all forms that trigger slow work (dashboard + compare)
  function attachFormLoading() {
    var forms = document.querySelectorAll('#dash-form, #compare-form, #hero-search-form');
    forms.forEach(function (form) {
      form.addEventListener('submit', function () {
        var btn = form.querySelector('[type=submit]');
        if (btn) { btn.disabled = true; btn.textContent = 'Loading…'; }
        showLoading();
      });
    });
  }

  // ---- Vanta 3D background ----
  var vanta = null;
  function vantaColors() {
    return isDark()
      ? { color: 0xa855f7, backgroundColor: 0x0d0b1f }
      : { color: 0x6366f1, backgroundColor: 0xf3f4ff };
  }
  function initVanta() {
    var el = document.getElementById('vanta-hero');
    if (!el || typeof VANTA === 'undefined' || !VANTA.NET) return;
    if (vanta) vanta.destroy();
    var c = vantaColors();
    vanta = VANTA.NET({
      el: el, mouseControls: true, touchControls: true, gyroControls: false,
      minHeight: 200.0, minWidth: 200.0, scale: 1.0, scaleMobile: 1.0,
      points: 11.0, maxDistance: 22.0, spacing: 16.0, showDots: true,
      color: c.color, backgroundColor: c.backgroundColor, backgroundAlpha: 0.0,
    });
  }

  // ---- Theme toggle ----
  var btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', function () {
      var next = isDark() ? 'light' : 'dark';
      root.setAttribute('data-bs-theme', next);
      localStorage.setItem('theme', next);
      var icon = btn.querySelector('.theme-icon');
      if (icon) icon.textContent = next === 'dark' ? '🌙' : '☀️';
      initVanta();
    });
    var icon = btn.querySelector('.theme-icon');
    if (icon) icon.textContent = isDark() ? '🌙' : '☀️';
  }

  // ---- 3D tilt ----
  function initTilt() {
    if (typeof VanillaTilt !== 'undefined') {
      VanillaTilt.init(document.querySelectorAll('[data-tilt]'), {
        speed: 600, glare: true, 'max-glare': 0.25, scale: 1.03,
      });
    }
  }

  // ---- Scroll reveal ----
  function initReveal() {
    var items = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) {
      items.forEach(function (i) { i.classList.add('revealed'); });
      return;
    }
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('revealed'); obs.unobserve(e.target); }
      });
    }, { threshold: 0.1 });
    items.forEach(function (i) { obs.observe(i); });
  }

  // ---- Ticker input: auto-uppercase ----
  function initTickerInput() {
    var inputs = document.querySelectorAll('input[name="ticker"], #ticker-input');
    inputs.forEach(function (inp) {
      inp.addEventListener('input', function () {
        var pos = inp.selectionStart;
        inp.value = inp.value.toUpperCase();
        inp.setSelectionRange(pos, pos);
      });
    });
  }

  window.addEventListener('DOMContentLoaded', function () {
    initVanta();
    initTilt();
    initReveal();
    attachFormLoading();
    initTickerInput();
    finishProgress();
  });
})();
