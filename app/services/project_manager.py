"""Project management — create, open, list recent projects."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.models.project import Project
from app.utils.yaml_helper import save_yaml


RECENT_FILE = Path.home() / ".web-novel-app" / "recent.json"
MAX_RECENT = 10


# ------------------------------------------------------------------
# Recent projects
# ------------------------------------------------------------------

def load_recent() -> list[str]:
    """Return list of recent project paths (most recent first)."""
    if not RECENT_FILE.exists():
        return []
    try:
        data = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
        return [p for p in data if Path(p).exists()]
    except (json.JSONDecodeError, KeyError):
        return []


def add_recent(project_path: str) -> None:
    """Add a project path to the recent list."""
    recent = load_recent()
    # Remove if already present, then prepend
    normalized = str(Path(project_path).resolve())
    recent = [p for p in recent if str(Path(p).resolve()) != normalized]
    recent.insert(0, normalized)
    recent = recent[:MAX_RECENT]

    RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECENT_FILE.write_text(json.dumps(recent, indent=2), encoding="utf-8")


# ------------------------------------------------------------------
# Open project
# ------------------------------------------------------------------

def open_project(path: str | Path) -> Project:
    """Open an existing project from a directory path."""
    project = Project(root=Path(path))
    if not project.is_valid():
        raise FileNotFoundError(
            f"Not a valid project: missing site_config.yaml or generate.py in {path}"
        )
    add_recent(str(project.root))
    return project


# ------------------------------------------------------------------
# Create new project
# ------------------------------------------------------------------

def create_project(directory: str | Path, site_name: str = "My Novel Site") -> Project:
    """Create a new project with scaffold files."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)

    # Copy generator files
    generator_src = Path(__file__).resolve().parent.parent.parent / "generator"
    if not generator_src.exists():
        raise FileNotFoundError(f"Generator not found at {generator_src}")

    # Copy essential generator files
    for item in ["generate.py", "templates", "static"]:
        src = generator_src / item
        dst = root / item
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        elif src.is_file():
            shutil.copy2(src, dst)

    # Create site_config.yaml
    site_config: dict[str, Any] = {
        "site_name": site_name,
        "site_description": "A web novel collection",
        "site_url": "https://example.com",
        "site_author": "Author",
        "languages": {"available": ["en"]},
        "rss": {"generate_feeds": True, "site_feed": {
            "title": f"{site_name} - Latest Chapters",
            "description": "Latest chapter updates",
        }, "story_feeds_enabled": True},
        "epub": {"generate_enabled": True},
        "comments": {"enabled": False},
        "image_optimization": {"enabled": False, "quality": 85},
        "footer": {
            "copyright": f"© {site_name}",
            "links": [],
        },
    }
    save_yaml(root / "site_config.yaml", site_config)

    # Create authors.yaml
    save_yaml(root / "authors.yaml", {
        "authors": {
            "default-author": {
                "name": "Author Name",
                "bio": "About the author.",
                "links": [],
            }
        }
    })

    # Create sample novel
    novel_dir = root / "content" / "sample-novel"
    chapters_dir = novel_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    novel_config: dict[str, Any] = {
        "title": "Sample Novel",
        "description": "A sample novel to get you started.",
        "slug": "sample-novel",
        "primary_language": "en",
        "status": "ongoing",
        "tags": ["sample"],
        "author": {"name": "Author Name"},
        "languages": {"default": "en", "available": ["en"]},
        "downloads": {"epub_enabled": True},
        "comments": {"enabled": False},
        "arcs": [{
            "title": "Arc 1",
            "chapters": [{"id": "chapter-1", "title": "Chapter 1: Getting Started"}],
        }],
    }
    save_yaml(novel_dir / "config.yaml", novel_config)

    # Sample chapter
    chapter_text = """---
title: "Chapter 1: Getting Started"
author: "Author Name"
published: "2025-01-01"
tags: ["sample"]
---

# Chapter 1: Getting Started

Welcome to your first chapter! Edit this file to start writing your novel.
"""
    (chapters_dir / "chapter-1.md").write_text(chapter_text, encoding="utf-8")

    # Create pages directory with sample
    pages_dir = root / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    about_text = """---
title: "About"
description: "About this site"
navigation: "header"
nav_order: 10
---

# About

Welcome to this web novel site!
"""
    (pages_dir / "about.md").write_text(about_text, encoding="utf-8")

    project = Project(root=root)
    add_recent(str(root))
    return project
