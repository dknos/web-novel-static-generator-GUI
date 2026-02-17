"""GitHub publishing service — push built site to GitHub Pages."""

from __future__ import annotations

import json
import subprocess
import shutil
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal


# Settings file for GitHub config
SETTINGS_DIR = Path.home() / ".web-novel-app"
GITHUB_SETTINGS_FILE = SETTINGS_DIR / "github.json"


def load_github_settings() -> dict[str, Any]:
    """Load saved GitHub settings."""
    if not GITHUB_SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(GITHUB_SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_github_settings(settings: dict[str, Any]) -> None:
    """Save GitHub settings to disk."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    GITHUB_SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2), encoding="utf-8"
    )


class PublishWorker(QObject):
    """Worker that runs git operations in a background thread."""

    output = Signal(str)
    finished = Signal(bool, str)  # (success, message)

    def __init__(
        self,
        build_dir: Path,
        token: str,
        repo: str,
        branch: str = "main",
        cname: str = "",
        commit_message: str = "Deploy site update",
    ):
        super().__init__()
        self._build_dir = build_dir
        self._token = token
        self._repo = repo
        self._branch = branch
        self._cname = cname
        self._commit_message = commit_message

    def run(self) -> None:
        try:
            self._publish()
        except Exception as e:
            self.finished.emit(False, str(e))

    def _run_git(self, args: list[str], cwd: Path) -> str:
        """Run a git command and return output."""
        cmd = ["git"] + args
        # Mask token in output
        display_cmd = " ".join(args).replace(self._token, "***")
        self.output.emit(f"$ git {display_cmd}")

        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.stdout.strip():
            # Mask token in any output
            safe_out = result.stdout.replace(self._token, "***")
            self.output.emit(safe_out.strip())
        if result.returncode != 0:
            safe_err = result.stderr.replace(self._token, "***")
            if safe_err.strip():
                self.output.emit(f"ERROR: {safe_err.strip()}")
            raise RuntimeError(f"git {display_cmd} failed: {safe_err.strip()}")
        return result.stdout.strip()

    def _publish(self) -> None:
        build = self._build_dir
        if not build.exists() or not (build / "index.html").exists():
            self.finished.emit(False, "No build found. Build the site first.")
            return

        self.output.emit("Preparing to publish to GitHub Pages...")
        self.output.emit(f"Repository: {self._repo}")
        self.output.emit(f"Branch: {self._branch}")

        # Create a temp directory for the git repo
        tmp = build.parent / "_deploy_tmp"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir()

        try:
            # Init git repo
            self._run_git(["init"], tmp)
            self._run_git(["checkout", "-b", self._branch], tmp)

            # Copy build contents to temp dir
            self.output.emit("Copying build files...")
            for item in build.iterdir():
                dest = tmp / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)

            # Add CNAME if configured
            if self._cname:
                (tmp / "CNAME").write_text(self._cname, encoding="utf-8")
                self.output.emit(f"Added CNAME: {self._cname}")

            # Add .nojekyll to skip Jekyll processing
            (tmp / ".nojekyll").write_text("", encoding="utf-8")

            # Configure git
            self._run_git(["config", "user.email", "web-novel-studio@users.noreply.github.com"], tmp)
            self._run_git(["config", "user.name", "Web Novel Studio"], tmp)

            # Add and commit
            self._run_git(["add", "-A"], tmp)
            self._run_git(["commit", "-m", self._commit_message], tmp)

            # Push to remote
            remote_url = f"https://x-access-token:{self._token}@github.com/{self._repo}.git"
            self._run_git(["remote", "add", "origin", remote_url], tmp)
            self._run_git(["push", "--force", "origin", self._branch], tmp)

            self.output.emit("")
            self.output.emit("=== Published successfully! ===")
            self.output.emit(f"Site will be available at: https://{self._repo.split('/')[0]}.github.io/{self._repo.split('/')[1]}/")
            if self._cname:
                self.output.emit(f"Custom domain: https://{self._cname}/")

            self.finished.emit(True, "Published successfully!")
        finally:
            # Clean up temp dir
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)


class GitHubPublisher(QObject):
    """Manages GitHub publishing from the GUI."""

    output_line = Signal(str)
    publish_started = Signal()
    publish_finished = Signal(bool, str)  # (success, message)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: PublishWorker | None = None

    @property
    def is_publishing(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def publish(
        self,
        build_dir: Path,
        token: str,
        repo: str,
        branch: str = "main",
        cname: str = "",
        commit_message: str = "Deploy site update",
    ) -> None:
        if self.is_publishing:
            return

        self._worker = PublishWorker(
            build_dir=build_dir,
            token=token,
            repo=repo,
            branch=branch,
            cname=cname,
            commit_message=commit_message,
        )
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.output.connect(self.output_line.emit)
        self._worker.finished.connect(self._on_finished)

        self.publish_started.emit()
        self._thread.start()

    def _on_finished(self, success: bool, message: str) -> None:
        self.publish_finished.emit(success, message)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        self._worker = None
