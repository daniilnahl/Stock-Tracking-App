'use strict';
// Hosting demonstration only: no connection, credential storage or API requests.
const theme = document.getElementById('theme');
theme.addEventListener('click', () => {
  const dark = document.body.classList.toggle('dark');
  theme.setAttribute('aria-pressed', String(dark));
  theme.textContent = dark ? 'Light theme' : 'Dark theme';
});
