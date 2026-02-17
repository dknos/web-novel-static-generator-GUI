"""Chapter editor with live markdown preview."""
import os
import sys
import yaml

# Add generator to path for importing convert_markdown_to_html
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generator'))


def load_chapter(story_slug, chapter_id, language='en'):
    """Load chapter content (front matter + markdown body).

    Returns:
        Tuple of (front_matter_str, markdown_body)
    """
    from panels import get_content_dir
    content_dir = get_content_dir()

    # Try language-specific first
    lang_path = os.path.join(content_dir, story_slug, 'chapters', language, f'{chapter_id}.md')
    default_path = os.path.join(content_dir, story_slug, 'chapters', f'{chapter_id}.md')

    filepath = lang_path if os.path.exists(lang_path) else default_path

    if not os.path.exists(filepath):
        return '', ''

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split front matter and body
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[1].strip(), parts[2].strip()

    return '', content


def save_chapter(story_slug, chapter_id, front_matter_str, markdown_body, language='en'):
    """Save chapter content."""
    from panels import get_content_dir
    content_dir = get_content_dir()

    # Determine save path
    lang_dir = os.path.join(content_dir, story_slug, 'chapters', language)
    default_dir = os.path.join(content_dir, story_slug, 'chapters')

    if language != 'en' and os.path.isdir(lang_dir):
        filepath = os.path.join(lang_dir, f'{chapter_id}.md')
    else:
        filepath = os.path.join(default_dir, f'{chapter_id}.md')

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    content = f'---\n{front_matter_str}\n---\n\n{markdown_body}'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


def preview_markdown(markdown_text):
    """Convert markdown to HTML for live preview.

    Returns:
        HTML string
    """
    try:
        from generate import convert_markdown_to_html
        return convert_markdown_to_html(markdown_text)
    except ImportError:
        # Fallback: basic markdown conversion
        import markdown
        return markdown.markdown(markdown_text, extensions=['footnotes', 'tables', 'attr_list'])
