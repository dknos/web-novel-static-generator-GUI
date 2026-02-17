"""File I/O service — read/write YAML and markdown files."""

from pathlib import Path
from typing import Any

from app.utils.yaml_helper import load_yaml, save_yaml, parse_front_matter, build_front_matter


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_yaml(path: Path) -> dict[str, Any]:
    return load_yaml(path)


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    save_yaml(path, data)


def read_chapter(path: Path) -> tuple[dict[str, Any], str]:
    """Read a chapter file and return (front_matter, body)."""
    return parse_front_matter(read_text(path))


def write_chapter(path: Path, front_matter: dict[str, Any], body: str) -> None:
    """Write a chapter file with combined front matter and body."""
    write_text(path, build_front_matter(front_matter, body))
