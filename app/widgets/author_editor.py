"""Author editor — list of authors + edit form."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QInputDialog,
    QMessageBox,
)

from app.models.project import Project
from app.utils.yaml_helper import load_yaml, save_yaml


class AuthorEditor(QWidget):
    """Editor for authors.yaml — list on left, form on right."""

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._data: dict = {}
        self._current_key: str | None = None
        self._dirty = False
        self._setup_ui()
        self._load()

    def is_dirty(self) -> bool:
        return self._dirty

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel("<b>Authors</b>"))
        header.addStretch()
        save_btn = QPushButton("Save All")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self.save)
        header.addWidget(save_btn)
        outer.addLayout(header)

        content = QHBoxLayout()

        # Left: author list
        left = QVBoxLayout()
        self._list = QListWidget()
        self._list.setMaximumWidth(220)
        self._list.currentItemChanged.connect(self._on_select)
        left.addWidget(self._list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_author)
        btn_row.addWidget(add_btn)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_author)
        btn_row.addWidget(remove_btn)
        left.addLayout(btn_row)

        content.addLayout(left)

        # Right: edit form
        form_group = QGroupBox("Author Details")
        fl = QFormLayout(form_group)

        self._name = QLineEdit()
        self._name.textChanged.connect(self._mark_dirty)
        fl.addRow("Display Name:", self._name)

        self._bio = QTextEdit()
        self._bio.setMaximumHeight(100)
        self._bio.textChanged.connect(self._mark_dirty)
        fl.addRow("Bio:", self._bio)

        self._avatar = QLineEdit()
        self._avatar.setPlaceholderText("static/images/authors/username.png")
        self._avatar.textChanged.connect(self._mark_dirty)
        fl.addRow("Avatar:", self._avatar)

        self._links = QTextEdit()
        self._links.setMaximumHeight(100)
        self._links.setPlaceholderText("One per line: Label | URL")
        self._links.textChanged.connect(self._mark_dirty)
        fl.addRow("Links:", self._links)

        content.addWidget(form_group)
        outer.addLayout(content)

    def _load(self) -> None:
        if self._project.authors_path.exists():
            self._data = load_yaml(self._project.authors_path)
        else:
            self._data = {"authors": {}}
        self._refresh_list()

    def _refresh_list(self) -> None:
        self._list.clear()
        authors = self._data.get("authors", {})
        for key, info in authors.items():
            label = info.get("name", key)
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._list.addItem(item)

    def _on_select(self, current: QListWidgetItem | None, _prev) -> None:
        if not current:
            self._current_key = None
            return

        # Save previous author's edits back to data before switching
        self._commit_current()

        key = current.data(Qt.ItemDataRole.UserRole)
        self._current_key = key
        info = self._data.get("authors", {}).get(key, {})

        self._name.setText(info.get("name", ""))
        self._bio.setPlainText(info.get("bio", ""))
        self._avatar.setText(info.get("avatar", ""))

        links = info.get("links", [])
        link_lines = [f"{l.get('text', '')} | {l.get('url', '')}" for l in links]
        self._links.setPlainText("\n".join(link_lines))

    def _commit_current(self) -> None:
        """Write current form values back into self._data for the current author."""
        if not self._current_key:
            return
        authors = self._data.setdefault("authors", {})
        info = authors.setdefault(self._current_key, {})
        info["name"] = self._name.text()
        info["bio"] = self._bio.toPlainText()
        avatar = self._avatar.text().strip()
        if avatar:
            info["avatar"] = avatar
        else:
            info.pop("avatar", None)

        links = []
        for line in self._links.toPlainText().strip().splitlines():
            if "|" in line:
                parts = line.split("|", 1)
                links.append({"text": parts[0].strip(), "url": parts[1].strip()})
        info["links"] = links

    def _add_author(self) -> None:
        key, ok = QInputDialog.getText(self, "Add Author", "Author key (e.g. john-doe):")
        if not ok or not key.strip():
            return
        key = key.strip().lower().replace(" ", "-")
        authors = self._data.setdefault("authors", {})
        if key in authors:
            QMessageBox.warning(self, "Exists", f"Author '{key}' already exists.")
            return
        authors[key] = {"name": key.replace("-", " ").title(), "bio": "", "links": []}
        self._refresh_list()
        self._mark_dirty()

    def _remove_author(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        key = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Remove Author", f"Remove author '{key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._data.get("authors", {}).pop(key, None)
            self._current_key = None
            self._refresh_list()
            self._mark_dirty()

    def save(self) -> None:
        self._commit_current()
        try:
            save_yaml(self._project.authors_path, self._data)
            self._dirty = False
            QMessageBox.information(self, "Saved", "Authors saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
