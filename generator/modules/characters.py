"""Character/Location index module for loading YAML data and generating index pages."""
import os
import yaml


def load_characters(novel_slug, content_dir):
    """Load characters data from per-story YAML file.

    Looks for content/{novel_slug}/characters.yaml

    Returns:
        dict with 'characters' list, or None
    """
    chars_path = os.path.join(content_dir, novel_slug, 'characters.yaml')
    if not os.path.exists(chars_path):
        return None

    with open(chars_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data


def filter_by_spoiler_level(characters_data, max_level=None):
    """Filter character details by spoiler level.

    If max_level is None, returns all characters with all details.
    Otherwise, filters details to only show entries with spoiler_level <= max_level.

    Args:
        characters_data: dict with 'characters' list
        max_level: Maximum spoiler level to show (None for all)

    Returns:
        Filtered characters data
    """
    if not characters_data or not characters_data.get('characters'):
        return characters_data

    if max_level is None:
        return characters_data

    filtered = []
    for char in characters_data['characters']:
        if char.get('spoiler_level', 0) > max_level:
            continue

        filtered_char = dict(char)
        if 'details' in filtered_char:
            filtered_char['details'] = [
                d for d in filtered_char['details']
                if d.get('spoiler_level', 0) <= max_level
            ]
        filtered.append(filtered_char)

    return {'characters': filtered}


def group_by_tags(characters_data):
    """Group characters by their tags.

    Returns:
        dict of tag -> list of characters
    """
    if not characters_data or not characters_data.get('characters'):
        return {}

    groups = {}
    for char in characters_data['characters']:
        tags = char.get('tags', [])
        if not tags:
            tags = ['other']
        for tag in tags:
            if tag not in groups:
                groups[tag] = []
            groups[tag].append(char)

    return groups
