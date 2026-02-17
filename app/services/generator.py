"""Generator service — wraps generate.py subprocess calls."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal


class GeneratorRunner(QObject):
    """Runs generate.py as a subprocess, emitting signals for output."""

    output_line = Signal(str)       # Each line of stdout/stderr
    finished = Signal(int)          # Exit code
    started = Signal()

    def __init__(self, project_root: Path, parent: QObject | None = None):
        super().__init__(parent)
        self._project_root = project_root
        self._process: QProcess | None = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning

    def build(
        self,
        *,
        clean: bool = False,
        include_drafts: bool = False,
        include_scheduled: bool = False,
        no_epub: bool = False,
        optimize_images: bool = False,
        no_minify: bool = False,
        extra_flags: list[str] | None = None,
    ) -> None:
        """Start a build of the site."""
        if self.is_running:
            return

        args: list[str] = [str(self._project_root / "generate.py")]
        if clean:
            args.append("--clean")
        if include_drafts:
            args.append("--include-drafts")
        if include_scheduled:
            args.append("--include-scheduled")
        if no_epub:
            args.append("--no-epub")
        if optimize_images:
            args.append("--optimize-images")
        if no_minify:
            args.append("--no-minify")
        if extra_flags:
            args.extend(extra_flags)

        self._run(args)

    def serve(self, port: int = 8000) -> None:
        """Start the dev server."""
        if self.is_running:
            return
        args = [str(self._project_root / "generate.py"), "--serve", str(port)]
        self._run(args)

    def stop(self) -> None:
        """Kill a running process."""
        if self._process and self.is_running:
            self._process.kill()

    # ------------------------------------------------------------------

    def _run(self, args: list[str]) -> None:
        self._process = QProcess(self)
        self._process.setWorkingDirectory(str(self._project_root))
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_output)
        self._process.finished.connect(self._on_finished)

        python = sys.executable
        self._process.start(python, args)
        self.started.emit()

    def _on_output(self) -> None:
        if self._process is None:
            return
        data = self._process.readAllStandardOutput().data()
        text = data.decode("utf-8", errors="replace")
        for line in text.splitlines():
            self.output_line.emit(line)

    def _on_finished(self, exit_code: int, _status: QProcess.ExitStatus) -> None:
        self.finished.emit(exit_code)
