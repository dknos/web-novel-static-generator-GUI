"""Web Novel Desktop App — Entry Point."""

import sys
import os

# Ensure the app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPalette, QColor


from app.main_window import MainWindow


def _is_windows_dark_mode() -> bool:
    """Detect whether Windows is set to dark mode via registry."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False


def _dark_palette() -> QPalette:
    """Create a dark QPalette."""
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(45, 45, 45))
    p.setColor(QPalette.ColorRole.WindowText, QColor(212, 212, 212))
    p.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(50, 50, 50))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(212, 212, 212))
    p.setColor(QPalette.ColorRole.Text, QColor(212, 212, 212))
    p.setColor(QPalette.ColorRole.Button, QColor(55, 55, 55))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(212, 212, 212))
    p.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.Link, QColor(86, 156, 214))
    p.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 212))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(128, 128, 128))

    # Disabled colors
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(128, 128, 128))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(128, 128, 128))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(128, 128, 128))
    return p


def _base_stylesheet(dark: bool) -> str:
    if dark:
        return """
            QMainWindow {
                font-family: "Segoe UI", sans-serif;
            }
            QTreeWidget {
                font-size: 13px;
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            QPlainTextEdit#buildConsole {
                font-family: "Cascadia Code", "Consolas", monospace;
                font-size: 12px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
                color: #d4d4d4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 3px 6px;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #0078d4;
            }
            QScrollArea {
                border: none;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #333;
            }
            QListWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: #d4d4d4;
            }
            QMenuBar::item:selected {
                background-color: #094771;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QToolBar {
                background-color: #2d2d2d;
                border: none;
                spacing: 4px;
            }
            QDockWidget {
                color: #d4d4d4;
            }
            QDockWidget::title {
                background-color: #2d2d2d;
                padding: 4px;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
            QCheckBox {
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
            }
            QSplitter::handle {
                background-color: #3c3c3c;
            }
        """
    else:
        return """
            QMainWindow {
                font-family: "Segoe UI", sans-serif;
            }
            QTreeWidget {
                font-size: 13px;
            }
            QPlainTextEdit#buildConsole {
                font-family: "Cascadia Code", "Consolas", monospace;
                font-size: 12px;
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QStatusBar {
                background-color: #0078d4;
                color: white;
            }
        """


def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Web Novel Studio")
    app.setOrganizationName("WebNovelStudio")
    app.setApplicationDisplayName("Web Novel Studio")

    # Use Fusion style for cross-platform consistency
    app.setStyle(QStyleFactory.create("Fusion"))

    # Detect dark mode and apply theme
    dark = _is_windows_dark_mode()
    if dark:
        app.setPalette(_dark_palette())
    app.setStyleSheet(_base_stylesheet(dark))

    # Store theme flag for widgets that need it
    app.setProperty("dark_mode", dark)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
