// Spoiler gate: reads visited chapters from localStorage, determines highest chapter read,
// and shows/hides elements with [data-spoiler-level] based on reading progress.
(function() {
    'use strict';

    function initSpoilerGate(novelSlug) {
        var visitedKey = 'visited_' + novelSlug;
        var visited = JSON.parse(localStorage.getItem(visitedKey) || '{}');

        // Determine highest completed chapter index
        var maxLevel = 0;
        var completedCount = 0;
        Object.keys(visited).forEach(function(chId) {
            if (visited[chId].completed) {
                completedCount++;
            }
        });
        // Use completed chapter count as spoiler level
        maxLevel = completedCount;

        // Update notice
        var notice = document.getElementById('spoiler-notice');
        if (notice) {
            if (completedCount > 0) {
                notice.textContent = 'Showing details up to chapter ' + completedCount + ' (based on your reading progress).';
            } else {
                notice.textContent = 'No reading progress detected. Only spoiler-free content is shown.';
            }
        }

        // Apply spoiler gate
        var spoilerElements = document.querySelectorAll('[data-spoiler-level]');
        spoilerElements.forEach(function(el) {
            var level = parseInt(el.getAttribute('data-spoiler-level') || '0', 10);
            if (level > maxLevel) {
                el.classList.add('spoiler-hidden');
            }
        });
    }

    window.initSpoilerGate = initSpoilerGate;
})();
