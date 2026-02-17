# Changelog


## [2.0.1] - 2026-02-17

### Improvements
- Added optional incremental build mode (`--incremental`) with build input fingerprint caching to skip no-op rebuilds.
- Added local search engine script (`static/lunr.min.js`) and search boot checks to avoid CDN/runtime failures.
- Added optional Gradio Studio auth guardrails via `--require-auth` and `WNSG_STUDIO_USER`/`WNSG_STUDIO_PASSWORD`.
- Added initial automated tests (`pytest`) and GitHub Actions CI workflow with generator smoke check.

## [2.0.0] - 2026-02-16

Major feature release adding 13 new features across reader UX, collaboration tooling, and content management, plus infrastructure improvements and standalone launchers.

### Infrastructure

#### JS Module Extraction (Phase 0A)
- **Extracted ~700 lines of inline JavaScript** from `chapter.html` into 5 standalone static files:
  - `reading-settings.js` — text size, line spacing, auto-scroll persistence
  - `reading-progress.js` — visited/completed chapter tracking, scroll-based completion detection
  - `keyboard-nav.js` — keyboard shortcuts (arrows, h/j/k/l, g/G, t, +/-, ?, 0) and help modal
  - `chapter-nav.js` — chapter dropdown jump, scroll position save/restore
  - `password-unlock.js` — password-protected chapter decryption (reads data attributes instead of inline template vars)
- Chapter template now uses a small inline init script that passes Jinja2 variables as function parameters
- Manga reader JS remains inline due to heavy Jinja2 coupling (14+ template expressions)
- All new JS files are cache-busted via the existing `copy_static_assets()` pipeline

#### Build Module System (Phase 0B)
- Created `generator/modules/` package for new build-time features
- Keeps `generate.py` from growing beyond maintainability limits

---

### New Features

