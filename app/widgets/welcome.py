"""Welcome / project picker screen shown on launch."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
)

from app.services.project_manager import load_recent


class WelcomeWidget(QWidget):
    """Landing screen with New/Open project options and recent list."""

    new_project_requested = Signal()
    open_project_requested = Signal()
    recent_project_selected = Signal(str)  # path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Title
        title = QLabel("Web Novel Studio")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Create and manage static web novel sites")
        subtitle.setStyleSheet("font-size: 14px; color: #666;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        new_btn = QPushButton("New Project")
        new_btn.setFixedSize(180, 50)
        new_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #106ebe; }
        """)
        new_btn.clicked.connect(self.new_project_requested)
        btn_layout.addWidget(new_btn)

        open_btn = QPushButton("Open Existing")
        open_btn.setFixedSize(180, 50)
        open_btn.setObjectName("openBtn")
        open_btn.setStyleSheet("""
            QPushButton#openBtn {
                font-size: 15px;
                background-color: palette(button);
                color: palette(button-text);
                border: 1px solid palette(mid);
                border-radius: 6px;
            }
            QPushButton#openBtn:hover { background-color: palette(midlight); }
        """)
        open_btn.clicked.connect(self.open_project_requested)
        btn_layout.addWidget(open_btn)

        layout.addLayout(btn_layout)

        layout.addSpacing(10)

        # Recent projects
        self._recent_group = QGroupBox("Recent Projects")
        self._recent_group.setMaximumWidth(500)
        recent_layout = QVBoxLayout(self._recent_group)

        self._recent_list = QListWidget()
        self._recent_list.setMaximumHeight(250)
        self._recent_list.itemDoubleClicked.connect(self._on_recent_click)
        recent_layout.addWidget(self._recent_list)

        layout.addWidget(self._recent_group, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def refresh_recent(self) -> None:
        """Refresh the recent projects list."""
        self._recent_list.clear()
        recent = load_recent()
        if not recent:
            self._recent_group.setVisible(False)
            return

        self._recent_group.setVisible(True)
        for path_str in recent:
            p = Path(path_str)
            item = QListWidgetItem(f"{p.name}  —  {p}")
            item.setData(Qt.ItemDataRole.UserRole, path_str)
            self._recent_list.addItem(item)

    def _on_recent_click(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.recent_project_selected.emit(path)
