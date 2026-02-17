"""Chapter/page editor — markdown editor with live preview (split pane)."""

from __future__ import annotations

from pathlib import Path

import yaml

from PySide6.QtCore import Qt, QTimer, QRegularExpression
from PySide6.QtGui import (
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QTextCursor,
    QPainter,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QSplitter,
    QGroupBox,
    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QPushButton,
    QLabel,
    QToolBar,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from app.models.project import Project
from app.models.chapter import Chapter
from app.utils.markdown_helper import render_markdown, wrap_html


# ------------------------------------------------------------------
# Markdown syntax highlighter
# ------------------------------------------------------------------

class MarkdownHighlighter(QSyntaxHighlighter):
    """Basic markdown syntax highlighter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []

        heading_fmt = QTextCharFormat()
        heading_fmt.setForeground(QColor("#0066cc"))
        heading_fmt.setFontWeight(QFont.Weight.Bold)
        self._rules.append((QRegularExpression(r"^#{1,6}\s.*$"), heading_fmt))

        bold_fmt = QTextCharFormat()
        bold_fmt.setFontWeight(QFont.Weight.Bold)
        self._rules.append((QRegularExpression(r"\*\*[^*]+\*\*"), bold_fmt))
        self._rules.append((QRegularExpression(r"__[^_]+__"), bold_fmt))

        italic_fmt = QTextCharFormat()
        italic_fmt.setFontItalic(True)
        self._rules.append((QRegularExpression(r"(?<!\*)\*(?!\*)[^*]+\*(?!\*)"), italic_fmt))
        self._rules.append((QRegularExpression(r"(?<!_)_(?!_)[^_]+_(?!_)"), italic_fmt))

        code_fmt = QTextCharFormat()
        code_fmt.setForeground(QColor("#c7254e"))
        code_fmt.setBackground(QColor("#f9f2f4"))
        code_fmt.setFontFamily("Consolas")
        self._rules.append((QRegularExpression(r"`[^`]+`"), code_fmt))

        link_fmt = QTextCharFormat()
        link_fmt.setForeground(QColor("#0066cc"))
        link_fmt.setFontUnderline(True)
        self._rules.append((QRegularExpression(r"\[([^\]]+)\]\([^\)]+\)"), link_fmt))

        img_fmt = QTextCharFormat()
        img_fmt.setForeground(QColor("#6a9955"))
        self._rules.append((QRegularExpression(r"!\[([^\]]*)\]\([^\)]+\)"), img_fmt))

        quote_fmt = QTextCharFormat()
        quote_fmt.setForeground(QColor("#666666"))
        self._rules.append((QRegularExpression(r"^>\s.*$"), quote_fmt))

        hr_fmt = QTextCharFormat()
        hr_fmt.setForeground(QColor("#999999"))
        self._rules.append((QRegularExpression(r"^(-{3,}|\*{3,}|_{3,})\s*$"), hr_fmt))

        list_fmt = QTextCharFormat()
        list_fmt.setForeground(QColor("#d63384"))
        self._rules.append((QRegularExpression(r"^\s*[-*+]\s"), list_fmt))
        self._rules.append((QRegularExpression(r"^\s*\d+\.\s"), list_fmt))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


# ------------------------------------------------------------------
# Line number area
# ------------------------------------------------------------------

class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return self._editor.line_number_area_size()

    def paintEvent(self, event):
        self._editor.line_number_area_paint(event)


class CodeEditor(QPlainTextEdit):
    """QPlainTextEdit with line numbers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_area_width)
        self.updateRequest.connect(self._update_line_area)
        self._update_line_area_width()

        font = QFont("Cascadia Code", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)

    def line_number_area_size(self):
        digits = max(1, len(str(self.blockCount())))
        return self.fontMetrics().horizontalAdvance("9") * (digits + 2) + 6

    def _update_line_area_width(self):
        self.setViewportMargins(self.line_number_area_size(), 0, 0, 0)

    def _update_line_area(self, rect, dy):
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(cr.left(), cr.top(), self.line_number_area_size(), cr.height())

    def line_number_area_paint(self, event):
        from PySide6.QtWidgets import QApplication
        dark = QApplication.instance().property("dark_mode") or False
        bg = QColor("#2d2d2d") if dark else QColor("#f0f0f0")
        fg = QColor("#858585") if dark else QColor("#999999")

        painter = QPainter(self._line_area)
        painter.fillRect(event.rect(), bg)
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(fg)
                painter.drawText(
                    0, top,
                    self._line_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
        painter.end()


# ------------------------------------------------------------------
# Chapter / Page Editor Widget
# ------------------------------------------------------------------

class ChapterEditor(QWidget):
    """Split-pane editor: front matter form + markdown editor + live preview.

    Works for both chapters and pages — pass is_page=True for page-specific fields.
    """

    def __init__(self, chapter_path: Path, project: Project, is_page: bool = False, parent=None):
        super().__init__(parent)
        self._project = project
        self._chapter = Chapter.from_file(chapter_path)
        self._is_page = is_page
        self._dirty = False
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(500)
        self._preview_timer.timeout.connect(self._update_preview)
        self._setup_ui()
        self._populate()

    def is_dirty(self) -> bool:
        return self._dirty

    def _mark_dirty(self) -> None:
        self._dirty = True
        self._preview_timer.start()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QHBoxLayout()
        kind = "Page" if self._is_page else "Chapter"
        self._title_label = QLabel(f"<b>{kind}: {self._chapter.path.name}</b>")
        header.addWidget(self._title_label)
        header.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self.save)
        header.addWidget(save_btn)
        outer.addLayout(header)

        # --- Front matter form (collapsible) ---
        fm_group = QGroupBox("Front Matter")
        fm_group.setCheckable(True)
        fm_group.setChecked(True)
        fm_scroll = QScrollArea()
        fm_scroll.setWidgetResizable(True)
        fm_scroll.setMaximumHeight(280)
        fm_widget = QWidget()
        fm_layout = QFormLayout(fm_widget)
        fm_layout.setContentsMargins(8, 4, 8, 4)

        # --- Common fields ---
        self._fm_title = QLineEdit()
        self._fm_title.textChanged.connect(self._mark_dirty)
        fm_layout.addRow("Title:", self._fm_title)

        if not self._is_page:
            # Chapter-specific: author, translator
            row1 = QHBoxLayout()
            self._fm_author = QLineEdit()
            self._fm_author.textChanged.connect(self._mark_dirty)
            row1.addWidget(QLabel("Author:"))
            row1.addWidget(self._fm_author)
            self._fm_translator = QLineEdit()
            self._fm_translator.textChanged.connect(self._mark_dirty)
            row1.addWidget(QLabel("Translator:"))
            row1.addWidget(self._fm_translator)
            fm_layout.addRow(row1)

        # Published + Tags
        row2 = QHBoxLayout()
        self._fm_published = QLineEdit()
        self._fm_published.setPlaceholderText("YYYY-MM-DD or YYYY-MM-DDThh:mm:ss-05:00")
        self._fm_published.textChanged.connect(self._mark_dirty)
        row2.addWidget(QLabel("Published:"))
        row2.addWidget(self._fm_published)
        self._fm_tags = QLineEdit()
        self._fm_tags.setPlaceholderText("tag1, tag2")
        self._fm_tags.textChanged.connect(self._mark_dirty)
        row2.addWidget(QLabel("Tags:"))
        row2.addWidget(self._fm_tags)
        fm_layout.addRow(row2)

        # Toggles row
        row3 = QHBoxLayout()
        self._fm_draft = QCheckBox("Draft")
        self._fm_draft.stateChanged.connect(self._mark_dirty)
        row3.addWidget(self._fm_draft)
        self._fm_hidden = QCheckBox("Hidden")
        self._fm_hidden.setToolTip("Accessible by direct link only, not shown in navigation")
        self._fm_hidden.stateChanged.connect(self._mark_dirty)
        row3.addWidget(self._fm_hidden)
        self._fm_comments = QCheckBox("Comments")
        self._fm_comments.setToolTip("Enable/disable comments for this content")
        self._fm_comments.stateChanged.connect(self._mark_dirty)
        row3.addWidget(self._fm_comments)
        fm_layout.addRow(row3)

        if not self._is_page:
            # Status dropdown
            status_row = QHBoxLayout()
            self._fm_status = QComboBox()
            self._fm_status.addItems(["", "draft", "review", "approved", "scheduled", "published"])
            self._fm_status.currentTextChanged.connect(self._mark_dirty)
            status_row.addWidget(QLabel("Status:"))
            status_row.addWidget(self._fm_status)

            self._fm_reviewers = QLineEdit()
            self._fm_reviewers.setPlaceholderText("reviewer1, reviewer2")
            self._fm_reviewers.textChanged.connect(self._mark_dirty)
            status_row.addWidget(QLabel("Reviewers:"))
            status_row.addWidget(self._fm_reviewers)
            fm_layout.addRow(status_row)

            # Contributors
            self._fm_contributors = QTextEdit()
            self._fm_contributors.setPlaceholderText(
                "YAML list, e.g.:\n"
                "- name: Author Name\n"
                "  role: author\n"
                "- name: Editor Name\n"
                "  role: editor"
            )
            self._fm_contributors.setMaximumHeight(70)
            self._fm_contributors.textChanged.connect(self._mark_dirty)
            fm_layout.addRow("Contributors:", self._fm_contributors)

        # Password
        row4 = QHBoxLayout()
        self._fm_password = QLineEdit()
        self._fm_password.setPlaceholderText("Password (optional)")
        self._fm_password.textChanged.connect(self._mark_dirty)
        row4.addWidget(QLabel("Password:"))
        row4.addWidget(self._fm_password)
        self._fm_password_hint = QLineEdit()
        self._fm_password_hint.setPlaceholderText("Password hint")
        self._fm_password_hint.textChanged.connect(self._mark_dirty)
        row4.addWidget(QLabel("Hint:"))
        row4.addWidget(self._fm_password_hint)
        fm_layout.addRow(row4)

        if not self._is_page:
            # Chapter-specific: translation notes and commentary
            self._fm_notes = QLineEdit()
            self._fm_notes.setPlaceholderText("Translation notes (cultural context, etc.)")
            self._fm_notes.textChanged.connect(self._mark_dirty)
            fm_layout.addRow("Translation Notes:", self._fm_notes)

            self._fm_commentary = QTextEdit()
            self._fm_commentary.setPlaceholderText("Extended translator commentary (shown at chapter end)")
            self._fm_commentary.setMaximumHeight(60)
            self._fm_commentary.textChanged.connect(self._mark_dirty)
            fm_layout.addRow("Commentary:", self._fm_commentary)

        # Social embeds
        social_row = QHBoxLayout()
        self._fm_social_image = QLineEdit()
        self._fm_social_image.setPlaceholderText("/static/images/social.jpg")
        self._fm_social_image.textChanged.connect(self._mark_dirty)
        social_row.addWidget(QLabel("Social Image:"))
        social_row.addWidget(self._fm_social_image)
        self._fm_social_desc = QLineEdit()
        self._fm_social_desc.setPlaceholderText("Social media description")
        self._fm_social_desc.textChanged.connect(self._mark_dirty)
        social_row.addWidget(QLabel("Social Desc:"))
        social_row.addWidget(self._fm_social_desc)
        fm_layout.addRow(social_row)

        # SEO
        seo_row = QHBoxLayout()
        self._fm_seo_index = QCheckBox("Allow Indexing")
        self._fm_seo_index.stateChanged.connect(self._mark_dirty)
        seo_row.addWidget(self._fm_seo_index)
        self._fm_seo_desc = QLineEdit()
        self._fm_seo_desc.setPlaceholderText("SEO meta description")
        self._fm_seo_desc.textChanged.connect(self._mark_dirty)
        seo_row.addWidget(QLabel("Meta Desc:"))
        seo_row.addWidget(self._fm_seo_desc)
        fm_layout.addRow(seo_row)

        if self._is_page:
            # Page-specific fields
            page_row = QHBoxLayout()
            self._fm_navigation = QComboBox()
            self._fm_navigation.addItems(["", "header", "footer"])
            self._fm_navigation.currentTextChanged.connect(self._mark_dirty)
            page_row.addWidget(QLabel("Navigation:"))
            page_row.addWidget(self._fm_navigation)
            self._fm_nav_order = QSpinBox()
            self._fm_nav_order.setRange(0, 999)
            self._fm_nav_order.valueChanged.connect(self._mark_dirty)
            page_row.addWidget(QLabel("Nav Order:"))
            page_row.addWidget(self._fm_nav_order)
            self._fm_parent = QLineEdit()
            self._fm_parent.setPlaceholderText("Parent page slug")
            self._fm_parent.textChanged.connect(self._mark_dirty)
            page_row.addWidget(QLabel("Parent:"))
            page_row.addWidget(self._fm_parent)
            fm_layout.addRow(page_row)

            self._fm_description = QLineEdit()
            self._fm_description.setPlaceholderText("Page description")
            self._fm_description.textChanged.connect(self._mark_dirty)
            fm_layout.addRow("Description:", self._fm_description)

        fm_scroll.setWidget(fm_widget)
        fm_group_layout = QVBoxLayout(fm_group)
        fm_group_layout.setContentsMargins(0, 0, 0, 0)
        fm_group_layout.addWidget(fm_scroll)
        outer.addWidget(fm_group)

        # --- Toolbar ---
        toolbar = QToolBar()
        toolbar.addAction("B", self._insert_bold)
        toolbar.addAction("I", self._insert_italic)
        toolbar.addAction("H", self._insert_heading)
        toolbar.addAction("Link", self._insert_link)
        toolbar.addAction("Img", self._insert_image)
        toolbar.addSeparator()
        toolbar.addAction("Code", self._insert_code)
        toolbar.addAction("Quote", self._insert_quote)
        outer.addWidget(toolbar)

        # --- Split: editor | preview ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._editor = CodeEditor()
        self._editor.textChanged.connect(self._mark_dirty)
        self._highlighter = MarkdownHighlighter(self._editor.document())
        splitter.addWidget(self._editor)

        self._preview = QWebEngineView()
        splitter.addWidget(self._preview)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, stretch=1)

    # ------------------------------------------------------------------
    # Populate
    # ------------------------------------------------------------------

    def _populate(self) -> None:
        fm = self._chapter.front_matter
        self._fm_title.setText(fm.get("title", ""))

        if not self._is_page:
            self._fm_author.setText(fm.get("author", ""))
            self._fm_translator.setText(fm.get("translator", ""))

        self._fm_published.setText(str(fm.get("published", "")))
        self._fm_tags.setText(", ".join(fm.get("tags", [])))
        self._fm_draft.setChecked(fm.get("draft", False))
        self._fm_hidden.setChecked(fm.get("hidden", False))

        # Comments — can be True, False, or absent
        comments_val = fm.get("comments")
        if comments_val is None:
            self._fm_comments.setChecked(True)  # default on
        else:
            self._fm_comments.setChecked(bool(comments_val))

        self._fm_password.setText(str(fm.get("password", "")))
        self._fm_password_hint.setText(fm.get("password_hint", ""))

        if not self._is_page:
            # Status / reviewers / contributors
            status_val = fm.get("status", "")
            idx = self._fm_status.findText(status_val)
            if idx >= 0:
                self._fm_status.setCurrentIndex(idx)
            reviewers = fm.get("reviewers", [])
            if isinstance(reviewers, list):
                self._fm_reviewers.setText(", ".join(reviewers))
            else:
                self._fm_reviewers.setText(str(reviewers))
            contributors = fm.get("contributors", [])
            if contributors:
                self._fm_contributors.setPlainText(
                    yaml.dump(contributors, default_flow_style=False, allow_unicode=True).strip()
                )
            else:
                self._fm_contributors.setPlainText("")

            self._fm_notes.setText(fm.get("translation_notes", ""))
            self._fm_commentary.setPlainText(fm.get("translator_commentary", ""))

        # Social embeds
        se = fm.get("social_embeds", {})
        self._fm_social_image.setText(se.get("image", ""))
        self._fm_social_desc.setText(se.get("description", ""))

        # SEO
        seo = fm.get("seo", {})
        self._fm_seo_index.setChecked(seo.get("allow_indexing", True))
        self._fm_seo_desc.setText(seo.get("meta_description", ""))

        if self._is_page:
            nav = fm.get("navigation", "")
            idx = self._fm_navigation.findText(nav)
            if idx >= 0:
                self._fm_navigation.setCurrentIndex(idx)
            self._fm_nav_order.setValue(fm.get("nav_order", 0))
            self._fm_parent.setText(fm.get("parent", ""))
            self._fm_description.setText(fm.get("description", ""))

        self._editor.setPlainText(self._chapter.body)
        self._dirty = False
        self._update_preview()

    def _update_preview(self) -> None:
        md_text = self._editor.toPlainText()
        html_body = render_markdown(md_text)
        from PySide6.QtWidgets import QApplication
        dark = QApplication.instance().property("dark_mode") or False
        full_html = wrap_html(html_body, dark=dark)
        self._preview.setHtml(full_html)

    # ------------------------------------------------------------------
    # Toolbar actions
    # ------------------------------------------------------------------

    def _wrap_selection(self, before: str, after: str) -> None:
        cursor = self._editor.textCursor()
        selected = cursor.selectedText()
        cursor.insertText(f"{before}{selected}{after}")
        self._editor.setTextCursor(cursor)

    def _insert_bold(self) -> None:
        self._wrap_selection("**", "**")

    def _insert_italic(self) -> None:
        self._wrap_selection("*", "*")

    def _insert_heading(self) -> None:
        cursor = self._editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText("## ")
        self._editor.setTextCursor(cursor)

    def _insert_link(self) -> None:
        cursor = self._editor.textCursor()
        selected = cursor.selectedText() or "text"
        cursor.insertText(f"[{selected}](url)")
        self._editor.setTextCursor(cursor)

    def _insert_image(self) -> None:
        cursor = self._editor.textCursor()
        cursor.insertText("![alt text](image.jpg)")
        self._editor.setTextCursor(cursor)

    def _insert_code(self) -> None:
        cursor = self._editor.textCursor()
        selected = cursor.selectedText()
        if "\n" in selected or not selected:
            cursor.insertText(f"```\n{selected}\n```")
        else:
            cursor.insertText(f"`{selected}`")
        self._editor.setTextCursor(cursor)

    def _insert_quote(self) -> None:
        cursor = self._editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText("> ")
        self._editor.setTextCursor(cursor)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _set_or_remove(self, fm: dict, key: str, value) -> None:
        """Set a key in fm if value is truthy, otherwise remove it."""
        if value:
            fm[key] = value
        else:
            fm.pop(key, None)

    def save(self) -> None:
        fm = dict(self._chapter.front_matter)
        fm["title"] = self._fm_title.text()

        if not self._is_page:
            self._set_or_remove(fm, "author", self._fm_author.text())
            self._set_or_remove(fm, "translator", self._fm_translator.text())

        self._set_or_remove(fm, "published", self._fm_published.text())

        tags_text = self._fm_tags.text()
        if tags_text.strip():
            fm["tags"] = [t.strip() for t in tags_text.split(",") if t.strip()]
        else:
            fm.pop("tags", None)

        if self._fm_draft.isChecked():
            fm["draft"] = True
        else:
            fm.pop("draft", None)

        if self._fm_hidden.isChecked():
            fm["hidden"] = True
        else:
            fm.pop("hidden", None)

        # Comments: only write if explicitly toggled off
        if not self._fm_comments.isChecked():
            fm["comments"] = False
        else:
            # If it was explicitly set before, keep it; otherwise remove
            if "comments" in fm and fm["comments"] is False:
                fm["comments"] = True

        self._set_or_remove(fm, "password", self._fm_password.text())
        self._set_or_remove(fm, "password_hint", self._fm_password_hint.text())

        if not self._is_page:
            # Status / reviewers / contributors
            self._set_or_remove(fm, "status", self._fm_status.currentText())

            reviewers_text = self._fm_reviewers.text().strip()
            if reviewers_text:
                fm["reviewers"] = [r.strip() for r in reviewers_text.split(",") if r.strip()]
            else:
                fm.pop("reviewers", None)

            contributors_text = self._fm_contributors.toPlainText().strip()
            if contributors_text:
                try:
                    parsed = yaml.safe_load(contributors_text)
                    if isinstance(parsed, list):
                        fm["contributors"] = parsed
                except yaml.YAMLError:
                    pass  # Keep existing value if YAML is invalid
            else:
                fm.pop("contributors", None)

            self._set_or_remove(fm, "translation_notes", self._fm_notes.text())
            self._set_or_remove(fm, "translator_commentary", self._fm_commentary.toPlainText())

        # Social embeds
        social_image = self._fm_social_image.text()
        social_desc = self._fm_social_desc.text()
        if social_image or social_desc:
            se = fm.get("social_embeds", {})
            if social_image:
                se["image"] = social_image
            if social_desc:
                se["description"] = social_desc
            fm["social_embeds"] = se
        else:
            fm.pop("social_embeds", None)

        # SEO
        seo_desc = self._fm_seo_desc.text()
        seo_index = self._fm_seo_index.isChecked()
        if seo_desc or not seo_index:
            seo = {}
            seo["allow_indexing"] = seo_index
            if seo_desc:
                seo["meta_description"] = seo_desc
            fm["seo"] = seo
        else:
            fm.pop("seo", None)

        if self._is_page:
            nav = self._fm_navigation.currentText()
            self._set_or_remove(fm, "navigation", nav)
            nav_order = self._fm_nav_order.value()
            if nav_order > 0:
                fm["nav_order"] = nav_order
            else:
                fm.pop("nav_order", None)
            self._set_or_remove(fm, "parent", self._fm_parent.text())
            self._set_or_remove(fm, "description", self._fm_description.text())

        self._chapter.front_matter = fm
        self._chapter.body = self._editor.toPlainText()

        try:
            self._chapter.save()
            self._dirty = False
            kind = "Page" if self._is_page else "Chapter"
            self.window().statusBar().showMessage(f"{kind} saved", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
