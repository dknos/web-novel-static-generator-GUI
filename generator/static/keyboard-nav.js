// Keyboard navigation support + help modal
(function() {
    'use strict';

    function initKeyboardNavigation(prevChapterId, nextChapterId, isManga) {
        document.addEventListener('keydown', function(e) {
            // Skip keyboard navigation for manga chapters - they have their own handlers
            if (isManga) return;

            // Skip if user is typing in an input field
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                return;
            }

            // Skip if any modifier keys are pressed
            if (e.ctrlKey || e.metaKey || e.altKey) {
                return;
            }

            switch(e.key) {
                case 'ArrowLeft':
                case 'h':
                    if (prevChapterId) {
                        var prevLink = document.querySelector('nav.chapter-nav a[href*="' + prevChapterId + '"]');
                        if (prevLink) {
                            var url = prevLink.href;
                            var autoScroll = localStorage.getItem('autoScrollToContent');
                            if (autoScroll === 'true') {
                                var urlObj = new URL(url, window.location.href);
                                urlObj.searchParams.set('scroll', 'content');
                                url = urlObj.toString();
                            }
                            window.location.href = url;
                        }
                    }
                    e.preventDefault();
                    break;

                case 'ArrowRight':
                case 'l':
                    if (nextChapterId) {
                        var nextLink = document.querySelector('nav.chapter-nav a[href*="' + nextChapterId + '"]');
                        if (nextLink) {
                            var url = nextLink.href;
                            var autoScroll = localStorage.getItem('autoScrollToContent');
                            if (autoScroll === 'true') {
                                var urlObj = new URL(url, window.location.href);
                                urlObj.searchParams.set('scroll', 'content');
                                url = urlObj.toString();
                            }
                            window.location.href = url;
                        }
                    }
                    e.preventDefault();
                    break;

                case 'ArrowUp':
                case 'k':
                    window.scrollBy(0, -100);
                    e.preventDefault();
                    break;

                case 'ArrowDown':
                case 'j':
                    window.scrollBy(0, 100);
                    e.preventDefault();
                    break;

                case 'Home':
                case 'g':
                    window.scrollTo(0, 0);
                    e.preventDefault();
                    break;

                case 'End':
                case 'G':
                    window.scrollTo(0, document.body.scrollHeight);
                    e.preventDefault();
                    break;

                case 't':
                    var tocLink = document.querySelector('nav.chapter-nav a[href*="toc"]');
                    if (tocLink) {
                        window.location.href = tocLink.href;
                    }
                    e.preventDefault();
                    break;

                case '=':
                case '+':
                    if (window.adjustTextSize) window.adjustTextSize(1);
                    e.preventDefault();
                    break;

                case '-':
                    if (window.adjustTextSize) window.adjustTextSize(-1);
                    e.preventDefault();
                    break;

                case '0':
                    if (window.resetReadingSettings) window.resetReadingSettings();
                    e.preventDefault();
                    break;

                case '?':
                    showKeyboardHelp();
                    e.preventDefault();
                    break;
            }
        });
    }

    function showKeyboardHelp() {
        var existingModal = document.getElementById('keyboard-help-modal');
        if (existingModal) {
            existingModal.style.display = 'block';
            existingModal.querySelector('.help-close').focus();
            return;
        }

        var modal = document.createElement('div');
        modal.id = 'keyboard-help-modal';
        modal.className = 'keyboard-help-modal';
        modal.innerHTML =
            '<div class="help-content">' +
                '<div class="help-header">' +
                    '<h3>Keyboard Shortcuts</h3>' +
                    '<button class="help-close" aria-label="Close help">&times;</button>' +
                '</div>' +
                '<div class="help-body">' +
                    '<div class="help-section">' +
                        '<h4>Navigation</h4>' +
                        '<ul>' +
                            '<li><kbd>\u2190</kbd> or <kbd>h</kbd> - Previous chapter</li>' +
                            '<li><kbd>\u2192</kbd> or <kbd>l</kbd> - Next chapter</li>' +
                            '<li><kbd>t</kbd> - Table of contents</li>' +
                        '</ul>' +
                    '</div>' +
                    '<div class="help-section">' +
                        '<h4>Scrolling</h4>' +
                        '<ul>' +
                            '<li><kbd>\u2191</kbd> or <kbd>k</kbd> - Scroll up</li>' +
                            '<li><kbd>\u2193</kbd> or <kbd>j</kbd> - Scroll down</li>' +
                            '<li><kbd>Home</kbd> or <kbd>g</kbd> - Go to top</li>' +
                            '<li><kbd>End</kbd> or <kbd>G</kbd> - Go to bottom</li>' +
                        '</ul>' +
                    '</div>' +
                    '<div class="help-section">' +
                        '<h4>Reading Settings</h4>' +
                        '<ul>' +
                            '<li><kbd>+</kbd> or <kbd>=</kbd> - Increase text size</li>' +
                            '<li><kbd>-</kbd> - Decrease text size</li>' +
                            '<li><kbd>0</kbd> - Reset all settings</li>' +
                        '</ul>' +
                    '</div>' +
                    '<div class="help-section">' +
                        '<h4>Help</h4>' +
                        '<ul>' +
                            '<li><kbd>?</kbd> - Show this help</li>' +
                            '<li><kbd>Esc</kbd> - Close help/modals</li>' +
                        '</ul>' +
                    '</div>' +
                '</div>' +
            '</div>' +
            '<div class="help-overlay"></div>';

        document.body.appendChild(modal);

        var closeBtn = modal.querySelector('.help-close');
        closeBtn.focus();

        closeBtn.addEventListener('click', function() {
            document.body.removeChild(modal);
        });

        modal.querySelector('.help-overlay').addEventListener('click', function() {
            document.body.removeChild(modal);
        });

        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                if (document.getElementById('keyboard-help-modal')) {
                    document.body.removeChild(modal);
                }
                document.removeEventListener('keydown', escHandler);
            }
        });
    }

    // Expose to global scope
    window.initKeyboardNavigation = initKeyboardNavigation;
    window.showKeyboardHelp = showKeyboardHelp;
})();
