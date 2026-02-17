"""Search index generation module.

Generates a JSON search index of all published chapters for client-side full-text search.
"""
import os
import json
import re
from html import unescape


def strip_html(html_text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def generate_search_index(all_novels_data, content_dir, load_chapter_content_fn,
                          should_skip_fn, convert_md_fn,
                          include_drafts=False, include_scheduled=False,
                          max_excerpt_chars=2000):
    """Generate search_index.json for client-side search.

    Args:
        all_novels_data: List of novel data dicts (with slug, title, arcs, etc.)
        content_dir: Path to content directory
        load_chapter_content_fn: Function(novel_slug, chapter_id, lang) -> (md, metadata)
        should_skip_fn: Function(metadata, include_drafts, include_scheduled) -> bool
        convert_md_fn: Function(markdown_str) -> html_str
        include_drafts: Whether to include draft chapters
        include_scheduled: Whether to include scheduled chapters
        max_excerpt_chars: Max characters for text excerpt

    Returns:
        List of search index entries (dicts)
    """
    index = []

    for novel in all_novels_data:
        novel_slug = novel.get('slug', '')
        novel_title = novel.get('title', '')
        primary_lang = novel.get('primary_language', 'en')

        # Determine available languages
        languages = [primary_lang]
        lang_config = novel.get('languages', {})
        if isinstance(lang_config, dict):
            for lang in lang_config:
                if lang != primary_lang:
                    languages.append(lang)

        all_chapters = []
        for arc in novel.get('arcs', []):
            all_chapters.extend(arc.get('chapters', []))

        for chapter in all_chapters:
            chapter_id = chapter.get('id', '')

            for lang in languages:
                try:
                    md_content, metadata = load_chapter_content_fn(novel_slug, chapter_id, lang)
                except Exception:
                    continue

                if should_skip_fn(metadata, include_drafts, include_scheduled):
                    continue

                # Skip password-protected chapters
                if metadata.get('password'):
                    continue

                # Skip hidden chapters
                if metadata.get('hidden'):
                    continue

                chapter_title = metadata.get('title', chapter.get('title', chapter_id))
                tags = metadata.get('tags', []) or []
                published = str(metadata.get('published', ''))

                # Convert markdown to HTML, then strip to plain text
                try:
                    html_content = convert_md_fn(md_content)
                    text_content = strip_html(html_content)
                except Exception:
                    text_content = strip_html(md_content)

                # Truncate excerpt
                excerpt = text_content[:max_excerpt_chars]

                entry = {
                    'id': f'{novel_slug}/{lang}/{chapter_id}',
                    'title': chapter_title,
                    'story': novel_title,
                    'storySlug': novel_slug,
                    'language': lang,
                    'tags': tags,
                    'published': published,
                    'url': f'{novel_slug}/{lang}/{chapter_id}/',
                    'text': excerpt,
                }

                index.append(entry)

    return index
