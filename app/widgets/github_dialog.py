"""GitHub settings and publish dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QCheckBox,
    QMessageBox,
    QTabWidget,
    QWidget,
)

from app.services.github_publisher import (
    GitHubPublisher,
    load_github_settings,
    save_github_settings,
)


class GitHubDialog(QDialog):
    """Dialog for configuring GitHub settings and publishing."""

    def __init__(self, build_dir: Path, parent=None):
        super().__init__(parent)
        self._build_dir = build_dir
        self._publisher = GitHubPublisher(self)
        self._publisher.output_line.connect(self._on_output)
        self._publisher.publish_started.connect(self._on_publish_started)
        self._publisher.publish_finished.connect(self._on_publish_finished)

        self.setWindowTitle("GitHub Publishing")
        self.setMinimumSize(600, 550)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # --- Settings tab ---
        settings_tab = QWidget()
        sl = QVBoxLayout(settings_tab)

        info = QLabel(
            "Configure your GitHub token and repository to publish your site.\n"
            "The token needs 'repo' scope permissions.\n"
            "Generate one at: GitHub → Settings → Developer settings → Personal access tokens"
        )
        info.setWordWrap(True)
        sl.addWidget(info)

        token_group = QGroupBox("Authentication")
        tl = QFormLayout(token_group)

        self._token = QLineEdit()
        self._token.setEchoMode(QLineEdit.EchoMode.Password)
        self._token.setPlaceholderText("ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        tl.addRow("GitHub Token:", self._token)

        show_btn = QCheckBox("Show token")
        show_btn.toggled.connect(
            lambda checked: self._token.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        tl.addRow("", show_btn)
        sl.addWidget(token_group)

        repo_group = QGroupBox("Repository")
        rl = QFormLayout(repo_group)

        self._repo = QLineEdit()
        self._repo.setPlaceholderText("username/repo-name")
        rl.addRow("Target Repository:", self._repo)

        self._branch = QComboBox()
        self._branch.setEditable(True)
        self._branch.addItems(["main", "gh-pages", "master"])
        rl.addRow("Branch:", self._branch)

        self._cname = QLineEdit()
        self._cname.setPlaceholderText("www.example.com (optional)")
        rl.addRow("Custom Domain:", self._cname)

        sl.addWidget(repo_group)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)
        sl.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        sl.addStretch()

        help_group = QGroupBox("Setup Guide")
        hl = QVBoxLayout(help_group)
        help_text = QLabel(
            "<b>Two-Repository Setup (Recommended for private source):</b><br>"
            "1. Keep your source in a <b>private</b> repo (protects passwords, drafts)<br>"
            "2. Set the <b>Target Repository</b> above to a separate <b>public</b> repo<br>"
            "3. Enable GitHub Pages on the target repo (Settings → Pages → Deploy from branch)<br>"
            "<br>"
            "<b>Single-Repository Setup:</b><br>"
            "1. Set the <b>Target Repository</b> to your source repo<br>"
            "2. Use <b>gh-pages</b> branch to keep built files separate<br>"
            "3. Enable GitHub Pages with 'gh-pages' as the source branch<br>"
            "<br>"
            "<b>Token Permissions:</b> repo (full control) + workflow"
        )
        help_text.setWordWrap(True)
        help_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        hl.addWidget(help_text)
        sl.addWidget(help_group)

        tabs.addTab(settings_tab, "Settings")

        # --- Publish tab ---
        publish_tab = QWidget()
        pl = QVBoxLayout(publish_tab)

        self._commit_msg = QLineEdit()
        self._commit_msg.setText("Deploy site update")
        self._commit_msg.setPlaceholderText("Commit message")
        pl.addWidget(QLabel("Commit message:"))
        pl.addWidget(self._commit_msg)

        btn_row = QHBoxLayout()
        self._publish_btn = QPushButton("Publish to GitHub Pages")
        self._publish_btn.setFixedHeight(40)
        self._publish_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 24px;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:disabled { background-color: #666; color: #aaa; }
        """)
        self._publish_btn.clicked.connect(self._publish)
        btn_row.addWidget(self._publish_btn)
        pl.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        pl.addWidget(self._progress)

        self._console = QPlainTextEdit()
        self._console.setObjectName("buildConsole")
        self._console.setReadOnly(True)
        self._console.setMaximumBlockCount(2000)
        pl.addWidget(self._console, stretch=1)

        tabs.addTab(publish_tab, "Publish")

        layout.addWidget(tabs)

    def _load_settings(self) -> None:
        s = load_github_settings()
        self._token.setText(s.get("token", ""))
        self._repo.setText(s.get("repo", ""))
        branch = s.get("branch", "main")
        idx = self._branch.findText(branch)
        if idx >= 0:
            self._branch.setCurrentIndex(idx)
        else:
            self._branch.setCurrentText(branch)
        self._cname.setText(s.get("cname", ""))

    def _save_settings(self) -> None:
        save_github_settings({
            "token": self._token.text(),
            "repo": self._repo.text(),
            "branch": self._branch.currentText(),
            "cname": self._cname.text(),
        })
        QMessageBox.information(self, "Saved", "GitHub settings saved.")

    def _publish(self) -> None:
        token = self._token.text().strip()
        repo = self._repo.text().strip()

        if not token:
            QMessageBox.warning(self, "Missing Token", "Enter your GitHub personal access token.")
            return
        if not repo or "/" not in repo:
            QMessageBox.warning(self, "Missing Repo", "Enter repository as 'username/repo-name'.")
            return

        if not (self._build_dir / "index.html").exists():
            QMessageBox.warning(self, "No Build", "Build the site first before publishing.")
            return

        # Save settings before publishing
        self._save_settings()

        self._console.clear()
        self._publisher.publish(
            build_dir=self._build_dir,
            token=token,
            repo=repo,
            branch=self._branch.currentText(),
            cname=self._cname.text().strip(),
            commit_message=self._commit_msg.text() or "Deploy site update",
        )

    def _on_output(self, line: str) -> None:
        self._console.appendPlainText(line)

    def _on_publish_started(self) -> None:
        self._publish_btn.setEnabled(False)
        self._progress.setVisible(True)

    def _on_publish_finished(self, success: bool, message: str) -> None:
        self._publish_btn.setEnabled(True)
        self._progress.setVisible(False)
        if success:
            QMessageBox.information(self, "Published", message)
        else:
            QMessageBox.critical(self, "Publish Failed", message)
