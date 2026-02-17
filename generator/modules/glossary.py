"""Glossary module for loading glossary data and auto-linking terms in chapter HTML."""
import os
import re
import yaml
from bs4 import BeautifulSoup


def load_glossary(novel_slug, content_dir, language='en'):
    """Load glossary data from per-story YAML file.

    Looks for:
      1. content/{novel_slug}/glossary-{language}.yaml
      2. content/{novel_slug}/glossary.yaml

    Returns:
        dict with 'terms' list, or None if no glossary file found
    """
    # Try language-specific first
    lang_path = os.path.join(content_dir, novel_slug, f'glossary-{language}.yaml')
    default_path = os.path.join(content_dir, novel_slug, 'glossary.yaml')

    glossary_path = None
    if os.path.exists(lang_path):
        glossary_path = lang_path
    elif os.path.exists(default_path):
        glossary_path = default_path

    if not glossary_path:
        return None

    with open(glossary_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data


def auto_link_terms(html_content, glossary_data):
    """Post-process HTML to wrap matching glossary terms with tooltip spans.

    Args:
        html_content: HTML string of chapter content
        glossary_data: Glossary dict with 'terms' list

    Returns:
        Modified HTML string with terms wrapped in <span class="glossary-linked-term">
    """
    if not glossary_data or not glossary_data.get('terms'):
        return html_content

    soup = BeautifulSoup(html_content, 'html.parser')

    # Build lookup: term -> definition (including aliases)
    term_lookup = {}
    for term_entry in glossary_data['terms']:
        term = term_entry.get('term', '')
        definition = term_entry.get('definition', '')
        if term:
            term_lookup[term.lower()] = {'term': term, 'definition': definition}
        for alias in term_entry.get('aliases', []):
            if alias:
                term_lookup[alias.lower()] = {'term': term, 'definition': definition}

    if not term_lookup:
        return html_content

    # Sort by length descending to match longer terms first
    sorted_terms = sorted(term_lookup.keys(), key=len, reverse=True)

    # Build regex pattern
    escaped = [re.escape(t) for t in sorted_terms]
    pattern = re.compile(r'\b(' + '|'.join(escaped) + r')\b', re.IGNORECASE)

    # Track which terms have been linked (only link first occurrence)
    linked_terms = set()

    # Process text nodes in <p>, <li>, <td> elements (skip headings, code, etc.)
    for element in soup.find_all(['p', 'li', 'td', 'dd']):
        for text_node in element.find_all(string=True):
            # Skip if inside a link, code, or already glossary-linked
            parent = text_node.parent
            if parent.name in ('a', 'code', 'pre', 'script', 'style', 'span'):
                if parent.get('class') and 'glossary-linked-term' in parent.get('class', []):
                    continue
                if parent.name in ('a', 'code', 'pre', 'script', 'style'):
                    continue

            original = str(text_node)
            modified = original

            def replace_term(match):
                matched_text = match.group(0)
                key = matched_text.lower()
                if key in linked_terms:
                    return matched_text
                if key not in term_lookup:
                    return matched_text
                linked_terms.add(key)
                info = term_lookup[key]
                escaped_def = info['definition'].replace('"', '&quot;').replace("'", '&#39;')
                return (f'<span class="glossary-linked-term" '
                        f'data-term="{info["term"]}" '
                        f'data-definition="{escaped_def}">'
                        f'{matched_text}</span>')

            modified = pattern.sub(replace_term, modified)

            if modified != original:
                new_content = BeautifulSoup(modified, 'html.parser')
                text_node.replace_with(new_content)

    return str(soup)


def group_terms_by_category(glossary_data):
    """Group glossary terms by category for display.

    Returns:
        OrderedDict of category -> list of term entries
    """
    if not glossary_data or not glossary_data.get('terms'):
        return {}

    groups = {}
    for term in glossary_data['terms']:
        category = term.get('category', 'general')
        if category not in groups:
            groups[category] = []
        groups[category].append(term)

    # Sort each group by term name
    for category in groups:
        groups[category].sort(key=lambda t: t.get('term', '').lower())

    return groups
