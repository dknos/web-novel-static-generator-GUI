// Reading modes: Normal, Typewriter, Focus, Paged
(function() {
    'use strict';

    var currentMode = 'normal';
    var typewriterObserver = null;
    var pagedState = { currentPage: 0, totalPages: 0 };
    var pagedControls = null;
    var focusExitBtn = null;

    function setReadingMode(mode) {
        // Cleanup previous mode
        cleanupMode(currentMode);

        currentMode = mode;
        localStorage.setItem('readingMode', mode);

        // Update button states
        var buttons = document.querySelectorAll('.reading-mode-btn');
        buttons.forEach(function(btn) {
            btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
        });

        // Apply new mode
        document.body.classList.remove('typewriter-mode', 'focus-mode', 'paged-mode');

        switch (mode) {
            case 'typewriter':
                document.body.classList.add('typewriter-mode');
                initTypewriterMode();
                break;
            case 'focus':
                document.body.classList.add('focus-mode');
                initFocusMode();
                break;
            case 'paged':
                document.body.classList.add('paged-mode');
                initPagedMode();
                break;
            default:
                // Normal mode - no special handling
                break;
        }
    }

    function cleanupMode(mode) {
        switch (mode) {
            case 'typewriter':
                cleanupTypewriterMode();
                break;
            case 'focus':
                cleanupFocusMode();
                break;
            case 'paged':
                cleanupPagedMode();
                break;
        }
    }

    // --- Typewriter Mode ---
    function initTypewriterMode() {
        var paragraphs = document.querySelectorAll('.chapter-content p');
        if (paragraphs.length === 0) return;

        // Dim all paragraphs initially
        paragraphs.forEach(function(p) {
            p.classList.add('typewriter-dim');
        });

        typewriterObserver = new IntersectionObserver(function(entries) {
            // Find the paragraph closest to the center of the viewport
            var viewportCenter = window.innerHeight / 2;
            var closest = null;
            var closestDistance = Infinity;

            paragraphs.forEach(function(p) {
                var rect = p.getBoundingClientRect();
                var pCenter = rect.top + rect.height / 2;
                var distance = Math.abs(pCenter - viewportCenter);
                if (distance < closestDistance) {
                    closestDistance = distance;
                    closest = p;
                }
            });

            paragraphs.forEach(function(p) {
                p.classList.remove('typewriter-focus');
                p.classList.add('typewriter-dim');
            });

            if (closest) {
                closest.classList.remove('typewriter-dim');
                closest.classList.add('typewriter-focus');
            }
        }, {
            threshold: [0, 0.25, 0.5, 0.75, 1.0],
            rootMargin: '-30% 0px -30% 0px'
        });

        paragraphs.forEach(function(p) {
            typewriterObserver.observe(p);
        });

        // Also update on scroll for better tracking
        window.addEventListener('scroll', typewriterScrollHandler);
    }

    function typewriterScrollHandler() {
        if (currentMode !== 'typewriter') return;
        var paragraphs = document.querySelectorAll('.chapter-content p');
        var viewportCenter = window.innerHeight / 2;
        var closest = null;
        var closestDistance = Infinity;

        paragraphs.forEach(function(p) {
            var rect = p.getBoundingClientRect();
            var pCenter = rect.top + rect.height / 2;
            var distance = Math.abs(pCenter - viewportCenter);
            if (distance < closestDistance) {
                closestDistance = distance;
                closest = p;
            }
        });

        paragraphs.forEach(function(p) {
            p.classList.remove('typewriter-focus');
            p.classList.add('typewriter-dim');
        });

        if (closest) {
            closest.classList.remove('typewriter-dim');
            closest.classList.add('typewriter-focus');
        }
    }

    function cleanupTypewriterMode() {
        if (typewriterObserver) {
            typewriterObserver.disconnect();
            typewriterObserver = null;
        }
        window.removeEventListener('scroll', typewriterScrollHandler);
        var paragraphs = document.querySelectorAll('.chapter-content p');
        paragraphs.forEach(function(p) {
            p.classList.remove('typewriter-dim', 'typewriter-focus');
        });
    }

    // --- Focus Mode ---
    function initFocusMode() {
        focusExitBtn = document.createElement('button');
        focusExitBtn.className = 'focus-exit-btn';
        focusExitBtn.textContent = 'Exit Focus Mode';
        focusExitBtn.addEventListener('click', function() {
            setReadingMode('normal');
        });
        document.body.appendChild(focusExitBtn);
    }

    function cleanupFocusMode() {
        if (focusExitBtn && focusExitBtn.parentNode) {
            focusExitBtn.parentNode.removeChild(focusExitBtn);
            focusExitBtn = null;
        }
    }

    // --- Paged Mode ---
    function initPagedMode() {
        var content = document.querySelector('.chapter-content');
        if (!content) return;

        // Create paged controls
        pagedControls = document.createElement('div');
        pagedControls.className = 'paged-controls';
        pagedControls.innerHTML =
            '<button id="paged-prev" aria-label="Previous page">&larr; Prev</button>' +
            '<span class="paged-page-indicator" id="paged-indicator"></span>' +
            '<button id="paged-next" aria-label="Next page">Next &rarr;</button>';
        document.body.appendChild(pagedControls);

        pagedState.currentPage = 0;
        updatePagedView();

        document.getElementById('paged-prev').addEventListener('click', function() {
            if (pagedState.currentPage > 0) {
                pagedState.currentPage--;
                updatePagedView();
            }
        });

        document.getElementById('paged-next').addEventListener('click', function() {
            if (pagedState.currentPage < pagedState.totalPages - 1) {
                pagedState.currentPage++;
                updatePagedView();
            }
        });

        // Keyboard navigation for paged mode
        document.addEventListener('keydown', pagedKeyHandler);

        // Recalculate on resize
        window.addEventListener('resize', updatePagedView);
    }

    function pagedKeyHandler(e) {
        if (currentMode !== 'paged') return;
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.key === 'ArrowRight' || e.key === 'l') {
            if (pagedState.currentPage < pagedState.totalPages - 1) {
                pagedState.currentPage++;
                updatePagedView();
                e.preventDefault();
            }
        } else if (e.key === 'ArrowLeft' || e.key === 'h') {
            if (pagedState.currentPage > 0) {
                pagedState.currentPage--;
                updatePagedView();
                e.preventDefault();
            }
        }
    }

    function updatePagedView() {
        var content = document.querySelector('.chapter-content');
        if (!content) return;

        var containerWidth = content.scrollWidth;
        var viewWidth = content.clientWidth;

        if (viewWidth <= 0) viewWidth = window.innerWidth - 40;

        pagedState.totalPages = Math.max(1, Math.ceil(containerWidth / viewWidth));

        // Clamp current page
        if (pagedState.currentPage >= pagedState.totalPages) {
            pagedState.currentPage = pagedState.totalPages - 1;
        }

        // Scroll the columns
        content.style.transform = 'translateX(-' + (pagedState.currentPage * viewWidth) + 'px)';

        // Update indicator
        var indicator = document.getElementById('paged-indicator');
        if (indicator) {
            indicator.textContent = (pagedState.currentPage + 1) + ' / ' + pagedState.totalPages;
        }

        // Update button states
        var prevBtn = document.getElementById('paged-prev');
        var nextBtn = document.getElementById('paged-next');
        if (prevBtn) prevBtn.disabled = pagedState.currentPage === 0;
        if (nextBtn) nextBtn.disabled = pagedState.currentPage >= pagedState.totalPages - 1;
    }

    function cleanupPagedMode() {
        if (pagedControls && pagedControls.parentNode) {
            pagedControls.parentNode.removeChild(pagedControls);
            pagedControls = null;
        }

        var content = document.querySelector('.chapter-content');
        if (content) {
            content.style.transform = '';
        }

        document.removeEventListener('keydown', pagedKeyHandler);
        window.removeEventListener('resize', updatePagedView);
        pagedState = { currentPage: 0, totalPages: 0 };
    }

    // --- Initialization ---
    function initReadingModes() {
        // Only init on chapter pages with reading mode buttons
        var modeContainer = document.querySelector('.reading-mode-buttons');
        if (!modeContainer) return;

        var buttons = modeContainer.querySelectorAll('.reading-mode-btn');
        buttons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                setReadingMode(btn.getAttribute('data-mode'));
            });
        });

        // Restore saved mode
        var saved = localStorage.getItem('readingMode');
        if (saved && saved !== 'normal') {
            setReadingMode(saved);
        }
    }

    // Expose to global scope
    window.setReadingMode = setReadingMode;

    document.addEventListener('DOMContentLoaded', initReadingModes);
})();
