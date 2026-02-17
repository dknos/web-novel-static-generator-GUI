// Full-text search using lunr.js
(function() {
    'use strict';

    var searchIndex = null;
    var lunrIndex = null;
    var searchData = null;

    function isSearchEngineAvailable() {
        return typeof lunr === 'function';
    }

    function loadSearchIndex() {
        var resultsEl = document.getElementById('search-results');
        if (!resultsEl) return;

        if (!isSearchEngineAvailable()) {
            resultsEl.innerHTML = '<p class="search-loading">Search engine failed to load. Ensure <code>lunr.min.js</code> is available in <code>/static/</code>.</p>';
            return;
        }

        resultsEl.innerHTML = '<p class="search-loading">Loading search index...</p>';

        fetch('../search_index.json')
            .then(function(res) { return res.json(); })
            .then(function(data) {
                searchData = data;
                buildLunrIndex(data);
                resultsEl.innerHTML = '';
                // Check if there's a query param
                var urlParams = new URLSearchParams(window.location.search);
                var q = urlParams.get('q');
                if (q) {
                    document.getElementById('search-input').value = q;
                    performSearch(q);
                }
            })
            .catch(function(err) {
                resultsEl.innerHTML = '<p>Failed to load search index.</p>';
            });
    }

    function buildLunrIndex(data) {
        lunrIndex = lunr(function() {
            this.ref('id');
            this.field('title', { boost: 10 });
            this.field('tags', { boost: 5 });
            this.field('story', { boost: 3 });
            this.field('text');

            var self = this;
            data.forEach(function(doc) {
                self.add({
                    id: doc.id,
                    title: doc.title,
                    tags: (doc.tags || []).join(' '),
                    story: doc.story,
                    text: doc.text
                });
            });
        });
    }

    function performSearch(query) {
        if (!lunrIndex || !searchData || !query.trim()) {
            renderResults([]);
            return;
        }

        var results;
        try {
            results = lunrIndex.search(query);
        } catch (e) {
            // Fallback: try wrapping in wildcards
            try {
                results = lunrIndex.search('*' + query + '*');
            } catch (e2) {
                results = [];
            }
        }

        // Get filters
        var storyFilter = document.getElementById('filter-story');
        var langFilter = document.getElementById('filter-language');
        var selectedStory = storyFilter ? storyFilter.value : '';
        var selectedLang = langFilter ? langFilter.value : '';

        // Map results to data
        var mapped = [];
        results.forEach(function(result) {
            var doc = searchData.find(function(d) { return d.id === result.ref; });
            if (!doc) return;
            if (selectedStory && doc.storySlug !== selectedStory) return;
            if (selectedLang && doc.language !== selectedLang) return;
            mapped.push({ doc: doc, score: result.score });
        });

        renderResults(mapped, query);
    }

    function highlightText(text, query) {
        if (!query) return text;
        var words = query.split(/\s+/).filter(function(w) { return w.length > 1; });
        var escaped = words.map(function(w) { return w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); });
        if (escaped.length === 0) return text;
        var regex = new RegExp('(' + escaped.join('|') + ')', 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    function getExcerptAroundQuery(text, query, contextChars) {
        contextChars = contextChars || 200;
        if (!query || !text) return text.substring(0, 300);
        var words = query.split(/\s+/).filter(function(w) { return w.length > 1; });
        var lowerText = text.toLowerCase();
        var bestPos = -1;

        for (var i = 0; i < words.length; i++) {
            var pos = lowerText.indexOf(words[i].toLowerCase());
            if (pos !== -1) {
                bestPos = pos;
                break;
            }
        }

        if (bestPos === -1) return text.substring(0, 300);

        var start = Math.max(0, bestPos - contextChars);
        var end = Math.min(text.length, bestPos + contextChars);
        var excerpt = text.substring(start, end);

        if (start > 0) excerpt = '...' + excerpt;
        if (end < text.length) excerpt = excerpt + '...';
        return excerpt;
    }

    function renderResults(results, query) {
        var container = document.getElementById('search-results');
        if (!container) return;

        if (results.length === 0) {
            if (query) {
                container.innerHTML = '<p class="search-result-count">No results found.</p>';
            } else {
                container.innerHTML = '';
            }
            return;
        }

        var html = '<p class="search-result-count">' + results.length + ' result' + (results.length !== 1 ? 's' : '') + ' found</p>';
        results.forEach(function(item) {
            var doc = item.doc;
            var excerpt = getExcerptAroundQuery(doc.text || '', query);
            excerpt = highlightText(excerpt, query);
            var titleHtml = highlightText(escapeHtml(doc.title), query);

            html += '<div class="search-result-card">' +
                '<div class="search-result-title"><a href="../' + doc.url + '">' + titleHtml + '</a></div>' +
                '<div class="search-result-meta">' + escapeHtml(doc.story) + ' &middot; ' + doc.language.toUpperCase();
            if (doc.published) html += ' &middot; ' + escapeHtml(doc.published);
            html += '</div>';
            if (doc.tags && doc.tags.length > 0) {
                html += '<div class="search-result-meta">';
                doc.tags.forEach(function(t) { html += '<span class="tag tag-small">' + escapeHtml(t) + '</span> '; });
                html += '</div>';
            }
            html += '<div class="search-result-excerpt">' + excerpt + '</div>' +
                '</div>';
        });

        container.innerHTML = html;
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function initSearch() {
        var input = document.getElementById('search-input');
        if (!input) return;

        var debounceTimer;
        input.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                performSearch(input.value);
            }, 200);
        });

        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch(input.value);
            }
        });

        // Filter change handlers
        var storyFilter = document.getElementById('filter-story');
        var langFilter = document.getElementById('filter-language');
        if (storyFilter) storyFilter.addEventListener('change', function() { performSearch(input.value); });
        if (langFilter) langFilter.addEventListener('change', function() { performSearch(input.value); });

        loadSearchIndex();
    }

    document.addEventListener('DOMContentLoaded', initSearch);
})();
