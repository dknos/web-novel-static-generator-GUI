// Footnote tooltip preview (desktop hover, mobile tap modal)
(function() {
    'use strict';

    var tooltip = null;
    var activeRef = null;

    function createTooltip() {
        if (tooltip) return tooltip;
        tooltip = document.createElement('div');
        tooltip.className = 'footnote-tooltip';
        tooltip.setAttribute('role', 'tooltip');
        tooltip.style.display = 'none';
        document.body.appendChild(tooltip);
        return tooltip;
    }

    function positionTooltip(ref) {
        var rect = ref.getBoundingClientRect();
        var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        var scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        tooltip.style.display = 'block';

        var tooltipRect = tooltip.getBoundingClientRect();
        var left = rect.left + scrollLeft + (rect.width / 2) - (tooltipRect.width / 2);
        var top = rect.top + scrollTop - tooltipRect.height - 8;

        // Keep within viewport
        if (left < 8) left = 8;
        if (left + tooltipRect.width > window.innerWidth - 8) {
            left = window.innerWidth - tooltipRect.width - 8;
        }
        if (top < scrollTop + 8) {
            top = rect.bottom + scrollTop + 8; // Show below if no room above
        }

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }

    function showTooltip(ref) {
        var footnoteId = ref.getAttribute('href');
        if (!footnoteId) return;

        var footnote = document.querySelector(footnoteId);
        if (!footnote) return;

        createTooltip();

        // Clone footnote content, remove backref links
        var clone = footnote.cloneNode(true);
        var backrefs = clone.querySelectorAll('.footnote-backref, a[href^="#fnref"]');
        backrefs.forEach(function(el) { el.remove(); });

        tooltip.innerHTML = clone.innerHTML;
        activeRef = ref;
        positionTooltip(ref);
    }

    function hideTooltip() {
        if (tooltip) {
            tooltip.style.display = 'none';
        }
        activeRef = null;
    }

    // Mobile modal overlay
    function showFootnoteModal(ref) {
        var footnoteId = ref.getAttribute('href');
        if (!footnoteId) return;

        var footnote = document.querySelector(footnoteId);
        if (!footnote) return;

        var clone = footnote.cloneNode(true);
        var backrefs = clone.querySelectorAll('.footnote-backref, a[href^="#fnref"]');
        backrefs.forEach(function(el) { el.remove(); });

        var modal = document.createElement('div');
        modal.className = 'footnote-modal';
        modal.innerHTML =
            '<div class="footnote-modal-overlay"></div>' +
            '<div class="footnote-modal-content">' +
                '<button class="footnote-modal-close" aria-label="Close">&times;</button>' +
                '<div class="footnote-modal-body">' + clone.innerHTML + '</div>' +
            '</div>';

        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';

        function closeModal() {
            document.body.removeChild(modal);
            document.body.style.overflow = '';
        }

        modal.querySelector('.footnote-modal-overlay').addEventListener('click', closeModal);
        modal.querySelector('.footnote-modal-close').addEventListener('click', closeModal);
        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escHandler);
            }
        });
    }

    function isMobile() {
        return window.matchMedia('(max-width: 768px)').matches || 'ontouchstart' in window;
    }

    function initFootnotePreview() {
        var footnoteRefs = document.querySelectorAll('sup a[href^="#fn"], a.footnote-ref');
        if (footnoteRefs.length === 0) return;

        footnoteRefs.forEach(function(ref) {
            if (isMobile()) {
                ref.addEventListener('click', function(e) {
                    e.preventDefault();
                    showFootnoteModal(ref);
                });
            } else {
                ref.addEventListener('mouseenter', function() {
                    showTooltip(ref);
                });
                ref.addEventListener('mouseleave', function() {
                    hideTooltip();
                });
                ref.addEventListener('focus', function() {
                    showTooltip(ref);
                });
                ref.addEventListener('blur', function() {
                    hideTooltip();
                });
            }
        });
    }

    document.addEventListener('DOMContentLoaded', initFootnotePreview);
})();
