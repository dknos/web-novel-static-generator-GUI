"""Webring editor — manage webring.yaml for cross-promotion."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QSpinBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QMessageBox,
)

from app.models.project import Project
from app.utils.yaml_helper import load_yaml, save_yaml


class WebringEditor(QWidget):
    """Editor for webring.yaml — sites list + settings."""

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._path = project.root / "webring.yaml"
        self._data: dict = {}
        self._current_idx: int = -1
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
        header.addWidget(QLabel("<b>Webring Configuration</b>"))
        header.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self.save)
        header.addWidget(save_btn)
        outer.addLayout(header)

        info = QLabel(
            "Cross-promote with fellow authors through RSS-based discovery feeds.\n"
            "RSS feeds are fetched at build time and shown on your front page."
        )
        info.setWordWrap(True)
        outer.addWidget(info)

        # --- Settings ---
        settings = QGroupBox("Settings")
        sl = QFormLayout(settings)
        self._enabled = QCheckBox("Enable webring")
        self._enabled.stateChanged.connect(self._mark_dirty)
        sl.addRow(self._enabled)
        self._max_items = QSpinBox()
        self._max_items.setRange(1, 100)
        self._max_items.valueChanged.connect(self._mark_dirty)
        sl.addRow("Max Items:", self._max_items)
        outer.addWidget(settings)

        # --- Display ---
        display = QGroupBox("Display")
        dl = QFormLayout(display)
        self._disp_title = QLineEdit()
        self._disp_title.setPlaceholderText("Recent Updates from the Webring")
        self._disp_title.textChanged.connect(self._mark_dirty)
        dl.addRow("Title:", self._disp_title)
        self._disp_subtitle = QLineEdit()
        self._disp_subtitle.setPlaceholderText("Check out recent chapters from fellow authors")
        self._disp_subtitle.textChanged.connect(self._mark_dirty)
        dl.addRow("Subtitle:", self._disp_subtitle)
        outer.addWidget(display)

        # --- Sites ---
        sites_group = QGroupBox("Sites")
        sgl = QHBoxLayout(sites_group)

        # Left: list
        left = QVBoxLayout()
        self._sites_list = QListWidget()
        self._sites_list.setMaximumWidth(250)
        self._sites_list.currentRowChanged.connect(self._on_site_select)
        left.addWidget(self._sites_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_site)
        btn_row.addWidget(add_btn)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_site)
        btn_row.addWidget(remove_btn)
        left.addLayout(btn_row)
        sgl.addLayout(left)

        # Right: edit form
        right = QVBoxLayout()
        self._site_name = QLineEdit()
        self._site_name.setPlaceholderText("Site or author name")
        self._site_name.textChanged.connect(self._mark_dirty)
        right.addWidget(QLabel("Name:"))
        right.addWidget(self._site_name)

        self._site_url = QLineEdit()
        self._site_url.setPlaceholderText("https://example.com/")
        self._site_url.textChanged.connect(self._mark_dirty)
        right.addWidget(QLabel("URL:"))
        right.addWidget(self._site_url)

        self._site_rss = QLineEdit()
        self._site_rss.setPlaceholderText("https://example.com/rss.xml")
        self._site_rss.textChanged.connect(self._mark_dirty)
        right.addWidget(QLabel("RSS Feed:"))
        right.addWidget(self._site_rss)

        self._site_desc = QLineEdit()
        self._site_desc.setPlaceholderText("Short description")
        self._site_desc.textChanged.connect(self._mark_dirty)
        right.addWidget(QLabel("Description:"))
        right.addWidget(self._site_desc)

        right.addStretch()
        sgl.addLayout(right)

        outer.addWidget(sites_group, stretch=1)

    def _load(self) -> None:
        if self._path.exists():
            self._data = load_yaml(self._path)
        else:
            self._data = {
                "webring": {
                    "enabled": False,
                    "max_items": 20,
                    "sites": [],
                }
            }

        wr = self._data.get("webring", {})
        self._enabled.setChecked(wr.get("enabled", False))
        self._max_items.setValue(wr.get("max_items", 20))

        disp = wr.get("display", {})
        self._disp_title.setText(disp.get("title", ""))
        self._disp_subtitle.setText(disp.get("subtitle", ""))

        self._refresh_sites()
        self._dirty = False

    def _refresh_sites(self) -> None:
        self._sites_list.clear()
        sites = self._data.get("webring", {}).get("sites", [])
        for site in sites:
            self._sites_list.addItem(site.get("name", "Unnamed"))
        self._current_idx = -1

    def _on_site_select(self, idx: int) -> None:
        # Save previous site's edits
        self._commit_current_site()

        self._current_idx = idx
        sites = self._data.get("webring", {}).get("sites", [])
        if 0 <= idx < len(sites):
            site = sites[idx]
            self._site_name.setText(site.get("name", ""))
            self._site_url.setText(site.get("url", ""))
            self._site_rss.setText(site.get("rss", ""))
            self._site_desc.setText(site.get("description", ""))
        else:
            self._site_name.clear()
            self._site_url.clear()
            self._site_rss.clear()
            self._site_desc.clear()

    def _commit_current_site(self) -> None:
        sites = self._data.get("webring", {}).get("sites", [])
        if 0 <= self._current_idx < len(sites):
            sites[self._current_idx] = {
                "name": self._site_name.text(),
                "url": self._site_url.text(),
                "rss": self._site_rss.text(),
                "description": self._site_desc.text(),
            }

    def _add_site(self) -> None:
        self._commit_current_site()
        wr = self._data.setdefault("webring", {})
        sites = wr.setdefault("sites", [])
        sites.append({"name": "New Site", "url": "", "rss": "", "description": ""})
        self._refresh_sites()
        self._sites_list.setCurrentRow(len(sites) - 1)
        self._mark_dirty()

    def _remove_site(self) -> None:
        idx = self._sites_list.currentRow()
        sites = self._data.get("webring", {}).get("sites", [])
        if 0 <= idx < len(sites):
            sites.pop(idx)
            self._current_idx = -1
            self._refresh_sites()
            self._mark_dirty()

    def save(self) -> None:
        self._commit_current_site()

        wr = self._data.setdefault("webring", {})
        wr["enabled"] = self._enabled.isChecked()
        wr["max_items"] = self._max_items.value()

        disp = {}
        if self._disp_title.text():
            disp["title"] = self._disp_title.text()
        if self._disp_subtitle.text():
            disp["subtitle"] = self._disp_subtitle.text()
        if disp:
            wr["display"] = disp

        try:
            save_yaml(self._path, self._data)
            self._dirty = False
            QMessageBox.information(self, "Saved", "Webring configuration saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
