---
title: "Chapter 1: The Beginning"
author: original-author
published: 2025-01-01
tags:
  - introduction
  - world-building
---

# The Beginning

This is an example chapter to demonstrate the web novel static site generator.

## Getting Started

Edit this file or create new `.md` files in the `chapters/` directory to add your own content. Each chapter needs YAML front matter (between the `---` markers) with at least a `title` and `published` date.

### Features you can use

- **Markdown formatting** — bold, italic, links, images, code blocks
- **Footnotes** — add references with `[^1]` syntax[^1]
- **Tags** — categorize chapters for discovery
- **Password protection** — add `password: "secret"` to front matter
- **Draft mode** — add `draft: true` to hide from published site
- **Translation notes** — add `translation_notes: "..."` for translator context

### Front matter options

```yaml
title: "Chapter Title"
author: author-key
translator: translator-key
published: 2025-01-01
tags: [tag1, tag2]
draft: false
status: published  # draft, review, approved, scheduled, published
password: ""
password_hint: ""
contributors:
  - name: "Author Name"
    role: author
  - name: "Editor Name"
    role: editor
reviewers: ["editor-key"]
```

Happy writing!

[^1]: This is an example footnote. Hover over the reference number to see a preview.
