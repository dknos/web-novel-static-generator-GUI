/* Local fallback implementation compatible with minimal lunr.js API used by search.js */
(function (global) {
  'use strict';

  function normalize(value) {
    return (value || '').toString().toLowerCase();
  }

  function createIndex() {
    return {
      _documents: [],
      _refField: 'id',
      _fields: [],
      ref: function (fieldName) {
        this._refField = fieldName;
      },
      field: function (fieldName) {
        this._fields.push(fieldName);
      },
      add: function (doc) {
        this._documents.push(doc || {});
      },
      search: function (query) {
        var q = normalize(query).replace(/\*/g, '').trim();
        if (!q) return [];
        var terms = q.split(/\s+/).filter(Boolean);
        var scored = [];
        for (var i = 0; i < this._documents.length; i++) {
          var doc = this._documents[i];
          var haystackParts = [];
          for (var j = 0; j < this._fields.length; j++) {
            haystackParts.push(normalize(doc[this._fields[j]]));
          }
          var haystack = haystackParts.join(' ');
          var score = 0;
          for (var k = 0; k < terms.length; k++) {
            if (haystack.indexOf(terms[k]) !== -1) score += 1;
          }
          if (score > 0) {
            scored.push({ ref: doc[this._refField], score: score });
          }
        }
        scored.sort(function (a, b) { return b.score - a.score; });
        return scored;
      }
    };
  }

  global.lunr = function (builderFn) {
    var index = createIndex();
    if (typeof builderFn === 'function') {
      builderFn.call(index);
    }
    return index;
  };
})(window);
