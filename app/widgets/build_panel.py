"""Build panel — build controls, dev server, validation, and console output."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
    QPushButton,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QSpinBox,
    QTabWidget,
)

from app.models.project import Project
from app.services.generator import GeneratorRunner


class BuildPanel(QWidget):
    """Build options, dev server, validation tools, and console output."""

    preview_requested = Signal()

    def __init__(self, project: Project, generator: GeneratorRunner | None, parent=None):
        super().__init__(parent)
        self._project = project
        self._generator = generator
        self._setup_ui()

        if self._generator:
            self._generator.output_line.connect(self._on_output)
            self._generator.started.connect(self._on_started)
            self._generator.finished.connect(self._on_finished)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel("<b>Build & Tools</b>")
        layout.addWidget(header)

        tabs = QTabWidget()

        # ===== Build Tab =====
        build_tab = QWidget()
        btl = QVBoxLayout(build_tab)

        opts = QGroupBox("Build Options")
        ol = QVBoxLayout(opts)
        self._clean = QCheckBox("Clean build (delete build/ first)")
        ol.addWidget(self._clean)
        self._include_drafts = QCheckBox("Include draft chapters")
        ol.addWidget(self._include_drafts)
        self._include_scheduled = QCheckBox("Include scheduled (future) chapters")
        ol.addWidget(self._include_scheduled)
        self._no_epub = QCheckBox("Skip EPUB generation (faster)")
        ol.addWidget(self._no_epub)
        self._optimize_images = QCheckBox("Optimize images (convert to WebP)")
        ol.addWidget(self._optimize_images)
        self._no_minify = QCheckBox("Skip minification (for debugging)")
        ol.addWidget(self._no_minify)
        btl.addWidget(opts)

        btn_row = QHBoxLayout()
        self._build_btn = QPushButton("Build")
        self._build_btn.setFixedHeight(40)
        self._build_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; background-color: #28a745; color: white;
                border: none; border-radius: 6px; padding: 0 20px;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:disabled { background-color: #999; }
        """)
        self._build_btn.clicked.connect(self._start_build)
        btn_row.addWidget(self._build_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setFixedHeight(40)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_build)
        btn_row.addWidget(self._stop_btn)

        self._preview_btn = QPushButton("Preview Site")
        self._preview_btn.setFixedHeight(40)
        self._preview_btn.clicked.connect(self.preview_requested)
        btn_row.addWidget(self._preview_btn)
        btl.addLayout(btn_row)

        tabs.addTab(build_tab, "Build")

        # ===== Dev Server Tab =====
        server_tab = QWidget()
        stl = QVBoxLayout(server_tab)

        server_group = QGroupBox("Development Server")
        sgl = QVBoxLayout(server_group)
        sgl.addWidget(QLabel(
            "Start a local dev server with live reload.\n"
            "Changes to content, templates, and static files will auto-rebuild."
        ))

        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Port:"))
        self._port = QSpinBox()
        self._port.setRange(1024, 65535)
        self._port.setValue(8000)
        port_row.addWidget(self._port)
        port_row.addStretch()
        sgl.addLayout(port_row)

        self._serve_drafts = QCheckBox("Include drafts")
        sgl.addWidget(self._serve_drafts)
        stl.addWidget(server_group)

        serve_btns = QHBoxLayout()
        self._serve_btn = QPushButton("Start Server")
        self._serve_btn.setFixedHeight(40)
        self._serve_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; background-color: #0078d4; color: white;
                border: none; border-radius: 6px; padding: 0 20px;
            }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:disabled { background-color: #999; }
        """)
        self._serve_btn.clicked.connect(self._start_serve)
        serve_btns.addWidget(self._serve_btn)

        self._stop_serve_btn = QPushButton("Stop Server")
        self._stop_serve_btn.setFixedHeight(40)
        self._stop_serve_btn.setEnabled(False)
        self._stop_serve_btn.clicked.connect(self._stop_build)
        serve_btns.addWidget(self._stop_serve_btn)
        stl.addLayout(serve_btns)

        # Watch-only mode
        watch_group = QGroupBox("Watch Mode (No Server)")
        wgl = QVBoxLayout(watch_group)
        wgl.addWidget(QLabel("Watch for file changes and rebuild automatically without a server."))
        self._watch_btn = QPushButton("Start Watching")
        self._watch_btn.clicked.connect(self._start_watch)
        wgl.addWidget(self._watch_btn)
        stl.addWidget(watch_group)

        stl.addStretch()
        tabs.addTab(server_tab, "Dev Server")

        # ===== Tools Tab =====
        tools_tab = QWidget()
        ttl = QVBoxLayout(tools_tab)

        validate_group = QGroupBox("Validation & Reports")
        vgl = QVBoxLayout(validate_group)

        self._validate_btn = QPushButton("Validate Config & Content")
        self._validate_btn.setToolTip("Check all config files and content for errors")
        self._validate_btn.clicked.connect(self._run_validate)
        vgl.addWidget(self._validate_btn)

        self._stats_btn = QPushButton("Generate Statistics Report")
        self._stats_btn.setToolTip("Generate stats_report.md with word counts, novel stats, etc.")
        self._stats_btn.clicked.connect(self._run_stats)
        vgl.addWidget(self._stats_btn)

        self._check_links_btn = QPushButton("Check for Broken Links")
        self._check_links_btn.setToolTip("Validate all internal links, images, and resources")
        self._check_links_btn.clicked.connect(self._run_check_links)
        vgl.addWidget(self._check_links_btn)

        self._check_a11y_btn = QPushButton("Check Accessibility")
        self._check_a11y_btn.setToolTip("Validate images have alt text and check accessibility")
        self._check_a11y_btn.clicked.connect(self._run_check_accessibility)
        vgl.addWidget(self._check_a11y_btn)

        ttl.addWidget(validate_group)
        ttl.addStretch()
        tabs.addTab(tools_tab, "Tools")

        layout.addWidget(tabs)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Console output
        console_group = QGroupBox("Output")
        cl = QVBoxLayout(console_group)
        self._console = QPlainTextEdit()
        self._console.setObjectName("buildConsole")
        self._console.setReadOnly(True)
        self._console.setMaximumBlockCount(5000)
        cl.addWidget(self._console)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self._console.clear)
        cl.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(console_group, stretch=1)

    # ------------------------------------------------------------------
    # Build actions
    # ------------------------------------------------------------------

    def _start_build(self) -> None:
        if not self._generator:
            return
        self._console.clear()
        self._generator.build(
            clean=self._clean.isChecked(),
            include_drafts=self._include_drafts.isChecked(),
            include_scheduled=self._include_scheduled.isChecked(),
            no_epub=self._no_epub.isChecked(),
            optimize_images=self._optimize_images.isChecked(),
            no_minify=self._no_minify.isChecked(),
        )

    def _start_serve(self) -> None:
        if not self._generator:
            return
        self._console.clear()
        flags = ["--serve", str(self._port.value())]
        if self._serve_drafts.isChecked():
            flags.append("--include-drafts")
        self._generator.build(extra_flags=flags)

    def _start_watch(self) -> None:
        if not self._generator:
            return
        self._console.clear()
        self._generator.build(extra_flags=["--watch"])

    def _stop_build(self) -> None:
        if self._generator:
            self._generator.stop()

    def _run_validate(self) -> None:
        if not self._generator:
            return
        self._console.clear()
        self._generator.build(extra_flags=["--validate"])

    def _run_stats(self) -> None:
        if not self._generator:
            return
        self._console.clear()
        self._generator.build(extra_flags=["--stats"])

    def _run_check_links(self) -> None:
        if not self._generator:
            return
        self._console.clear()
        self._generator.build(extra_flags=["--check-links"])

    def _run_check_accessibility(self) -> None:
        if not self._generator:
            return
        self._console.clear()
        self._generator.build(extra_flags=["--check-accessibility"])

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _on_started(self) -> None:
        self._build_btn.setEnabled(False)
        self._serve_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._stop_serve_btn.setEnabled(True)
        self._progress.setVisible(True)

    def _on_output(self, line: str) -> None:
        self._console.appendPlainText(line)

    def _on_finished(self, exit_code: int) -> None:
        self._build_btn.setEnabled(True)
        self._serve_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._stop_serve_btn.setEnabled(False)
        self._progress.setVisible(False)
        if exit_code == 0:
            self._console.appendPlainText("\n=== Completed successfully ===")
        else:
            self._console.appendPlainText(f"\n=== Failed (exit code {exit_code}) ===")
