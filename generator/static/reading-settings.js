// Reading settings functionality (text size, line spacing, font family, max width, auto-scroll, auto-advance)
(function() {
    'use strict';

    var currentTextSize = 100;
    var currentLineSpacing = 1.6;
    var autoScrollToContent = false;

    function loadReadingSettings() {
        var savedTextSize = localStorage.getItem('readingTextSize');
        var savedLineSpacing = localStorage.getItem('readingLineSpacing');
        var savedAutoScroll = localStorage.getItem('autoScrollToContent');
        var savedFontFamily = localStorage.getItem('readingFontFamily');
        var savedMaxWidth = localStorage.getItem('readingMaxWidth');
        var savedAutoAdvance = localStorage.getItem('autoAdvance');

        if (savedTextSize) {
            currentTextSize = parseInt(savedTextSize);
            applyTextSize();
        }

        if (savedLineSpacing) {
            currentLineSpacing = parseFloat(savedLineSpacing);
            applyLineSpacing();
        }

        if (savedAutoScroll !== null) {
            autoScrollToContent = savedAutoScroll === 'true';
            var checkbox = document.getElementById('auto-scroll-content');
            if (checkbox) checkbox.checked = autoScrollToContent;
        }

        if (savedFontFamily && savedFontFamily !== 'default') {
            applyFontFamily(savedFontFamily);
            var fontSelect = document.getElementById('font-family-select');
            if (fontSelect) fontSelect.value = savedFontFamily;
        }

        if (savedMaxWidth && savedMaxWidth !== 'default') {
            applyMaxWidth(savedMaxWidth);
            var widthSelect = document.getElementById('max-width-select');
            if (widthSelect) widthSelect.value = savedMaxWidth;
        }

        if (savedAutoAdvance !== null) {
            var advanceCheckbox = document.getElementById('auto-advance-toggle');
            if (advanceCheckbox) advanceCheckbox.checked = savedAutoAdvance === 'true';
        }

        updateDisplays();
    }

    function adjustTextSize(delta) {
        currentTextSize = Math.max(70, Math.min(200, currentTextSize + (delta * 10)));
        applyTextSize();
        localStorage.setItem('readingTextSize', currentTextSize);
        updateDisplays();
    }

    function adjustLineSpacing(delta) {
        currentLineSpacing = Math.max(1.0, Math.min(3.0, currentLineSpacing + delta));
        applyLineSpacing();
        localStorage.setItem('readingLineSpacing', currentLineSpacing);
        updateDisplays();
    }

    function applyTextSize() {
        document.documentElement.style.setProperty('--reading-font-size', (currentTextSize / 100) + 'rem');
    }

    function applyLineSpacing() {
        document.documentElement.style.setProperty('--reading-line-height', currentLineSpacing);
    }

    function changeFontFamily(value) {
        if (value === 'default') {
            document.documentElement.style.removeProperty('--reading-font-family');
            localStorage.removeItem('readingFontFamily');
        } else {
            applyFontFamily(value);
            localStorage.setItem('readingFontFamily', value);
        }
    }

    function applyFontFamily(value) {
        document.documentElement.style.setProperty('--reading-font-family', value);
    }

    function changeMaxWidth(value) {
        if (value === 'default') {
            document.documentElement.style.removeProperty('--reading-max-width');
            localStorage.removeItem('readingMaxWidth');
        } else {
            applyMaxWidth(value);
            localStorage.setItem('readingMaxWidth', value);
        }
    }

    function applyMaxWidth(value) {
        document.documentElement.style.setProperty('--reading-max-width', value + 'px');
    }

    function updateDisplays() {
        var sizeDisplay = document.getElementById('text-size-display');
        var spacingDisplay = document.getElementById('line-spacing-display');
        if (sizeDisplay) sizeDisplay.textContent = currentTextSize + '%';
        if (spacingDisplay) spacingDisplay.textContent = currentLineSpacing.toFixed(1);
    }

    function toggleAutoScrollContent() {
        var checkbox = document.getElementById('auto-scroll-content');
        autoScrollToContent = checkbox.checked;
        localStorage.setItem('autoScrollToContent', autoScrollToContent);
    }

    function toggleAutoAdvance() {
        var checkbox = document.getElementById('auto-advance-toggle');
        localStorage.setItem('autoAdvance', checkbox.checked ? 'true' : 'false');
    }

    function resetReadingSettings() {
        currentTextSize = 100;
        currentLineSpacing = 1.6;
        autoScrollToContent = false;
        applyTextSize();
        applyLineSpacing();
        document.documentElement.style.removeProperty('--reading-font-family');
        document.documentElement.style.removeProperty('--reading-max-width');
        localStorage.removeItem('readingTextSize');
        localStorage.removeItem('readingLineSpacing');
        localStorage.removeItem('autoScrollToContent');
        localStorage.removeItem('readingFontFamily');
        localStorage.removeItem('readingMaxWidth');
        localStorage.removeItem('autoAdvance');
        var checkbox = document.getElementById('auto-scroll-content');
        if (checkbox) checkbox.checked = false;
        var advanceCheckbox = document.getElementById('auto-advance-toggle');
        if (advanceCheckbox) advanceCheckbox.checked = false;
        var fontSelect = document.getElementById('font-family-select');
        if (fontSelect) fontSelect.value = 'default';
        var widthSelect = document.getElementById('max-width-select');
        if (widthSelect) widthSelect.value = 'default';
        updateDisplays();
    }

    function handleScrollParameter() {
        var urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('scroll') === 'content') {
            setTimeout(function() {
                var contentElement = document.getElementById('chapter-content-wrapper');
                if (contentElement) {
                    var offset = contentElement.offsetTop - 20;
                    window.scrollTo({ top: offset, behavior: 'smooth' });
                }
            }, 100);
        }
    }

    // Expose to global scope for inline onclick handlers and other scripts
    window.adjustTextSize = adjustTextSize;
    window.adjustLineSpacing = adjustLineSpacing;
    window.resetReadingSettings = resetReadingSettings;
    window.toggleAutoScrollContent = toggleAutoScrollContent;
    window.toggleAutoAdvance = toggleAutoAdvance;
    window.changeFontFamily = changeFontFamily;
    window.changeMaxWidth = changeMaxWidth;
    window.loadReadingSettings = loadReadingSettings;
    window.handleScrollParameter = handleScrollParameter;

    // Auto-init on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function() {
        loadReadingSettings();
    });
})();
