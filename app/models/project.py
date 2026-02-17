"""Project data model — represents an opened web-novel project on disk."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.utils.yaml_helper import load_yaml


@dataclass
class Project:
    """Represents an opened web-novel project."""

    root: Path  # Project root directory (contains site_config.yaml)

    @property
    def site_config_path(self) -> Path:
        return self.root / "site_config.yaml"

    @property
    def authors_path(self) -> Path:
        return self.root / "authors.yaml"

    @property
    def content_dir(self) -> Path:
        return self.root / "content"

    @property
    def pages_dir(self) -> Path:
        return self.root / "pages"

    @property
    def build_dir(self) -> Path:
        return self.root / "build"

    @property
    def static_dir(self) -> Path:
        return self.root / "static"

    @property
    def generator_script(self) -> Path:
        return self.root / "generate.py"

    @property
    def templates_dir(self) -> Path:
        return self.root / "templates"

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def is_valid(self) -> bool:
        """Check whether this looks like a valid project directory."""
        return self.site_config_path.exists() and self.generator_script.exists()

    def novel_slugs(self) -> list[str]:
        """Return a sorted list of novel directory slugs."""
        if not self.content_dir.exists():
            return []
        return sorted(
            d.name
            for d in self.content_dir.iterdir()
            if d.is_dir() and (d / "config.yaml").exists()
        )

    def novel_config_path(self, slug: str) -> Path:
        return self.content_dir / slug / "config.yaml"

    def chapters_dir(self, slug: str) -> Path:
        return self.content_dir / slug / "chapters"

    def chapter_files(self, slug: str) -> list[Path]:
        """Return markdown chapter files for a novel (non-recursive, top-level only)."""
        cdir = self.chapters_dir(slug)
        if not cdir.exists():
            return []
        files = sorted(cdir.glob("*.md"))
        return files

    def page_files(self) -> list[Path]:
        """Return top-level page markdown files."""
        if not self.pages_dir.exists():
            return []
        return sorted(self.pages_dir.glob("*.md"))

    def load_site_config(self) -> dict[str, Any]:
        return load_yaml(self.site_config_path)

    def load_authors(self) -> dict[str, Any]:
        if not self.authors_path.exists():
            return {"authors": {}}
        return load_yaml(self.authors_path)
