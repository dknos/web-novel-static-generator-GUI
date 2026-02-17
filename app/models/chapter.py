"""Chapter data model — front matter + markdown body."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.utils.yaml_helper import parse_front_matter, build_front_matter


@dataclass
class Chapter:
    """In-memory representation of a chapter markdown file."""

    path: Path
    front_matter: dict[str, Any] = field(default_factory=dict)
    body: str = ""

    # Convenience accessors for common front-matter fields
    @property
    def title(self) -> str:
        return self.front_matter.get("title", self.path.stem)

    @title.setter
    def title(self, value: str) -> None:
        self.front_matter["title"] = value

    @property
    def author(self) -> str:
        return self.front_matter.get("author", "")

    @author.setter
    def author(self, value: str) -> None:
        if value:
            self.front_matter["author"] = value
        else:
            self.front_matter.pop("author", None)

    @property
    def translator(self) -> str:
        return self.front_matter.get("translator", "")

    @translator.setter
    def translator(self, value: str) -> None:
        if value:
            self.front_matter["translator"] = value
        else:
            self.front_matter.pop("translator", None)

    @property
    def published(self) -> str:
        val = self.front_matter.get("published", "")
        return str(val) if val else ""

    @published.setter
    def published(self, value: str) -> None:
        if value:
            self.front_matter["published"] = value
        else:
            self.front_matter.pop("published", None)

    @property
    def tags(self) -> list[str]:
        return self.front_matter.get("tags", [])

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self.front_matter["tags"] = value

    @property
    def is_draft(self) -> bool:
        return self.front_matter.get("draft", False)

    @is_draft.setter
    def is_draft(self, value: bool) -> None:
        if value:
            self.front_matter["draft"] = True
        else:
            self.front_matter.pop("draft", None)

    @property
    def password(self) -> str:
        return self.front_matter.get("password", "")

    @password.setter
    def password(self, value: str) -> None:
        if value:
            self.front_matter["password"] = value
        else:
            self.front_matter.pop("password", None)

    @property
    def password_hint(self) -> str:
        return self.front_matter.get("password_hint", "")

    @password_hint.setter
    def password_hint(self, value: str) -> None:
        if value:
            self.front_matter["password_hint"] = value
        else:
            self.front_matter.pop("password_hint", None)

    @property
    def translation_notes(self) -> str:
        return self.front_matter.get("translation_notes", "")

    @translation_notes.setter
    def translation_notes(self, value: str) -> None:
        if value:
            self.front_matter["translation_notes"] = value
        else:
            self.front_matter.pop("translation_notes", None)

    @property
    def status(self) -> str:
        return self.front_matter.get("status", "")

    @status.setter
    def status(self, value: str) -> None:
        if value:
            self.front_matter["status"] = value
        else:
            self.front_matter.pop("status", None)

    @property
    def contributors(self) -> list[dict]:
        return self.front_matter.get("contributors", [])

    @contributors.setter
    def contributors(self, value: list[dict]) -> None:
        if value:
            self.front_matter["contributors"] = value
        else:
            self.front_matter.pop("contributors", None)

    @property
    def reviewers(self) -> list[str]:
        return self.front_matter.get("reviewers", [])

    @reviewers.setter
    def reviewers(self, value: list[str]) -> None:
        if value:
            self.front_matter["reviewers"] = value
        else:
            self.front_matter.pop("reviewers", None)

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: Path) -> Chapter:
        text = path.read_text(encoding="utf-8")
        fm, body = parse_front_matter(text)
        return cls(path=path, front_matter=fm, body=body)

    def to_text(self) -> str:
        if self.front_matter:
            return build_front_matter(self.front_matter, self.body)
        return self.body

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.to_text(), encoding="utf-8")
