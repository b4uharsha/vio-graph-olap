/**
 * TOC Toggle - Hideable Table of Contents
 *
 * Adds a toggle button to show/hide the right-side table of contents.
 * State is persisted to localStorage.
 */
(function() {
  'use strict';

  const STORAGE_KEY = 'toc-hidden';
  const HIDDEN_CLASS = 'toc-hidden';

  // SVG icons
  const ICON_HIDE = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>`;
  const ICON_SHOW = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>`;

  function createToggleButton() {
    const btn = document.createElement('button');
    btn.className = 'toc-toggle';
    btn.setAttribute('aria-label', 'Toggle table of contents');
    btn.setAttribute('title', 'Toggle table of contents');
    return btn;
  }

  function updateButtonIcon(btn, isHidden) {
    btn.innerHTML = isHidden ? ICON_SHOW : ICON_HIDE;
    btn.setAttribute('aria-expanded', !isHidden);
  }

  function isHidden() {
    return localStorage.getItem(STORAGE_KEY) === 'true';
  }

  function setHidden(hidden) {
    localStorage.setItem(STORAGE_KEY, hidden);
    document.body.classList.toggle(HIDDEN_CLASS, hidden);
  }

  function init() {
    // Only show on pages with a TOC
    const toc = document.querySelector('.md-sidebar--secondary');
    if (!toc) return;

    // Create and insert toggle button
    const btn = createToggleButton();
    document.body.appendChild(btn);

    // Apply initial state from localStorage
    const hidden = isHidden();
    document.body.classList.toggle(HIDDEN_CLASS, hidden);
    updateButtonIcon(btn, hidden);

    // Handle click
    btn.addEventListener('click', function() {
      const newHidden = !isHidden();
      setHidden(newHidden);
      updateButtonIcon(btn, newHidden);
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
