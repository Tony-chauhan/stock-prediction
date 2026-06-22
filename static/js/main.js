// Dark/light mode toggle persisted in localStorage
(function () {
  const root = document.documentElement;
  const saved = localStorage.getItem('theme');
  if (saved) root.setAttribute('data-bs-theme', saved);

  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', function () {
      const next = root.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-bs-theme', next);
      localStorage.setItem('theme', next);
    });
  }
})();
