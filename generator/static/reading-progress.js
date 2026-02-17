// Reading progress tracking (visited/completed chapters, scroll detection)
(function() {
    'use strict';

    function markChapterVisited(novelSlug, chapterId, chapterTitle) {
        const visitedKey = 'visited_' + novelSlug;
        var visitedChapters = JSON.parse(localStorage.getItem(visitedKey) || '{}');

        visitedChapters[chapterId] = {
            title: chapterTitle,
            visitedAt: new Date().toISOString(),
            completed: (visitedChapters[chapterId] && visitedChapters[chapterId].completed) || false
        };

        localStorage.setItem(visitedKey, JSON.stringify(visitedChapters));
    }

    function markChapterCompleted(novelSlug, chapterId) {
        const visitedKey = 'visited_' + novelSlug;
        var visitedChapters = JSON.parse(localStorage.getItem(visitedKey) || '{}');

        if (visitedChapters[chapterId]) {
            visitedChapters[chapterId].completed = true;
            visitedChapters[chapterId].completedAt = new Date().toISOString();
            localStorage.setItem(visitedKey, JSON.stringify(visitedChapters));

            // Update latest chapter read
            const latestKey = 'latest_' + novelSlug;
            localStorage.setItem(latestKey, JSON.stringify({
                chapterId: chapterId,
                title: visitedChapters[chapterId].title,
                completedAt: visitedChapters[chapterId].completedAt
            }));
        }
    }

    function setupScrollTracking(novelSlug, chapterId) {
        var hasScrolledToEnd = false;

        function checkScrollProgress() {
            if (hasScrolledToEnd) return;

            var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            var windowHeight = window.innerHeight;
            var documentHeight = document.documentElement.scrollHeight;

            // Try to find meaningful completion points
            var completionPoint = documentHeight - 200;

            var commentsSection = document.querySelector('.comments-section, #utterances-container, [data-repo]');
            if (commentsSection) {
                var commentsTop = commentsSection.getBoundingClientRect().top + scrollTop;
                completionPoint = Math.min(commentsTop - windowHeight * 0.3, completionPoint);
            }

            var footer = document.querySelector('footer');
            if (footer) {
                var footerTop = footer.getBoundingClientRect().top + scrollTop;
                completionPoint = Math.min(footerTop - windowHeight * 0.5, completionPoint);
            }

            var contentWrapper = document.querySelector('#chapter-content-wrapper, .chapter-content');
            if (contentWrapper) {
                var contentBottom = contentWrapper.getBoundingClientRect().bottom + scrollTop;
                completionPoint = Math.min(contentBottom + 100, completionPoint);
            }

            var scrolledToEnd = (scrollTop + windowHeight) >= completionPoint;

            if (scrolledToEnd) {
                hasScrolledToEnd = true;
                markChapterCompleted(novelSlug, chapterId);
            }
        }

        window.addEventListener('scroll', checkScrollProgress);
        window.addEventListener('resize', checkScrollProgress);

        // Check on load in case content is short
        setTimeout(checkScrollProgress, 1000);

        // Handle chapter navigation links
        var chapterLinks = document.querySelectorAll('nav a[href*="../"]:not([href*="toc"]), .chapter-nav a[href*="../"]:not([href*="toc"])');
        chapterLinks.forEach(function(link) {
            var linkText = link.textContent.toLowerCase();
            var isNextChapter = linkText.includes('next') || (linkText.includes('chapter') && !linkText.includes('previous') && !linkText.includes('prev'));
            var isPrevChapter = linkText.includes('prev') || linkText.includes('previous');

            if (isNextChapter || isPrevChapter) {
                link.addEventListener('click', function(e) {
                    if (isNextChapter) {
                        markChapterCompleted(novelSlug, chapterId);
                    }

                    var autoScroll = localStorage.getItem('autoScrollToContent');
                    if (autoScroll === 'true') {
                        e.preventDefault();
                        var url = new URL(link.href, window.location.href);
                        url.searchParams.set('scroll', 'content');
                        window.location.href = url.toString();
                    }
                });
            }
        });
    }

    function initReadingProgress(novelSlug, chapterId, chapterTitle, isManga) {
        markChapterVisited(novelSlug, chapterId, chapterTitle);
        if (!isManga) {
            setupScrollTracking(novelSlug, chapterId);
        }
    }

    // Expose to global scope
    window.initReadingProgress = initReadingProgress;
    window.markChapterCompleted = markChapterCompleted;
    window.markChapterVisited = markChapterVisited;
})();
