"""Novel configuration model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.utils.yaml_helper import load_yaml, save_yaml


@dataclass
class ArcChapter:
    id: str
    title: str


@dataclass
class Arc:
    title: str
    chapters: list[ArcChapter] = field(default_factory=list)
    cover_art: str = ""


@dataclass
class NovelConfig:
    """In-memory representation of a novel's config.yaml."""

    path: Path  # Path to config.yaml

    # Basic info
    title: str = ""
    slug: str = ""
    description: str = ""
    status: str = "ongoing"
    primary_language: str = "en"
    tags: list[str] = field(default_factory=list)
    chapter_type: str = ""  # "" for text, "manga" for manga

    # Cover
    cover_art: str = ""

    # Author
    author_name: str = ""
    copyright: str = ""

    # Languages
    languages_default: str = "en"
    languages_available: list[str] = field(default_factory=lambda: ["en"])

    # Feature toggles
    epub_enabled: bool = True
    comments_enabled: bool = True
    comments_toc: bool = True
    comments_chapter: bool = True

    # Arcs
    arcs: list[Arc] = field(default_factory=list)

    # Raw data for fields we don't explicitly model
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: Path) -> NovelConfig:
        data = load_yaml(path)
        arcs = []
        for arc_data in data.get("arcs", []):
            chapters = [
                ArcChapter(id=c.get("id", ""), title=c.get("title", ""))
                for c in arc_data.get("chapters", [])
            ]
            arcs.append(Arc(
                title=arc_data.get("title", ""),
                chapters=chapters,
                cover_art=arc_data.get("cover_art", ""),
            ))

        front_page = data.get("front_page", {})
        languages = data.get("languages", {})
        downloads = data.get("downloads", {})
        comments = data.get("comments", {})
        author = data.get("author", {})

        return cls(
            path=path,
            title=data.get("title", ""),
            slug=data.get("slug", ""),
            description=data.get("description", ""),
            status=data.get("status", "ongoing"),
            primary_language=data.get("primary_language", "en"),
            tags=data.get("tags", []),
            chapter_type=data.get("chapter_type", ""),
            cover_art=front_page.get("cover_art", ""),
            author_name=author.get("name", "") if isinstance(author, dict) else str(author),
            copyright=data.get("copyright", ""),
            languages_default=languages.get("default", "en"),
            languages_available=languages.get("available", ["en"]),
            epub_enabled=downloads.get("epub_enabled", True),
            comments_enabled=comments.get("enabled", True),
            comments_toc=comments.get("toc_comments", True),
            comments_chapter=comments.get("chapter_comments", True),
            arcs=arcs,
            _raw=data,
        )

    def to_dict(self) -> dict[str, Any]:
        """Merge editable fields back into the raw dict for saving."""
        data = dict(self._raw)
        data["title"] = self.title
        data["slug"] = self.slug
        data["description"] = self.description
        data["status"] = self.status
        data["primary_language"] = self.primary_language
        data["tags"] = self.tags
        if self.chapter_type:
            data["chapter_type"] = self.chapter_type

        data.setdefault("front_page", {})
        data["front_page"]["cover_art"] = self.cover_art

        data["author"] = {"name": self.author_name}
        data["copyright"] = self.copyright

        data["languages"] = {
            "default": self.languages_default,
            "available": self.languages_available,
        }
        data.setdefault("downloads", {})
        data["downloads"]["epub_enabled"] = self.epub_enabled

        data.setdefault("comments", {})
        data["comments"]["enabled"] = self.comments_enabled
        data["comments"]["toc_comments"] = self.comments_toc
        data["comments"]["chapter_comments"] = self.comments_chapter

        # Arcs
        data["arcs"] = []
        for arc in self.arcs:
            arc_dict: dict[str, Any] = {"title": arc.title, "chapters": []}
            if arc.cover_art:
                arc_dict["cover_art"] = arc.cover_art
            for ch in arc.chapters:
                arc_dict["chapters"].append({"id": ch.id, "title": ch.title})
            data["arcs"].append(arc_dict)

        return data

    def save(self) -> None:
        save_yaml(self.path, self.to_dict())
