# Web Novel Static Site Generator (Extended Fork)

> Fork of [Oekaki-Connect/web-novel-static-generator](https://github.com/Oekaki-Connect/web-novel-static-generator) with 13 new features, a Gradio collaboration studio, and standalone Windows launchers.

A Python-based static website generator designed for hosting serialized web fiction, with a PySide6 desktop editor and a new Gradio web-based collaboration studio.

---

## What's New in This Fork

### Reader Experience
- **Full-Text Search** — Client-side search powered by lunr.js with story/language filters and highlighted excerpts
- **Reading Modes** — Typewriter (focused paragraph), Focus (distraction-free), and Paged (book-like pagination) modes
- **Continue Reading + Progress Export/Import** — Smart "continue where you left off" widgets on the homepage and TOC, plus JSON export/import of all reading progress
- **Better Chapter Navigation** — Scroll position memory, "next unread" chapter button, and optional auto-advance to the next chapter on completion
- **Tag UX Upgrade** — Tag chips on TOC, filterable tag index, and "Related Chapters" recommendations based on shared tags
- **Footnote Previews** — Hover tooltips on desktop, tap modals on mobile for inline footnote reading
- **Typography Controls** — Per-story font family, max width, and sizing defaults with reader-adjustable overrides

### Content Management
- **Glossary System** — Per-story YAML-defined glossaries with auto-linked terms in chapters, hover tooltips, and dedicated glossary pages
- **Character/Location Index** — YAML-defined character profiles with spoiler-gated details that reveal based on the reader's progress
- **Role-Based Metadata** — Chapter workflow status (draft/review/approved/scheduled/published), contributor roles (author/translator/editor/proofreader), and reviewer assignments

### Collaboration
- **Gradio Web Studio** — Browser-based collaboration tool with story/chapter browsing, a live-preview markdown editor, YAML config editors, asset management, and one-click builds
- **Standalone Launchers** — `.exe` builders for both the desktop app and Gradio studio with automatic dependency installation

---

## Quick Start

### Desktop App
```
pip install -r requirements.txt
python main.py
```
Or double-click `Start App.bat` / build `Web Novel App.exe` via `build_exe.bat`.

### Gradio Studio
```
pip install -r requirements.txt
python gradio_studio.py
```
Or double-click `Start Studio.bat` / build `Web Novel Studio.exe` via `build_exe_studio.bat`.

### Generate Site
```
cd generator
python generate.py [--clean] [--include-drafts] [--include-scheduled] [--no-epub] [--optimize-images] [--no-minify] [--serve PORT]
```

---

## New Content Formats

### Glossary (`content/{story}/glossary.yaml`)
```yaml
terms:
  - term: "Eldoria"
    definition: "The ancient golden city"
    aliases: ["Golden City"]
    first_appearance: "chapter-1"
    category: "location"
```
Enable in story config:
```yaml
glossary:
  enabled: true
  auto_link: true
  show_in_navigation: true
```

### Characters (`content/{story}/characters.yaml`)
```yaml
characters:
  - name: "Aria"
    slug: "aria"
    description: "A young scribe from Eldoria"
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

### Typography (`content/{story}/config.yaml`)
```yaml
typography:
  font_family: "Georgia, serif"
  font_size: 18
  line_height: 1.8
  max_width: 700
```

### Role-Based Metadata (chapter front matter)
```yaml
status: review
contributors:
  - name: "Author Name"
    role: author
  - name: "Editor Name"
    role: editor
reviewers: ["editor-sama"]
```

---

## Architecture

| Component | Description |
|---|---|
| `generator/generate.py` | Static site generator (~6,200 lines) |
| `generator/modules/` | Build-time feature modules (search index, glossary auto-linking, character pages) |
| `generator/templates/` | 15 Jinja2 templates |
| `generator/static/` | CSS + 12 vanilla JS modules (no frameworks, no npm) |
| `app/` | PySide6 desktop IDE |
| `studio/` | Gradio web studio backend |
| `gradio_studio.py` | Gradio studio entry point |

---

## Technology Stack

- **Python 3.11+**, PySide6, Jinja2, PyYAML, markdown, ebooklib, BeautifulSoup4, Pillow
- **Gradio 4+** (optional, for web studio)
- **Frontend:** Vanilla JavaScript, CSS custom properties, localStorage for state
- **Search:** lunr.js (CDN)
- **No npm/node.js required**

---

## All Upstream Features Preserved

Multi-novel support, multi-language translations, EPUB generation, arc organization, dark/light theme, RSS feeds, sitemap, password-protected chapters, reading progress tracking, keyboard navigation, manga reader, Utterances comments, Open Graph/Twitter Cards, SEO controls, draft/scheduled chapters, GitHub Actions deployment, and more.

See [CHANGELOG.md](CHANGELOG.md) for the full detailed changelog.

---

## License

Same as upstream. See [LICENSE](LICENSE).
