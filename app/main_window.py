"""Main application window."""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QToolBar,
    QPlainTextEdit,
)

from app.models.project import Project
from app.models.novel import NovelConfig, Arc, ArcChapter
from app.models.chapter import Chapter
from app.sidebar import Sidebar
from app.services import project_manager
from app.services.generator import GeneratorRunner
from app.utils.yaml_helper import save_yaml

# Widget imports
from app.widgets.welcome import WelcomeWidget
from app.widgets.config_editor import ConfigEditor
from app.widgets.novel_editor import NovelEditor
from app.widgets.author_editor import AuthorEditor
from app.widgets.chapter_editor import ChapterEditor
from app.widgets.build_panel import BuildPanel
from app.widgets.site_preview import SitePreview
from app.widgets.webring_editor import WebringEditor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Novel Studio")
        self.resize(1400, 900)

        self._project: Project | None = None
        self._generator: GeneratorRunner | None = None
        self._unsaved_editors: dict[str, bool] = {}  # path -> dirty flag

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_shortcuts()

        # Show welcome screen
        self._show_welcome()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.item_selected.connect(self._on_sidebar_select)
        self._sidebar.novel_added.connect(self._on_novel_added)
        self._sidebar.chapter_added.connect(self._on_chapter_added)

        # Central stacked widget
        self._stack = QStackedWidget()

        # Welcome widget
        self._welcome = WelcomeWidget()
        self._welcome.new_project_requested.connect(self._new_project)
        self._welcome.open_project_requested.connect(self._open_project_dialog)
        self._welcome.recent_project_selected.connect(self._open_project)
        self._stack.addWidget(self._welcome)

        # Splitter: sidebar | content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 1140])
        self.setCentralWidget(splitter)

        # Bottom dock: build console
        self._console = QPlainTextEdit()
        self._console.setObjectName("buildConsole")
        self._console.setReadOnly(True)
        self._console.setMaximumBlockCount(5000)

        dock = QDockWidget("Build Output", self)
        dock.setWidget(self._console)
        dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        dock.setMinimumHeight(120)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _setup_menus(self) -> None:
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Project...", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)

        open_action = QAction("&Open Project...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self._open_project_dialog)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self._save_current)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Build menu
        build_menu = menubar.addMenu("&Build")

        build_action = QAction("&Build Site", self)
        build_action.setShortcut(QKeySequence("Ctrl+B"))
        build_action.triggered.connect(self._build_site)
        build_menu.addAction(build_action)

        clean_action = QAction("&Clean Build", self)
        clean_action.triggered.connect(lambda: self._build_site(clean=True))
        build_menu.addAction(clean_action)

        build_menu.addSeparator()

        preview_action = QAction("&Preview Site", self)
        preview_action.setShortcut(QKeySequence("Ctrl+P"))
        preview_action.triggered.connect(self._preview_site)
        build_menu.addAction(preview_action)

        build_menu.addSeparator()

        validate_action = QAction("&Validate Config", self)
        validate_action.triggered.connect(self._validate)
        build_menu.addAction(validate_action)

        stats_action = QAction("Generate &Stats Report", self)
        stats_action.triggered.connect(self._generate_stats)
        build_menu.addAction(stats_action)

        check_links_action = QAction("Check &Links", self)
        check_links_action.triggered.connect(self._check_links)
        build_menu.addAction(check_links_action)

        check_a11y_action = QAction("Check &Accessibility", self)
        check_a11y_action.triggered.connect(self._check_accessibility)
        build_menu.addAction(check_a11y_action)

        build_menu.addSeparator()

        build_panel_action = QAction("Build &Options...", self)
        build_panel_action.triggered.connect(self._show_build_panel)
        build_menu.addAction(build_panel_action)

        # Publish menu
        publish_menu = menubar.addMenu("&Publish")

        github_action = QAction("&Publish to GitHub Pages...", self)
        github_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        github_action.triggered.connect(self._publish_github)
        publish_menu.addAction(github_action)

        github_settings_action = QAction("GitHub &Settings...", self)
        github_settings_action.triggered.connect(self._github_settings)
        publish_menu.addAction(github_settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addAction("Build", self._build_site)
        toolbar.addAction("Preview", self._preview_site)
        toolbar.addAction("Publish", self._publish_github)
        toolbar.addSeparator()
        toolbar.addAction("Build Options", self._show_build_panel)

    def _setup_shortcuts(self) -> None:
        pass  # Shortcuts are set via menu actions above

    # ------------------------------------------------------------------
    # Welcome / project loading
    # ------------------------------------------------------------------

    def _show_welcome(self) -> None:
        self._welcome.refresh_recent()
        self._stack.setCurrentWidget(self._welcome)
        self._sidebar.setVisible(False)

    def _new_project(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Choose directory for new project"
        )
        if not directory:
            return

        name, ok = QInputDialog.getText(
            self, "Site Name", "Enter site name:", text="My Novel Site"
        )
        if not ok:
            return

        try:
            project = project_manager.create_project(directory, name)
            self._load_project(project)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create project:\n{e}")

    def _open_project_dialog(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Open project directory"
        )
        if directory:
            self._open_project(directory)

    def _open_project(self, path: str) -> None:
        try:
            project = project_manager.open_project(path)
            self._load_project(project)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{e}")

    def _load_project(self, project: Project) -> None:
        self._project = project
        self._generator = GeneratorRunner(project.root)
        self._generator.output_line.connect(self._console.appendPlainText)
        self._generator.finished.connect(self._on_build_finished)

        self._sidebar.setVisible(True)
        self._sidebar.load_project(project)

        # Remove old widgets from stack (keep welcome at index 0)
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            w.deleteLater()

        self.setWindowTitle(f"Web Novel Studio — {project.root.name}")
        self.statusBar().showMessage(f"Project loaded: {project.root}")

        # Show site config by default
        self._on_sidebar_select("site_config", str(project.site_config_path))

    # ------------------------------------------------------------------
    # Sidebar navigation
    # ------------------------------------------------------------------

    def _on_sidebar_select(self, item_type: str, item_path: str) -> None:
        if not self._project:
            return

        # Remove current editor (keep welcome at 0)
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            w.deleteLater()

        widget = None

        if item_type == "site_config":
            widget = ConfigEditor(self._project)
        elif item_type == "authors":
            widget = AuthorEditor(self._project)
        elif item_type == "webring":
            widget = WebringEditor(self._project)
        elif item_type == "novel":
            config_path = self._project.novel_config_path(item_path)
            if config_path.exists():
                widget = NovelEditor(config_path, self._project)
        elif item_type == "chapter":
            widget = ChapterEditor(Path(item_path), self._project, is_page=False)
        elif item_type == "page":
            widget = ChapterEditor(Path(item_path), self._project, is_page=True)
        elif item_type == "build":
            widget = BuildPanel(self._project, self._generator)
            widget.preview_requested.connect(self._preview_site)

        if widget:
            self._stack.addWidget(widget)
            self._stack.setCurrentWidget(widget)

    # ------------------------------------------------------------------
    # Novel / chapter creation
    # ------------------------------------------------------------------

    def _on_novel_added(self, slug: str) -> None:
        if not self._project:
            return

        novel_dir = self._project.content_dir / slug
        chapters_dir = novel_dir / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "title": slug.replace("-", " ").title(),
            "description": "",
            "slug": slug,
            "primary_language": "en",
            "status": "ongoing",
            "tags": [],
            "author": {"name": "Author"},
            "languages": {"default": "en", "available": ["en"]},
            "downloads": {"epub_enabled": True},
            "comments": {"enabled": False},
            "arcs": [{"title": "Arc 1", "chapters": []}],
        }
        save_yaml(novel_dir / "config.yaml", config)

        self._sidebar.load_project(self._project)
        self.statusBar().showMessage(f"Novel '{slug}' created")

    def _on_chapter_added(self, novel_slug: str, chapter_id: str) -> None:
        if not self._project:
            return

        ch_path = self._project.chapters_dir(novel_slug) / f"{chapter_id}.md"
        ch_path.parent.mkdir(parents=True, exist_ok=True)
        ch_path.write_text(
            f'---\ntitle: "{chapter_id.replace("-", " ").title()}"\npublished: ""\n---\n\n# {chapter_id.replace("-", " ").title()}\n\nStart writing here.\n',
            encoding="utf-8",
        )

        # Also add to novel config arcs if possible
        config_path = self._project.novel_config_path(novel_slug)
        if config_path.exists():
            try:
                nc = NovelConfig.from_file(config_path)
                if nc.arcs:
                    nc.arcs[-1].chapters.append(
                        ArcChapter(id=chapter_id, title=chapter_id.replace("-", " ").title())
                    )
                    nc.save()
            except Exception:
                pass

        self._sidebar.load_project(self._project)
        self._on_sidebar_select("chapter", str(ch_path))
        self.statusBar().showMessage(f"Chapter '{chapter_id}' created")

    # ------------------------------------------------------------------
    # Build / preview
    # ------------------------------------------------------------------

    def _build_site(self, clean: bool = False) -> None:
        if not self._project or not self._generator:
            QMessageBox.warning(self, "No Project", "Open a project first.")
            return
        self._console.clear()
        self._console.appendPlainText("Starting build...")
        self._generator.build(clean=clean)
        self.statusBar().showMessage("Building...")

    def _on_build_finished(self, exit_code: int) -> None:
        if exit_code == 0:
            self._console.appendPlainText("\n=== Build completed successfully ===")
            self.statusBar().showMessage("Build completed")
        else:
            self._console.appendPlainText(f"\n=== Build failed (exit code {exit_code}) ===")
            self.statusBar().showMessage("Build failed")

    def _validate(self) -> None:
        if not self._project or not self._generator:
            QMessageBox.warning(self, "No Project", "Open a project first.")
            return
        self._console.clear()
        self._console.appendPlainText("Validating configuration...")
        self._generator.build(extra_flags=["--validate"])
        self.statusBar().showMessage("Validating...")

    def _generate_stats(self) -> None:
        if not self._project or not self._generator:
            QMessageBox.warning(self, "No Project", "Open a project first.")
            return
        self._console.clear()
        self._console.appendPlainText("Generating stats report...")
        self._generator.build(extra_flags=["--stats"])
        self.statusBar().showMessage("Generating stats...")

    def _check_links(self) -> None:
        if not self._project or not self._generator:
            QMessageBox.warning(self, "No Project", "Open a project first.")
            return
        self._console.clear()
        self._console.appendPlainText("Checking links...")
        self._generator.build(extra_flags=["--check-links"])
        self.statusBar().showMessage("Checking links...")

    def _check_accessibility(self) -> None:
        if not self._project or not self._generator:
            QMessageBox.warning(self, "No Project", "Open a project first.")
            return
        self._console.clear()
        self._console.appendPlainText("Checking accessibility...")
        self._generator.build(extra_flags=["--check-accessibility"])
        self.statusBar().showMessage("Checking accessibility...")

    def _preview_site(self) -> None:
        if not self._project:
            QMessageBox.warning(self, "No Project", "Open a project first.")
            return
        build_index = self._project.build_dir / "index.html"
        if not build_index.exists():
            QMessageBox.information(
                self, "No Build", "Build the site first before previewing."
            )
            return

        # Remove current widget, show preview
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            w.deleteLater()

        preview = SitePreview(self._project.build_dir)
        self._stack.addWidget(preview)
        self._stack.setCurrentWidget(preview)

    def _show_build_panel(self) -> None:
        if not self._project:
            QMessageBox.warning(self, "No Project", "Open a project first.")
            return
        self._on_sidebar_select("build", "")

    # ------------------------------------------------------------------
    # GitHub Publishing
    # ------------------------------------------------------------------

    def _publish_github(self) -> None:
        if not self._project:
            QMessageBox.warning(self, "No Project", "Open a project first.")
            return
        from app.widgets.github_dialog import GitHubDialog
        dialog = GitHubDialog(self._project.build_dir, self)
        dialog.exec()

    def _github_settings(self) -> None:
        if not self._project:
            QMessageBox.warning(self, "No Project", "Open a project first.")
            return
        from app.widgets.github_dialog import GitHubDialog
        dialog = GitHubDialog(self._project.build_dir, self)
        dialog.exec()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save_current(self) -> None:
        current = self._stack.currentWidget()
        if hasattr(current, "save"):
            current.save()
            self.statusBar().showMessage("Saved", 3000)

    # ------------------------------------------------------------------
    # Close guard
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        # Check for unsaved editors
        current = self._stack.currentWidget()
        if hasattr(current, "is_dirty") and current.is_dirty():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        if self._generator and self._generator.is_running:
            self._generator.stop()
        event.accept()

    # ------------------------------------------------------------------
    # About
    # ------------------------------------------------------------------

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Web Novel Studio",
            "Web Novel Studio\n\n"
            "A desktop app for managing and building\n"
            "static web novel sites.\n\n"
            "Powered by web-novel-static-generator.",
        )
