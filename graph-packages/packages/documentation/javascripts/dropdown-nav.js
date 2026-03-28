/**
 * Dropdown Navigation for Material for MkDocs
 *
 * Transforms the left sidebar navigation into dropdown menus attached to top
 * navigation tabs. Supports hover, click, keyboard navigation, and touch events.
 *
 * Features:
 * - Hover to show dropdowns (with delay to prevent flicker)
 * - Click to navigate
 * - Keyboard navigation (arrow keys, escape to close)
 * - Touch events for mobile
 * - Nested dropdown support
 * - Close on outside click
 * - Optional state persistence
 *
 * Uses CSS class naming consistent with Material for MkDocs:
 * - .md-tabs__item--has-children
 * - .md-tabs__dropdown
 * - .md-tabs__dropdown-item
 * - .md-tabs__dropdown-section
 */
(function() {
  'use strict';

  // ============================================
  // Configuration
  // ============================================

  const CONFIG = {
    hoverDelay: 100,           // ms before showing dropdown on hover
    hoverCloseDelay: 250,      // ms before hiding dropdown when mouse leaves
    storageKey: 'dropdown-nav-last-open',
    enablePersistence: false,  // Set to true to remember last open dropdown
    touchHoldDelay: 500,       // ms for touch-and-hold to show dropdown
    animationDuration: 150     // ms for dropdown animation
  };

  // ============================================
  // State
  // ============================================

  let activeDropdown = null;
  let hoverTimeouts = new Map();
  let closeTimeouts = new Map();
  let focusedItemIndex = -1;
  let currentDropdownItems = [];

  // ============================================
  // Utility Functions
  // ============================================

  /**
   * Debounce function execution
   */
  function debounce(fn, delay) {
    let timeoutId;
    return function(...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  /**
   * Create an element with classes and attributes
   */
  function createElement(tag, classes = [], attrs = {}) {
    const el = document.createElement(tag);
    classes.forEach(c => el.classList.add(c));
    Object.entries(attrs).forEach(([key, value]) => {
      if (key === 'textContent') {
        el.textContent = value;
      } else if (key === 'innerHTML') {
        el.innerHTML = value;
      } else {
        el.setAttribute(key, value);
      }
    });
    return el;
  }

  /**
   * Get navigation data from sidebar
   */
  function extractNavData() {
    const primaryNav = document.querySelector('.md-sidebar--primary .md-nav--primary');
    if (!primaryNav) return [];

    const topLevelItems = primaryNav.querySelectorAll(':scope > .md-nav__list > .md-nav__item');
    const navData = [];

    topLevelItems.forEach(item => {
      const link = item.querySelector(':scope > .md-nav__link, :scope > label.md-nav__link');
      if (!link) return;

      // Get href from link or from nested anchor
      let href = link.getAttribute('href');
      if (!href) {
        const nestedLink = link.querySelector('a');
        if (nestedLink) {
          href = nestedLink.getAttribute('href');
        }
      }

      const navItem = {
        label: link.textContent.trim(),
        href: href,
        isSection: item.classList.contains('md-nav__item--nested'),
        isActive: item.classList.contains('md-nav__item--active'),
        children: []
      };

      // Extract nested items
      const nestedNav = item.querySelector(':scope > .md-nav');
      if (nestedNav) {
        navItem.children = extractNestedItems(nestedNav);
      }

      navData.push(navItem);
    });

    return navData;
  }

  /**
   * Recursively extract nested navigation items
   */
  function extractNestedItems(navElement, depth = 0) {
    const items = [];
    const listItems = navElement.querySelectorAll(':scope > .md-nav__list > .md-nav__item');

    listItems.forEach(item => {
      const link = item.querySelector(':scope > .md-nav__link, :scope > label.md-nav__link');
      if (!link) return;

      // Get href from link or from nested anchor
      let href = link.getAttribute('href');
      if (!href) {
        const nestedLink = link.querySelector('a');
        if (nestedLink) {
          href = nestedLink.getAttribute('href');
        }
      }

      const navItem = {
        label: link.textContent.trim(),
        href: href,
        isSection: item.classList.contains('md-nav__item--nested'),
        isActive: item.classList.contains('md-nav__item--active'),
        depth: depth,
        children: []
      };

      // Extract nested items recursively
      const nestedNav = item.querySelector(':scope > .md-nav');
      if (nestedNav) {
        navItem.children = extractNestedItems(nestedNav, depth + 1);
      }

      items.push(navItem);
    });

    return items;
  }

  // ============================================
  // Dropdown Creation
  // ============================================

  /**
   * Create a dropdown menu from navigation data
   */
  function createDropdown(navItem) {
    if (navItem.children.length === 0) {
      return null;
    }

    const dropdown = createElement('div', ['md-tabs__dropdown'], {
      'role': 'menu',
      'aria-label': `${navItem.label} submenu`
    });

    // Build dropdown content recursively
    buildDropdownContent(dropdown, navItem.children, 1);

    return dropdown;
  }

  /**
   * Build dropdown content from navigation items
   */
  function buildDropdownContent(container, items, level) {
    items.forEach(item => {
      if (item.isSection && item.children.length > 0) {
        // This is a section header
        const section = createElement('div', ['md-tabs__dropdown-section'], {
          'role': 'presentation',
          'textContent': item.label
        });
        container.appendChild(section);

        // Add children
        buildDropdownContent(container, item.children, level + 1);
      } else if (item.href) {
        // This is a navigable link
        const linkClasses = ['md-tabs__dropdown-item'];

        // Add depth class
        if (level >= 2) {
          linkClasses.push(`md-tabs__dropdown-item--level-${Math.min(level, 3)}`);
        }

        // Add active class
        if (item.isActive) {
          linkClasses.push('md-tabs__dropdown-item--active');
        }

        const link = createElement('a', linkClasses, {
          'href': item.href,
          'role': 'menuitem',
          'tabindex': '-1',
          'textContent': item.label
        });

        container.appendChild(link);

        // If this item has children, add them indented
        if (item.children.length > 0) {
          buildDropdownContent(container, item.children, level + 1);
        }
      } else {
        // Section without href - just add label and children
        const section = createElement('div', ['md-tabs__dropdown-section'], {
          'role': 'presentation',
          'textContent': item.label
        });
        container.appendChild(section);

        if (item.children.length > 0) {
          buildDropdownContent(container, item.children, level + 1);
        }
      }
    });
  }

  /**
   * Create dropdown attached to a tab item
   */
  function attachDropdownToTab(tabItem, navItem) {
    // Mark tab as having children
    tabItem.classList.add('md-tabs__item--has-children');

    // Create dropdown
    const dropdown = createDropdown(navItem);
    if (!dropdown) {
      tabItem.classList.remove('md-tabs__item--has-children');
      tabItem.classList.add('md-tabs__item--no-dropdown');
      return;
    }

    // Get the tab link
    const tabLink = tabItem.querySelector('.md-tabs__link');
    if (!tabLink) return;

    // Set ARIA attributes on trigger
    tabLink.setAttribute('aria-haspopup', 'true');
    tabLink.setAttribute('aria-expanded', 'false');

    // Append dropdown to tab item
    tabItem.appendChild(dropdown);

    // Setup event handlers
    setupDropdownEvents(tabItem, tabLink, dropdown);
  }

  // ============================================
  // Event Handlers
  // ============================================

  /**
   * Setup all event handlers for a dropdown
   */
  function setupDropdownEvents(tabItem, tabLink, dropdown) {
    // Clear any existing timeouts for this item
    const clearItemTimeouts = () => {
      if (hoverTimeouts.has(tabItem)) {
        clearTimeout(hoverTimeouts.get(tabItem));
        hoverTimeouts.delete(tabItem);
      }
      if (closeTimeouts.has(tabItem)) {
        clearTimeout(closeTimeouts.get(tabItem));
        closeTimeouts.delete(tabItem);
      }
    };

    // Mouse enter - show dropdown after delay
    tabItem.addEventListener('mouseenter', () => {
      clearItemTimeouts();

      const timeout = setTimeout(() => {
        showDropdown(tabItem, tabLink, dropdown);
      }, CONFIG.hoverDelay);

      hoverTimeouts.set(tabItem, timeout);
    });

    // Mouse leave - hide dropdown after delay
    tabItem.addEventListener('mouseleave', () => {
      clearItemTimeouts();

      const timeout = setTimeout(() => {
        hideDropdown(tabItem, tabLink, dropdown);
      }, CONFIG.hoverCloseDelay);

      closeTimeouts.set(tabItem, timeout);
    });

    // Click on tab link
    tabLink.addEventListener('click', (e) => {
      const isOpen = dropdown.classList.contains('md-tabs__dropdown--visible') ||
                     tabItem.matches(':hover .md-tabs__dropdown');

      if (isOpen) {
        // If dropdown is open and tab has href, navigate
        const href = tabLink.getAttribute('href');
        if (href && href !== '#') {
          // Let the default click behavior happen
          return;
        }
      }

      // Toggle dropdown
      e.preventDefault();
      if (dropdown.classList.contains('md-tabs__dropdown--visible')) {
        hideDropdown(tabItem, tabLink, dropdown);
      } else {
        closeAllDropdowns();
        showDropdown(tabItem, tabLink, dropdown);
      }
    });

    // Keyboard navigation on trigger
    tabLink.addEventListener('keydown', (e) => {
      handleTriggerKeydown(e, tabItem, tabLink, dropdown);
    });

    // Keyboard navigation within dropdown
    dropdown.addEventListener('keydown', (e) => {
      handleDropdownKeydown(e, tabItem, tabLink, dropdown);
    });

    // Touch events for mobile
    setupTouchEvents(tabItem, tabLink, dropdown);
  }

  /**
   * Setup touch events for mobile devices
   */
  function setupTouchEvents(tabItem, tabLink, dropdown) {
    let touchStartTime = 0;
    let touchStartPos = { x: 0, y: 0 };
    let isTouchDevice = false;

    tabLink.addEventListener('touchstart', (e) => {
      isTouchDevice = true;
      touchStartTime = Date.now();
      touchStartPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }, { passive: true });

    tabLink.addEventListener('touchend', (e) => {
      if (!isTouchDevice) return;

      const touchDuration = Date.now() - touchStartTime;
      const touch = e.changedTouches[0];
      const moved = Math.abs(touch.clientX - touchStartPos.x) > 10 ||
                    Math.abs(touch.clientY - touchStartPos.y) > 10;

      // Only handle taps (not scrolls)
      if (!moved && touchDuration < CONFIG.touchHoldDelay) {
        const isVisible = dropdown.classList.contains('md-tabs__dropdown--visible');

        if (!isVisible) {
          e.preventDefault();
          closeAllDropdowns();
          showDropdown(tabItem, tabLink, dropdown);
        }
        // If visible and tap, let the click handler handle navigation
      }
    });
  }

  /**
   * Handle keydown on trigger element
   */
  function handleTriggerKeydown(e, tabItem, tabLink, dropdown) {
    const isOpen = dropdown.classList.contains('md-tabs__dropdown--visible');

    switch (e.key) {
      case 'Enter':
      case ' ':
        if (!isOpen) {
          e.preventDefault();
          showDropdown(tabItem, tabLink, dropdown);
          focusFirstItem(dropdown);
        }
        // If open, let Enter navigate to href
        break;

      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          showDropdown(tabItem, tabLink, dropdown);
        }
        focusFirstItem(dropdown);
        break;

      case 'ArrowUp':
        e.preventDefault();
        if (!isOpen) {
          showDropdown(tabItem, tabLink, dropdown);
        }
        focusLastItem(dropdown);
        break;

      case 'Escape':
        if (isOpen) {
          e.preventDefault();
          hideDropdown(tabItem, tabLink, dropdown);
          tabLink.focus();
        }
        break;
    }
  }

  /**
   * Handle keydown within dropdown menu
   */
  function handleDropdownKeydown(e, tabItem, tabLink, dropdown) {
    const items = Array.from(dropdown.querySelectorAll('.md-tabs__dropdown-item'));
    currentDropdownItems = items;

    const currentIndex = items.indexOf(document.activeElement);

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (currentIndex < items.length - 1) {
          items[currentIndex + 1].focus();
          focusedItemIndex = currentIndex + 1;
        } else {
          // Wrap to first
          items[0].focus();
          focusedItemIndex = 0;
        }
        break;

      case 'ArrowUp':
        e.preventDefault();
        if (currentIndex > 0) {
          items[currentIndex - 1].focus();
          focusedItemIndex = currentIndex - 1;
        } else {
          // Wrap to last
          items[items.length - 1].focus();
          focusedItemIndex = items.length - 1;
        }
        break;

      case 'Home':
        e.preventDefault();
        items[0]?.focus();
        focusedItemIndex = 0;
        break;

      case 'End':
        e.preventDefault();
        items[items.length - 1]?.focus();
        focusedItemIndex = items.length - 1;
        break;

      case 'Escape':
        e.preventDefault();
        hideDropdown(tabItem, tabLink, dropdown);
        tabLink.focus();
        break;

      case 'Tab':
        // Let tab close dropdown and move focus naturally
        hideDropdown(tabItem, tabLink, dropdown);
        break;

      case 'Enter':
        // Allow default link behavior - navigate to href
        break;

      default:
        // Type-ahead search - find item starting with typed character
        if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
          const char = e.key.toLowerCase();
          const startIndex = (currentIndex + 1) % items.length;

          // Search from current position forward, then wrap
          for (let i = 0; i < items.length; i++) {
            const idx = (startIndex + i) % items.length;
            const itemText = items[idx].textContent.trim().toLowerCase();
            if (itemText.startsWith(char)) {
              items[idx].focus();
              focusedItemIndex = idx;
              break;
            }
          }
        }
    }
  }

  // ============================================
  // Focus Management
  // ============================================

  function focusFirstItem(dropdown) {
    const items = dropdown.querySelectorAll('.md-tabs__dropdown-item');
    if (items.length > 0) {
      items[0].focus();
      focusedItemIndex = 0;
    }
  }

  function focusLastItem(dropdown) {
    const items = dropdown.querySelectorAll('.md-tabs__dropdown-item');
    if (items.length > 0) {
      const lastIndex = items.length - 1;
      items[lastIndex].focus();
      focusedItemIndex = lastIndex;
    }
  }

  // ============================================
  // Dropdown Show/Hide
  // ============================================

  function showDropdown(tabItem, tabLink, dropdown) {
    // Close other dropdowns first
    closeAllDropdowns();

    tabItem.classList.add('md-tabs__item--dropdown-open');
    tabLink.setAttribute('aria-expanded', 'true');
    dropdown.classList.add('md-tabs__dropdown--visible');
    activeDropdown = tabItem;

    // Position dropdown to stay in viewport
    positionDropdown(tabItem, dropdown);

    // Save state if persistence is enabled
    if (CONFIG.enablePersistence) {
      const label = tabLink.textContent.trim();
      try {
        localStorage.setItem(CONFIG.storageKey, label);
      } catch (e) {
        // localStorage may not be available
      }
    }
  }

  function hideDropdown(tabItem, tabLink, dropdown) {
    tabItem.classList.remove('md-tabs__item--dropdown-open');
    tabLink.setAttribute('aria-expanded', 'false');
    dropdown.classList.remove('md-tabs__dropdown--visible');

    if (activeDropdown === tabItem) {
      activeDropdown = null;
    }

    focusedItemIndex = -1;
  }

  function closeAllDropdowns() {
    document.querySelectorAll('.md-tabs__item--has-children').forEach(tabItem => {
      const tabLink = tabItem.querySelector('.md-tabs__link');
      const dropdown = tabItem.querySelector('.md-tabs__dropdown');
      if (tabLink && dropdown) {
        hideDropdown(tabItem, tabLink, dropdown);
      }
    });
  }

  /**
   * Position dropdown to stay within viewport
   */
  function positionDropdown(tabItem, dropdown) {
    // Reset positioning
    dropdown.style.left = '';
    dropdown.style.right = '';
    dropdown.style.maxHeight = '';
    dropdown.style.overflowY = '';

    // Get dimensions after reset
    const rect = dropdown.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Horizontal: prevent overflow on right side
    if (rect.right > viewportWidth - 16) {
      dropdown.style.left = 'auto';
      dropdown.style.right = '0';
    }

    // Horizontal: prevent overflow on left side
    if (rect.left < 16) {
      dropdown.style.left = '0';
      dropdown.style.right = 'auto';
    }

    // Vertical: limit height if it would overflow
    const maxHeight = viewportHeight - rect.top - 32;
    if (rect.height > maxHeight && maxHeight > 200) {
      dropdown.style.maxHeight = `${maxHeight}px`;
      dropdown.style.overflowY = 'auto';
    }
  }

  // ============================================
  // Initialization
  // ============================================

  function init() {
    // Check if tabs exist (they're hidden on mobile)
    const tabsContainer = document.querySelector('.md-tabs__list');
    if (!tabsContainer) return;

    // Only init if not already initialized
    if (document.body.classList.contains('dropdown-nav--initialized')) {
      return;
    }

    // Extract navigation data from sidebar
    const navData = extractNavData();
    if (navData.length === 0) return;

    // Get all tab items
    const tabItems = tabsContainer.querySelectorAll('.md-tabs__item');

    // Match tabs with navigation data by label
    tabItems.forEach(tabItem => {
      const tabLink = tabItem.querySelector('.md-tabs__link');
      if (!tabLink) return;

      const tabLabel = tabLink.textContent.trim();
      const matchingNav = navData.find(nav => nav.label === tabLabel);

      if (matchingNav && matchingNav.children.length > 0) {
        attachDropdownToTab(tabItem, matchingNav);
      } else {
        tabItem.classList.add('md-tabs__item--no-dropdown');
      }
    });

    // Mark as initialized
    document.body.classList.add('dropdown-nav--initialized');

    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.md-tabs__item--has-children')) {
        closeAllDropdowns();
      }
    });

    // Close dropdowns on scroll (debounced)
    window.addEventListener('scroll', debounce(() => {
      closeAllDropdowns();
    }, 100), { passive: true });

    // Close dropdowns on window resize
    window.addEventListener('resize', debounce(() => {
      closeAllDropdowns();
    }, 100));

    // Restore last open dropdown if persistence is enabled
    if (CONFIG.enablePersistence) {
      try {
        const lastOpen = localStorage.getItem(CONFIG.storageKey);
        if (lastOpen) {
          const tabItem = Array.from(tabItems).find(item => {
            const link = item.querySelector('.md-tabs__link');
            return link && link.textContent.trim() === lastOpen;
          });

          if (tabItem) {
            const tabLink = tabItem.querySelector('.md-tabs__link');
            const dropdown = tabItem.querySelector('.md-tabs__dropdown');
            if (tabLink && dropdown) {
              // Delay to ensure layout is complete
              requestAnimationFrame(() => {
                showDropdown(tabItem, tabLink, dropdown);
              });
            }
          }
        }
      } catch (e) {
        // localStorage may not be available
      }
    }
  }

  // ============================================
  // Bootstrap
  // ============================================

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Re-initialize on navigation (for Material for MkDocs instant loading)
  // Material uses a custom event system for SPA-like navigation
  if (typeof document$ !== 'undefined') {
    // MkDocs Material uses RxJS observables
    document$.subscribe(() => {
      // Reset initialization state on page change
      document.body.classList.remove('dropdown-nav--initialized');
      init();
    });
  } else {
    // Fallback: listen for location changes
    let lastUrl = location.href;
    new MutationObserver(() => {
      if (location.href !== lastUrl) {
        lastUrl = location.href;
        document.body.classList.remove('dropdown-nav--initialized');
        init();
      }
    }).observe(document.body, { childList: true, subtree: true });
  }
})();
