"""Site preview — embedded browser for the built site."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PySide6.QtWebEngineWidgets import QWebEngineView


class SitePreview(QWidget):
    """Embedded Chromium browser for previewing the built site."""

    def __init__(self, build_dir: Path, parent=None):
        super().__init__(parent)
        self._build_dir = build_dir
        self._setup_ui()
        self._load_site()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Navigation toolbar
        nav = QHBoxLayout()

        self._back_btn = QPushButton("<")
        self._back_btn.setFixedWidth(32)
        self._back_btn.clicked.connect(lambda: self._browser.back())
        nav.addWidget(self._back_btn)

        self._forward_btn = QPushButton(">")
        self._forward_btn.setFixedWidth(32)
        self._forward_btn.clicked.connect(lambda: self._browser.forward())
        nav.addWidget(self._forward_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setFixedWidth(70)
        self._refresh_btn.clicked.connect(lambda: self._browser.reload())
        nav.addWidget(self._refresh_btn)

        self._url_bar = QLineEdit()
        self._url_bar.setReadOnly(True)
        nav.addWidget(self._url_bar)

        home_btn = QPushButton("Home")
        home_btn.setFixedWidth(60)
        home_btn.clicked.connect(self._load_site)
        nav.addWidget(home_btn)

        layout.addLayout(nav)

        # Browser
        self._browser = QWebEngineView()
        self._browser.urlChanged.connect(self._on_url_changed)
        layout.addWidget(self._browser, stretch=1)

    def _load_site(self) -> None:
        index = self._build_dir / "index.html"
        if index.exists():
            self._browser.setUrl(QUrl.fromLocalFile(str(index)))
        else:
            self._browser.setHtml(
                "<html><body><h2>No build found</h2>"
                "<p>Build the site first to see a preview.</p></body></html>"
            )

    def _on_url_changed(self, url: QUrl) -> None:
        self._url_bar.setText(url.toString())
