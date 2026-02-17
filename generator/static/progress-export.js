// Reading progress export/import + Continue Reading widget
(function() {
    'use strict';

    // Gather all reading progress data from localStorage
    function gatherProgressData() {
        var data = { visited: {}, latest: {}, settings: {} };
        for (var i = 0; i < localStorage.length; i++) {
            var key = localStorage.key(i);
            if (key.startsWith('visited_')) {
                data.visited[key] = JSON.parse(localStorage.getItem(key));
            } else if (key.startsWith('latest_')) {
                data.latest[key] = JSON.parse(localStorage.getItem(key));
            } else if (key.startsWith('scroll_')) {
                if (!data.scrollPositions) data.scrollPositions = {};
                data.scrollPositions[key] = localStorage.getItem(key);
            }
        }
        // Reading settings
        var settingKeys = ['readingTextSize', 'readingLineSpacing', 'autoScrollToContent', 'readingMode', 'readingFontFamily', 'readingMaxWidth', 'autoAdvance'];
        settingKeys.forEach(function(k) {
            var v = localStorage.getItem(k);
            if (v !== null) data.settings[k] = v;
        });
        data.exportedAt = new Date().toISOString();
        data.version = 1;
        return data;
    }

    function exportProgress() {
        var data = gatherProgressData();
        var json = JSON.stringify(data, null, 2);
        var blob = new Blob([json], { type: 'application/json' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'reading-progress-' + new Date().toISOString().slice(0, 10) + '.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function importProgress() {
        var input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.addEventListener('change', function(e) {
            var file = e.target.files[0];
            if (!file) return;
            var reader = new FileReader();
            reader.onload = function(ev) {
                try {
                    var data = JSON.parse(ev.target.result);
                    mergeProgressData(data);
                    alert('Reading progress imported successfully! Refreshing page...');
                    location.reload();
                } catch (err) {
                    alert('Failed to import progress: Invalid file format.');
                }
            };
            reader.readAsText(file);
        });
        input.click();
    }

    function mergeProgressData(data) {
        // Merge visited chapters (keep newer timestamps)
        if (data.visited) {
            Object.keys(data.visited).forEach(function(key) {
                var existing = JSON.parse(localStorage.getItem(key) || '{}');
                var incoming = data.visited[key];
                Object.keys(incoming).forEach(function(chId) {
                    if (!existing[chId] || incoming[chId].visitedAt > existing[chId].visitedAt) {
                        existing[chId] = incoming[chId];
                    } else {
                        // Merge completed status (take true if either is true)
                        if (incoming[chId].completed && !existing[chId].completed) {
                            existing[chId].completed = true;
                            existing[chId].completedAt = incoming[chId].completedAt;
                        }
                    }
                });
                localStorage.setItem(key, JSON.stringify(existing));
            });
        }

        // Merge latest (keep newer)
        if (data.latest) {
            Object.keys(data.latest).forEach(function(key) {
                var existing = JSON.parse(localStorage.getItem(key) || 'null');
                var incoming = data.latest[key];
                if (!existing || (incoming.completedAt && (!existing.completedAt || incoming.completedAt > existing.completedAt))) {
                    localStorage.setItem(key, JSON.stringify(incoming));
                }
            });
        }

        // Merge scroll positions
        if (data.scrollPositions) {
            Object.keys(data.scrollPositions).forEach(function(key) {
                if (!localStorage.getItem(key)) {
                    localStorage.setItem(key, data.scrollPositions[key]);
                }
            });
        }

        // Merge settings (import overwrites)
        if (data.settings) {
            Object.keys(data.settings).forEach(function(key) {
                localStorage.setItem(key, data.settings[key]);
            });
        }
    }

    // Display Continue Reading widget on index page
    function displayContinueReading(novelDataList) {
        var container = document.getElementById('continue-reading-widget');
        if (!container) return;

        var cards = [];

        // Scan all latest_* keys
        for (var i = 0; i < localStorage.length; i++) {
            var key = localStorage.key(i);
            if (!key.startsWith('latest_')) continue;

            var novelSlug = key.replace('latest_', '');
            var latest = JSON.parse(localStorage.getItem(key));
            if (!latest) continue;

            // Find next unread chapter
            var visitedKey = 'visited_' + novelSlug;
            var visited = JSON.parse(localStorage.getItem(visitedKey) || '{}');

            // Find novel info from novelDataList
            var novelInfo = null;
            if (novelDataList) {
                for (var n = 0; n < novelDataList.length; n++) {
                    if (novelDataList[n].slug === novelSlug) {
                        novelInfo = novelDataList[n];
                        break;
                    }
                }
            }

            var novelTitle = novelInfo ? novelInfo.title : novelSlug;

            cards.push({
                novelSlug: novelSlug,
                novelTitle: novelTitle,
                lastChapterId: latest.chapterId,
                lastChapterTitle: latest.title,
                completedAt: latest.completedAt,
                totalRead: Object.keys(visited).length,
                totalCompleted: Object.keys(visited).filter(function(k) { return visited[k].completed; }).length
            });
        }

        if (cards.length === 0) {
            container.style.display = 'none';
            return;
        }

        // Sort by most recently read
        cards.sort(function(a, b) {
            return (b.completedAt || '').localeCompare(a.completedAt || '');
        });

        var html = '<h2>Continue Reading</h2><div class="continue-reading-cards">';
        cards.forEach(function(card) {
            var date = card.completedAt ? new Date(card.completedAt).toLocaleDateString() : '';
            html += '<div class="continue-reading-card">' +
                '<h3><a href="' + card.novelSlug + '/en/toc/">' + escapeHtml(card.novelTitle) + '</a></h3>' +
                '<p class="last-read">Last read: <a href="' + card.novelSlug + '/en/' + card.lastChapterId + '/">' + escapeHtml(card.lastChapterTitle) + '</a></p>' +
                (date ? '<p class="read-date">' + date + '</p>' : '') +
                '<p class="read-stats">' + card.totalCompleted + ' chapters completed</p>' +
                '</div>';
        });
        html += '</div>';
        container.innerHTML = html;
        container.style.display = 'block';
    }

    // Display Continue Reading on TOC page with next unread
    function displayTocContinueReading(novelSlug, allChapterIds) {
        var container = document.getElementById('toc-continue-reading');
        if (!container) return;

        var latestKey = 'latest_' + novelSlug;
        var latest = JSON.parse(localStorage.getItem(latestKey) || 'null');
        if (!latest) {
            container.style.display = 'none';
            return;
        }

        var visitedKey = 'visited_' + novelSlug;
        var visited = JSON.parse(localStorage.getItem(visitedKey) || '{}');

        // Find next unread
        var nextUnread = null;
        if (allChapterIds) {
            var latestIdx = allChapterIds.indexOf(latest.chapterId);
            if (latestIdx !== -1) {
                for (var i = latestIdx + 1; i < allChapterIds.length; i++) {
                    if (!visited[allChapterIds[i]] || !visited[allChapterIds[i]].completed) {
                        nextUnread = allChapterIds[i];
                        break;
                    }
                }
            }
        }

        var html = '<h3>Continue Reading</h3>' +
            '<p>Last completed: <a href="../' + latest.chapterId + '/">' + escapeHtml(latest.title) + '</a></p>';

        if (nextUnread) {
            html += '<p class="next-unread"><a href="../' + nextUnread + '/" class="next-unread-link">Next Unread Chapter &rarr;</a></p>';
        }

        var date = latest.completedAt ? new Date(latest.completedAt).toLocaleDateString() : '';
        if (date) {
            html += '<p class="completion-date">Finished on ' + date + '</p>';
        }

        container.innerHTML = html;
        container.style.display = 'block';
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // Expose to global scope
    window.exportProgress = exportProgress;
    window.importProgress = importProgress;
    window.displayContinueReading = displayContinueReading;
    window.displayTocContinueReading = displayTocContinueReading;
})();
