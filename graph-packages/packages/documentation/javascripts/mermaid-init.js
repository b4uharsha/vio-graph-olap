// Initialize Mermaid with ELK layout support and dark mode detection
document$.subscribe(function() {
  const theme = document.body.getAttribute('data-md-color-scheme') === 'slate'
    ? 'dark'
    : 'default';

  mermaid.initialize({
    startOnLoad: true,
    theme: theme,
    securityLevel: 'loose',
    flowchart: {
      useMaxWidth: true,
      htmlLabels: true,
      curve: 'basis'
    }
  });
});
