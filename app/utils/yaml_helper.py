"""YAML parsing and writing utilities."""

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write a dict to a YAML file, preserving readability."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown file into YAML front matter dict and body content.

    Returns (front_matter_dict, markdown_body).  If no front matter is
    present, front_matter_dict will be an empty dict.
    """
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    fm_raw = parts[1]
    body = parts[2].lstrip("\n")
    fm = yaml.safe_load(fm_raw)
    if not isinstance(fm, dict):
        fm = {}
    return fm, body


def build_front_matter(front_matter: dict[str, Any], body: str) -> str:
    """Combine a front matter dict and markdown body into a single string."""
    fm_str = yaml.dump(
        front_matter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    ).rstrip("\n")
    return f"---\n{fm_str}\n---\n\n{body}"
