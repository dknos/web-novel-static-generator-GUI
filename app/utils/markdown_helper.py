"""Markdown rendering utilities for live preview."""

import markdown


_MD = markdown.Markdown(
    extensions=[
        "extra",       # tables, footnotes, abbreviations, attr_list, etc.
        "codehilite",  # code highlighting
        "toc",         # table of contents
        "meta",        # meta-data (front matter fallback)
        "sane_lists",  # better list handling
        "smarty",      # smart quotes
    ],
    extension_configs={
        "codehilite": {"guess_lang": False},
    },
)


def render_markdown(text: str) -> str:
    """Render markdown text to HTML fragment."""
    _MD.reset()
    return _MD.convert(text)


_LIGHT_CSS = """
  body {
    font-family: "Segoe UI", system-ui, sans-serif;
    line-height: 1.7;
    max-width: 800px;
    margin: 20px auto;
    padding: 0 20px;
    color: #222;
    background: #fff;
  }
  h1, h2, h3, h4 { margin-top: 1.4em; }
  code {
    background: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.9em;
  }
  pre {
    background: #f4f4f4;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
  }
  pre code { background: none; padding: 0; }
  blockquote {
    border-left: 4px solid #ddd;
    margin-left: 0;
    padding-left: 16px;
    color: #555;
  }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
  th { background: #f4f4f4; }
  img { max-width: 100%; height: auto; }
  a { color: #0066cc; }
"""

_DARK_CSS = """
  body {
    font-family: "Segoe UI", system-ui, sans-serif;
    line-height: 1.7;
    max-width: 800px;
    margin: 20px auto;
    padding: 0 20px;
    color: #d4d4d4;
    background: #1e1e1e;
  }
  h1, h2, h3, h4 { margin-top: 1.4em; color: #e0e0e0; }
  code {
    background: #2d2d2d;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.9em;
    color: #ce9178;
  }
  pre {
    background: #2d2d2d;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
  }
  pre code { background: none; padding: 0; color: #d4d4d4; }
  blockquote {
    border-left: 4px solid #555;
    margin-left: 0;
    padding-left: 16px;
    color: #999;
  }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #444; padding: 8px 12px; text-align: left; }
  th { background: #2d2d2d; }
  img { max-width: 100%; height: auto; }
  a { color: #569cd6; }
"""


def wrap_html(body_html: str, css: str = "", dark: bool = False) -> str:
    """Wrap an HTML body fragment in a full HTML document for QWebEngineView."""
    base_css = _DARK_CSS if dark else _LIGHT_CSS
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{base_css}
{css}
</style>
</head>
<body>
{body_html}
</body>
</html>"""
