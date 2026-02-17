"""Sidebar tree widget for project navigation."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QMenu,
    QInputDialog,
    QMessageBox,
)

from app.models.project import Project
from app.models.novel import NovelConfig


# Item data role for storing metadata
ROLE_TYPE = Qt.ItemDataRole.UserRole
ROLE_PATH = Qt.ItemDataRole.UserRole + 1


class Sidebar(QTreeWidget):
    """Project navigation tree."""

    # Signals: (item_type, path_or_identifier)
    item_selected = Signal(str, str)  # e.g. ("site_config", ""), ("chapter", "/path/to/ch.md")
    novel_added = Signal(str)          # slug
    chapter_added = Signal(str, str)   # novel_slug, chapter_id
    item_deleted = Signal(str, str)    # type, path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.itemClicked.connect(self._on_click)
        self.setMinimumWidth(220)
        self.setMaximumWidth(350)
        self._project: Project | None = None

    def load_project(self, project: Project) -> None:
        """Populate the tree from a project."""
        self._project = project
        self.clear()

        # Site Config
        cfg_item = QTreeWidgetItem(self, ["Site Config"])
        cfg_item.setData(0, ROLE_TYPE, "site_config")
        cfg_item.setData(0, ROLE_PATH, str(project.site_config_path))

        # Authors
        auth_item = QTreeWidgetItem(self, ["Authors"])
        auth_item.setData(0, ROLE_TYPE, "authors")
        auth_item.setData(0, ROLE_PATH, str(project.authors_path))

        # Webring
        webring_item = QTreeWidgetItem(self, ["Webring"])
        webring_item.setData(0, ROLE_TYPE, "webring")
        webring_item.setData(0, ROLE_PATH, str(project.root / "webring.yaml"))

        # Novels
        novels_item = QTreeWidgetItem(self, ["Novels"])
        novels_item.setData(0, ROLE_TYPE, "novels_root")
        novels_item.setFlags(novels_item.flags() | Qt.ItemFlag.ItemIsEnabled)

        for slug in project.novel_slugs():
            self._add_novel_node(novels_item, slug)

        novels_item.setExpanded(True)

        # Pages
        pages_item = QTreeWidgetItem(self, ["Pages"])
        pages_item.setData(0, ROLE_TYPE, "pages_root")
        for page_path in project.page_files():
            p_item = QTreeWidgetItem(pages_item, [page_path.stem])
            p_item.setData(0, ROLE_TYPE, "page")
            p_item.setData(0, ROLE_PATH, str(page_path))

        if pages_item.childCount():
            pages_item.setExpanded(True)

        # Build
        build_item = QTreeWidgetItem(self, ["Build"])
        build_item.setData(0, ROLE_TYPE, "build")

    def _add_novel_node(self, parent: QTreeWidgetItem, slug: str) -> QTreeWidgetItem:
        assert self._project is not None
        config_path = self._project.novel_config_path(slug)

        # Try to read novel title
        try:
            nc = NovelConfig.from_file(config_path)
            label = nc.title or slug
        except Exception:
            label = slug

        novel_item = QTreeWidgetItem(parent, [label])
        novel_item.setData(0, ROLE_TYPE, "novel")
        novel_item.setData(0, ROLE_PATH, slug)

        # Chapters
        for ch_path in self._project.chapter_files(slug):
            ch_item = QTreeWidgetItem(novel_item, [ch_path.stem])
            ch_item.setData(0, ROLE_TYPE, "chapter")
            ch_item.setData(0, ROLE_PATH, str(ch_path))

        novel_item.setExpanded(True)
        return novel_item

    # ------------------------------------------------------------------
    # Click handling
    # ------------------------------------------------------------------

    def _on_click(self, item: QTreeWidgetItem, _col: int) -> None:
        item_type = item.data(0, ROLE_TYPE)
        item_path = item.data(0, ROLE_PATH) or ""
        if item_type and item_type not in ("novels_root", "pages_root"):
            self.item_selected.emit(item_type, item_path)

    # ------------------------------------------------------------------
    # Context menus
    # ------------------------------------------------------------------

    def _context_menu(self, pos) -> None:
        item = self.itemAt(pos)
        if not item:
            return
        item_type = item.data(0, ROLE_TYPE)

        menu = QMenu(self)

        if item_type == "novels_root":
            menu.addAction("Add Novel", lambda: self._add_novel())
        elif item_type == "novel":
            slug = item.data(0, ROLE_PATH)
            menu.addAction("Add Chapter", lambda: self._add_chapter(slug))
            menu.addAction("Delete Novel", lambda: self._delete_novel(slug))
        elif item_type == "chapter":
            path = item.data(0, ROLE_PATH)
            menu.addAction("Delete Chapter", lambda: self._delete_item("chapter", path))
        elif item_type == "pages_root":
            menu.addAction("Add Page", lambda: self._add_page())
        elif item_type == "page":
            path = item.data(0, ROLE_PATH)
            menu.addAction("Delete Page", lambda: self._delete_item("page", path))

        if menu.actions():
            menu.exec(self.viewport().mapToGlobal(pos))

    def _add_novel(self) -> None:
        if not self._project:
            return
        slug, ok = QInputDialog.getText(self, "New Novel", "Novel slug (e.g. my-novel):")
        if not ok or not slug.strip():
            return
        slug = slug.strip().lower().replace(" ", "-")
        self.novel_added.emit(slug)

    def _add_chapter(self, novel_slug: str) -> None:
        chapter_id, ok = QInputDialog.getText(
            self, "New Chapter", "Chapter ID (e.g. chapter-1):"
        )
        if not ok or not chapter_id.strip():
            return
        chapter_id = chapter_id.strip().lower().replace(" ", "-")
        self.chapter_added.emit(novel_slug, chapter_id)

    def _add_page(self) -> None:
        if not self._project:
            return
        name, ok = QInputDialog.getText(self, "New Page", "Page filename (e.g. about):")
        if not ok or not name.strip():
            return
        name = name.strip().lower().replace(" ", "-")
        if not name.endswith(".md"):
            name += ".md"
        page_path = self._project.pages_dir / name
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(f"---\ntitle: \"{name.replace('.md', '').replace('-', ' ').title()}\"\n---\n\n# {name.replace('.md', '').replace('-', ' ').title()}\n\nContent here.\n", encoding="utf-8")
        self.load_project(self._project)
        self.item_selected.emit("page", str(page_path))

    def _delete_novel(self, slug: str) -> None:
        if not self._project:
            return
        reply = QMessageBox.question(
            self,
            "Delete Novel",
            f"Delete novel '{slug}' and all its chapters?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            import shutil
            novel_dir = self._project.content_dir / slug
            if novel_dir.exists():
                shutil.rmtree(novel_dir)
            self.load_project(self._project)
            self.item_deleted.emit("novel", slug)

    def _delete_item(self, item_type: str, path_str: str) -> None:
        path = Path(path_str)
        reply = QMessageBox.question(
            self,
            f"Delete {item_type.title()}",
            f"Delete '{path.name}'?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if path.exists():
                path.unlink()
            if self._project:
                self.load_project(self._project)
            self.item_deleted.emit(item_type, path_str)
