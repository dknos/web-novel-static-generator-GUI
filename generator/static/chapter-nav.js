// Chapter navigation (dropdown jump, scroll position save/restore, next unread, auto-advance)
(function() {
    'use strict';

    function jumpToChapter() {
        var select = document.getElementById('chapter-select');
        if (select && select.value) {
            window.location.href = select.value;
        }
    }

    // Scroll position save/restore
    function getScrollKey(novelSlug, chapterId) {
        return 'scroll_' + novelSlug + '_' + chapterId;
    }

    function saveScrollPosition(novelSlug, chapterId) {
        var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        var documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        var scrollPercent = documentHeight > 0 ? (scrollTop / documentHeight) : 0;
        localStorage.setItem(getScrollKey(novelSlug, chapterId), scrollPercent.toFixed(4));
    }

    function restoreScrollPosition(novelSlug, chapterId) {
        // Don't restore if there's a scroll parameter in URL
        var urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('scroll') === 'content') return;

        var saved = localStorage.getItem(getScrollKey(novelSlug, chapterId));
        if (saved) {
            var scrollPercent = parseFloat(saved);
            var documentHeight = document.documentElement.scrollHeight - window.innerHeight;
            var targetScroll = scrollPercent * documentHeight;
            window.scrollTo(0, targetScroll);
        }
    }

    // Next unread chapter detection
    function getNextUnreadChapter(novelSlug, allChapterIds, currentChapterId) {
        var visitedKey = 'visited_' + novelSlug;
        var visitedChapters = JSON.parse(localStorage.getItem(visitedKey) || '{}');

        // Find current chapter index
        var currentIdx = allChapterIds.indexOf(currentChapterId);
        if (currentIdx === -1) return null;

        // Look for first non-completed chapter after current
        for (var i = currentIdx + 1; i < allChapterIds.length; i++) {
            var chId = allChapterIds[i];
            if (!visitedChapters[chId] || !visitedChapters[chId].completed) {
                return chId;
            }
        }

        // Wrap around to beginning
        for (var i = 0; i < currentIdx; i++) {
            var chId = allChapterIds[i];
            if (!visitedChapters[chId] || !visitedChapters[chId].completed) {
                return chId;
            }
        }

        return null;
    }

    // Auto-advance: navigate to next chapter after completion
    function setupAutoAdvance(novelSlug, chapterId, nextChapterId) {
        if (!nextChapterId) return;
        if (localStorage.getItem('autoAdvance') !== 'true') return;

        // Listen for chapter completion
        var originalMarkCompleted = window.markChapterCompleted;
        if (originalMarkCompleted) {
            window.markChapterCompleted = function(ns, cid) {
                originalMarkCompleted(ns, cid);
                if (ns === novelSlug && cid === chapterId) {
                    // Wait 2 seconds then navigate
                    setTimeout(function() {
                        var url = '../' + nextChapterId + '/';
                        var autoScroll = localStorage.getItem('autoScrollToContent');
                        if (autoScroll === 'true') {
                            url += '?scroll=content';
                        }
                        window.location.href = url;
                    }, 2000);
                }
            };
        }
    }

    // Save scroll position periodically
    function initScrollPositionTracking(novelSlug, chapterId) {
        var saveTimeout;
        window.addEventListener('scroll', function() {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(function() {
                saveScrollPosition(novelSlug, chapterId);
            }, 500);
        });

        // Restore on load
        setTimeout(function() {
            restoreScrollPosition(novelSlug, chapterId);
        }, 200);
    }

    // Expose to global scope
    window.jumpToChapter = jumpToChapter;
    window.saveScrollPosition = saveScrollPosition;
    window.restoreScrollPosition = restoreScrollPosition;
    window.getNextUnreadChapter = getNextUnreadChapter;
    window.setupAutoAdvance = setupAutoAdvance;
    window.initScrollPositionTracking = initScrollPositionTracking;
})();
