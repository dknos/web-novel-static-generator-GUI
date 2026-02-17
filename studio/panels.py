"""Panels for story listing and chapter management."""
import os
import yaml


def get_content_dir():
    """Get the content directory path."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generator', 'content')


def get_generator_dir():
    """Get the generator directory path."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generator')


def list_stories():
    """List all stories with their config data.

    Returns:
        List of dicts with slug, title, status, description
    """
    content_dir = get_content_dir()
    stories = []

    if not os.path.exists(content_dir):
        return stories

    for slug in sorted(os.listdir(content_dir)):
        config_path = os.path.join(content_dir, slug, 'config.yaml')
        if os.path.isfile(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            stories.append({
                'slug': slug,
                'title': config.get('title', slug),
                'status': config.get('status', 'unknown'),
                'description': config.get('description', ''),
            })

    return stories


def list_chapters(story_slug, language='en'):
    """List all chapters for a story.

    Returns:
        List of dicts with id, title, status, published, tags
    """
    content_dir = get_content_dir()
    chapters_dir = os.path.join(content_dir, story_slug, 'chapters')

    # Check language-specific directory first
    lang_dir = os.path.join(chapters_dir, language)
    search_dir = lang_dir if os.path.isdir(lang_dir) else chapters_dir

    chapters = []
    if not os.path.isdir(search_dir):
        return chapters

    for fname in sorted(os.listdir(search_dir)):
        if not fname.endswith('.md'):
            continue
        chapter_id = fname[:-3]
        filepath = os.path.join(search_dir, fname)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse front matter
        metadata = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    pass

        chapters.append({
            'id': chapter_id,
            'title': metadata.get('title', chapter_id),
            'status': metadata.get('status', metadata.get('draft', False) and 'draft' or 'published'),
            'published': str(metadata.get('published', '')),
            'tags': metadata.get('tags', []) or [],
        })

    return chapters


def load_site_config():
    """Load the site config."""
    config_path = os.path.join(get_generator_dir(), 'site_config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def save_site_config(config_data):
    """Save the site config."""
    config_path = os.path.join(get_generator_dir(), 'site_config.yaml')
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)


def load_story_config(story_slug):
    """Load a story config."""
    config_path = os.path.join(get_content_dir(), story_slug, 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def save_story_config(story_slug, config_data):
    """Save a story config."""
    config_path = os.path.join(get_content_dir(), story_slug, 'config.yaml')
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)


def load_authors_config():
    """Load the authors config."""
    config_path = os.path.join(get_generator_dir(), 'authors.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def save_authors_config(config_data):
    """Save the authors config."""
    config_path = os.path.join(get_generator_dir(), 'authors.yaml')
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