#### Feature 1: Full-Text Search
- **New files:** `modules/search.py`, `static/search.js`, `templates/search.html`
- Client-side full-text search using [lunr.js](https://lunrjs.com/) (loaded via CDN)
- Build-time `generate_search_index()` iterates all novels/languages/chapters, extracts title, tags, and a 2,000-character text excerpt into `search_index.json`
- Skips drafts, password-protected, and hidden chapters
- Search page with story and language filter dropdowns
- Result cards show title, story, tags, and highlighted excerpt snippet
- Search link added to index page navigation

#### Feature 2: Reading Modes (Typewriter / Focus / Paged)
- **New file:** `static/reading-modes.js` (295 lines)
- Four reading modes selectable from the chapter settings panel:
  - **Normal** — default reading experience
  - **Typewriter** — IntersectionObserver tracks the paragraph nearest viewport center, dims all others to `opacity: 0.3` for focused reading
  - **Focus** — hides navigation, comments, metadata, and footer; shows a floating exit button
  - **Paged** — CSS columns-based pagination with page-turn controls (click left/right regions, keyboard arrows, swipe on touch devices)
- Mode persists via `localStorage` key `readingMode`
- Full dark mode support for all modes

#### Feature 3: Sticky "Continue Reading" + Progress Export/Import
- **New file:** `static/progress-export.js` (241 lines)
- **Index page:** "Continue Reading" widget scans `localStorage` for `latest_*` keys and shows cards linking to the last-read chapter per story
- **TOC page:** "Continue Reading" section with next-unread chapter detection
- **Export:** Downloads all reading progress (`visited_*`, `latest_*`) as a JSON file
- **Import:** Uploads a JSON file and merges progress with existing data
- Buttons added to index page footer

#### Feature 4: Better Chapter Navigation
- **Extended:** `static/chapter-nav.js`
- **Scroll position save/restore:** Saves scroll percentage to `localStorage` key `scroll_{novelSlug}_{chapterId}`, restores on page load
- **"Next Unread" button:** Scans `visited_*` keys to find the first non-completed chapter after the current one
- **Auto-advance:** When chapter completion is detected (scroll to bottom), optionally waits 2 seconds then navigates to next chapter. Toggle in reading settings panel. Persists via `localStorage` key `autoAdvance`

#### Feature 5: Tag UX Upgrade
- **TOC page:** Tag chips displayed next to each chapter title
- **Tags index page:** Added search/filter input that filters tag cards as you type
- **Chapter page:** "Related Chapters" section after content, showing top 3-5 chapters ranked by shared tag count
- **New function in generate.py:** `find_related_chapters()` computes tag overlap across all chapters in a novel
- Tags attached to enhanced chapter objects in `filter_hidden_chapters_from_novel()`

#### Feature 6: Gradio Collaboration Studio
- **New files:** `gradio_studio.py`, `studio/panels.py`, `studio/editor.py`, `studio/builder.py`
- Web-based collaboration tool with 6 tabs:
  - **Stories & Chapters** — browseable lists with status filters (ongoing/complete/hiatus, draft/review/scheduled/published)
  - **Chapter Editor** — load/edit/save chapters with YAML front matter editor, markdown body editor, and live HTML preview (uses the same `convert_markdown_to_html` as the generator)
  - **Configuration** — edit `site_config.yaml` and per-story `config.yaml` as raw YAML
  - **Authors** — edit `authors.yaml`
  - **Build & Preview** — one-click build with all generator flags (clean, include-drafts, include-scheduled, no-epub, optimize-images, no-minify) + start/stop preview server
  - **Assets** — browse and upload images per story
- Launch: `python gradio_studio.py [--port PORT] [--share]`

#### Feature 7: Role-Based Chapter Metadata
- **New front matter fields:** `status` (draft/review/approved/scheduled/published), `contributors` (list of name + role), `reviewers` (list of names)
- `should_skip_chapter()` now respects the `status` field alongside the existing `draft` boolean
- Chapter template displays contributor badges (color-coded by role: author, translator, editor, proofreader) and status badges
- **PySide6 desktop app updated:**
  - `app/models/chapter.py` — added `status`, `contributors`, `reviewers` properties
  - `app/widgets/chapter_editor.py` — added status dropdown, reviewers text field, and YAML contributors textarea to the front matter form

#### Feature 10: Better Typography + Layout System
- **New story config fields:** `typography.font_family`, `typography.font_size`, `typography.line_height`, `typography.max_width`
- Chapter template applies story-level typography as CSS custom properties (`--reading-font-family`, `--reading-max-width`)
- Reading settings panel extended with:
  - Font family selector (serif, sans-serif, monospace, system)
  - Max width slider (500–1000px)
- User overrides persist via `localStorage` keys `readingFontFamily`, `readingMaxWidth`
- CSS supports ruby text (`<ruby>`, `<rt>`) and optional `.vertical-text` class

#### Feature 11: Footnotes/Endnotes Enhancement
- **New file:** `static/footnote-preview.js` (139 lines)
- **Desktop:** Hovering over a footnote reference shows an inline tooltip with the footnote content
- **Mobile:** Tapping a footnote reference shows a modal overlay
- Clones footnote content and strips backref links for clean display
- Works with the existing markdown `footnotes` extension output

#### Feature 12: Glossary / Terms Pages
- **New files:** `modules/glossary.py`, `templates/glossary.html`, `static/glossary-links.js`
- **Per-story glossary:** Define terms in `content/{story}/glossary.yaml` (or `glossary-{lang}.yaml` for translations)
- **Glossary YAML format:**
  ```yaml
  terms:
    - term: "Eldoria"
      definition: "The ancient golden city"
      aliases: ["Golden City"]
      first_appearance: "chapter-1"
      category: "location"
  ```
- **Story config:** `glossary.enabled`, `glossary.auto_link`, `glossary.show_in_navigation`
- **Auto-linking:** When enabled, BeautifulSoup post-processes chapter HTML to wrap first occurrence of each term with a tooltip `<span>` (skips headings, code, links)
- **Glossary page:** Term cards grouped by category with search filter and language switcher
- **Inline tooltips:** Hover/focus on linked terms shows definition tooltip in chapters
- Navigation link added to TOC when enabled

#### Feature 13: Character / Location Index Pages
- **New files:** `modules/characters.py`, `templates/characters.html`, `templates/character_detail.html`, `static/spoiler-gate.js`
- **Per-story characters:** Define in `content/{story}/characters.yaml`
- **Characters YAML format:**
  ```yaml
  characters:
    - name: "Aria"
      slug: "aria"
      description: "A young scribe"
      image: "characters/aria.jpg"
      spoiler_level: 0
      details:
        - chapter: "chapter-1"
          spoiler_level: 0
          text: "Discovers the prophecy scroll"
        - chapter: "chapter-3"
          spoiler_level: 3
          text: "Reveals hidden ancestry"
      tags: ["protagonist"]
  ```
- **Spoiler gate:** Client-side JS reads `visited_*` from `localStorage`, counts completed chapters, and hides character details with `data-spoiler-level` higher than the reader's progress
- **Character index:** Grid layout with portrait cards, filterable by tag
- **Character detail pages:** Individual pages with portrait, description, and timeline of appearances (spoiler-gated)
- Navigation link added to TOC

---

### Standalone Launchers
- `Start App.bat` — double-click to launch the PySide6 desktop app
- `Start Studio.bat` — double-click to launch the Gradio studio
- `launcher.py` + `build_exe.bat` — compile `Web Novel App.exe` (auto-installs dependencies on first run, then launches desktop app)
- `launcher_studio.py` + `build_exe_studio.bat` — compile `Web Novel Studio.exe` (auto-installs dependencies including Gradio, launches studio and opens browser)

---

### CSS Additions (~400 lines)
- Continue reading widget, progress export/import buttons
- Tag chips, tag filter input
- Related chapters section
- Footnote tooltip and mobile modal
- Contributor badges (color-coded by role), status badges (color-coded by status)
- Typography controls (font family selector, max width slider)
- Ruby text and vertical text support
- Search page, result cards, filter UI
- Glossary page, term cards, inline tooltips
- Character cards/grid, character detail page
- Spoiler gate notice and hidden content
- Reading modes (typewriter dimming, focus mode overlay, paged columns)
- Full dark mode support for all new components
- Responsive breakpoints for mobile

---

### Modified Files Summary
| File | Changes |
|---|---|
| `generator/generate.py` | Cache-bust list, `find_related_chapters()`, `should_skip_chapter()` status support, tags in enhanced chapters, related chapters + all_chapter_ids + typography in render calls, glossary auto-linking, glossary/character/search page generation |
| `generator/templates/chapter.html` | Script extraction, init script, reading mode/font/width/auto-advance controls, contributor/status badges, related chapters, footnote/glossary/reading-mode scripts |
| `generator/templates/index.html` | Continue reading widget, search nav link, export/import buttons, progress-export.js |
| `generator/templates/toc.html` | Tag chips, continue reading section, glossary/characters nav links, allChapterIds |
| `generator/templates/tags_index.html` | Search/filter input |
| `generator/static/style.css` | ~400 lines of new styles |
| `requirements.txt` | Added `gradio>=4.0.0` |
| `app/models/chapter.py` | `status`, `contributors`, `reviewers` properties |
| `app/widgets/chapter_editor.py` | Status dropdown, reviewers field, contributors textarea |

### New Files Summary (30 files, ~3,570 lines)
- 11 JavaScript files in `generator/static/`
- 4 Python modules in `generator/modules/`
- 4 Jinja2 templates in `generator/templates/`
- 5 studio/Gradio files
- 2 launcher Python scripts
- 4 batch files
