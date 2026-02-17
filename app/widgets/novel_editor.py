"""Novel config editor — form for per-novel config.yaml with all settings."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QScrollArea,
    QGroupBox,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QInputDialog,
)

from app.models.project import Project
from app.models.novel import NovelConfig, Arc, ArcChapter


class NovelEditor(QWidget):
    """Form editor for a novel's config.yaml with all documented settings."""

    def __init__(self, config_path: Path, project: Project, parent=None):
        super().__init__(parent)
        self._config_path = config_path
        self._project = project
        self._novel = NovelConfig.from_file(config_path)
        self._dirty = False
        self._setup_ui()
        self._populate()

    def is_dirty(self) -> bool:
        return self._dirty

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel("<b>Novel Configuration</b>"))
        header.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self.save)
        header.addWidget(save_btn)
        outer.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        fl = QVBoxLayout(form_widget)
        fl.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Basic Info ---
        basic = QGroupBox("Basic Information")
        bl = QFormLayout(basic)
        self._title = QLineEdit()
        self._title.textChanged.connect(self._mark_dirty)
        bl.addRow("Title:", self._title)
        self._slug = QLineEdit()
        self._slug.textChanged.connect(self._mark_dirty)
        bl.addRow("Slug:", self._slug)
        self._description = QTextEdit()
        self._description.setMaximumHeight(80)
        self._description.textChanged.connect(self._mark_dirty)
        bl.addRow("Description:", self._description)
        self._status = QComboBox()
        self._status.addItems(["ongoing", "complete", "hiatus"])
        self._status.currentTextChanged.connect(self._mark_dirty)
        bl.addRow("Status:", self._status)
        self._primary_lang = QLineEdit()
        self._primary_lang.textChanged.connect(self._mark_dirty)
        bl.addRow("Primary Language:", self._primary_lang)
        self._chapter_type = QComboBox()
        self._chapter_type.addItems(["", "manga"])
        self._chapter_type.setToolTip("Leave empty for text novels, 'manga' for comic/manga")
        self._chapter_type.currentTextChanged.connect(self._mark_dirty)
        bl.addRow("Chapter Type:", self._chapter_type)
        fl.addWidget(basic)

        # --- Tags ---
        tags_group = QGroupBox("Tags")
        tl = QFormLayout(tags_group)
        self._tags = QLineEdit()
        self._tags.setPlaceholderText("fantasy, adventure, magic (comma separated)")
        self._tags.textChanged.connect(self._mark_dirty)
        tl.addRow("Genre Tags:", self._tags)
        fl.addWidget(tags_group)

        # --- Cover & Author ---
        cover = QGroupBox("Cover & Author")
        cvl = QFormLayout(cover)
        cover_row = QHBoxLayout()
        self._cover_art = QLineEdit()
        self._cover_art.textChanged.connect(self._mark_dirty)
        cover_row.addWidget(self._cover_art)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_cover)
        cover_row.addWidget(browse_btn)
        cvl.addRow("Cover Art:", cover_row)
        self._show_front = QCheckBox("Show on front page")
        self._show_front.stateChanged.connect(self._mark_dirty)
        cvl.addRow(self._show_front)
        self._author_name = QLineEdit()
        self._author_name.textChanged.connect(self._mark_dirty)
        cvl.addRow("Author Name:", self._author_name)
        self._copyright = QLineEdit()
        self._copyright.textChanged.connect(self._mark_dirty)
        cvl.addRow("Copyright:", self._copyright)
        fl.addWidget(cover)

        # --- Languages ---
        lang = QGroupBox("Languages")
        ll = QFormLayout(lang)
        self._lang_default = QLineEdit()
        self._lang_default.textChanged.connect(self._mark_dirty)
        ll.addRow("Default:", self._lang_default)
        self._lang_available = QLineEdit()
        self._lang_available.setPlaceholderText("en, jp")
        self._lang_available.textChanged.connect(self._mark_dirty)
        ll.addRow("Available:", self._lang_available)
        fl.addWidget(lang)

        # --- Length Display ---
        ld = QGroupBox("Length Display")
        ldl = QFormLayout(ld)
        self._length_unit = QComboBox()
        self._length_unit.addItems(["words", "characters"])
        self._length_unit.currentTextChanged.connect(self._mark_dirty)
        ldl.addRow("Default Unit:", self._length_unit)
        self._length_overrides = QLineEdit()
        self._length_overrides.setPlaceholderText("en:words, jp:characters")
        self._length_overrides.textChanged.connect(self._mark_dirty)
        ldl.addRow("Language Overrides:", self._length_overrides)
        fl.addWidget(ld)

        # --- Display Settings ---
        disp = QGroupBox("Display Settings")
        dl = QFormLayout(disp)
        self._show_tags = QCheckBox("Show tags on chapters")
        self._show_tags.stateChanged.connect(self._mark_dirty)
        dl.addRow(self._show_tags)
        self._show_metadata = QCheckBox("Show metadata")
        self._show_metadata.stateChanged.connect(self._mark_dirty)
        dl.addRow(self._show_metadata)
        self._show_tn = QCheckBox("Show translation notes")
        self._show_tn.stateChanged.connect(self._mark_dirty)
        dl.addRow(self._show_tn)
        self._show_tags_link = QCheckBox("Show tags navigation link")
        self._show_tags_link.stateChanged.connect(self._mark_dirty)
        dl.addRow(self._show_tags_link)
        fl.addWidget(disp)

        # --- Social Embeds ---
        se_group = QGroupBox("Social Embeds")
        sel = QFormLayout(se_group)
        self._se_image = QLineEdit()
        self._se_image.textChanged.connect(self._mark_dirty)
        sel.addRow("Image:", self._se_image)
        self._se_desc = QLineEdit()
        self._se_desc.textChanged.connect(self._mark_dirty)
        sel.addRow("Description:", self._se_desc)
        self._se_keywords = QLineEdit()
        self._se_keywords.setPlaceholderText("keyword1, keyword2")
        self._se_keywords.textChanged.connect(self._mark_dirty)
        sel.addRow("Keywords:", self._se_keywords)
        fl.addWidget(se_group)

        # --- SEO ---
        seo_group = QGroupBox("SEO")
        seol = QFormLayout(seo_group)
        self._seo_index = QCheckBox("Allow indexing")
        self._seo_index.stateChanged.connect(self._mark_dirty)
        seol.addRow(self._seo_index)
        self._seo_desc = QLineEdit()
        self._seo_desc.textChanged.connect(self._mark_dirty)
        seol.addRow("Meta Description:", self._seo_desc)
        fl.addWidget(seo_group)

        # --- Feature Toggles ---
        toggles = QGroupBox("Features")
        tgl = QFormLayout(toggles)
        self._epub = QCheckBox("EPUB generation")
        self._epub.stateChanged.connect(self._mark_dirty)
        tgl.addRow(self._epub)
        self._epub_arcs = QCheckBox("Include arc downloads")
        self._epub_arcs.stateChanged.connect(self._mark_dirty)
        tgl.addRow(self._epub_arcs)
        self._comments = QCheckBox("Comments enabled")
        self._comments.stateChanged.connect(self._mark_dirty)
        tgl.addRow(self._comments)
        self._comments_toc = QCheckBox("TOC comments")
        self._comments_toc.stateChanged.connect(self._mark_dirty)
        tgl.addRow(self._comments_toc)
        self._comments_chapter = QCheckBox("Chapter comments")
        self._comments_chapter.stateChanged.connect(self._mark_dirty)
        tgl.addRow(self._comments_chapter)
        fl.addWidget(toggles)

        # --- New Chapter Tags ---
        nct = QGroupBox("New Chapter Tags (Override)")
        ncl = QFormLayout(nct)
        self._nct_enabled = QCheckBox("Enable (NEW!) tags for this story")
        self._nct_enabled.stateChanged.connect(self._mark_dirty)
        ncl.addRow(self._nct_enabled)
        self._nct_days = QSpinBox()
        self._nct_days.setRange(1, 365)
        self._nct_days.valueChanged.connect(self._mark_dirty)
        ncl.addRow("Threshold (days):", self._nct_days)
        fl.addWidget(nct)

        # --- Manga Settings ---
        manga = QGroupBox("Manga Settings")
        mgl = QFormLayout(manga)
        self._reading_dir = QComboBox()
        self._reading_dir.addItems(["ltr", "rtl"])
        self._reading_dir.currentTextChanged.connect(self._mark_dirty)
        mgl.addRow("Reading Direction:", self._reading_dir)
        self._view_mode = QComboBox()
        self._view_mode.addItems(["single", "double", "scroll", "scroll_double"])
        self._view_mode.currentTextChanged.connect(self._mark_dirty)
        mgl.addRow("Default View Mode:", self._view_mode)
        self._cover_separate = QCheckBox("First page is cover (shown separately)")
        self._cover_separate.stateChanged.connect(self._mark_dirty)
        mgl.addRow(self._cover_separate)
        self._skip_compression = QCheckBox("Skip image compression")
        self._skip_compression.stateChanged.connect(self._mark_dirty)
        mgl.addRow(self._skip_compression)
        fl.addWidget(manga)

        # --- Story Metadata ---
        meta = QGroupBox("Story Metadata")
        mel = QFormLayout(meta)
        self._update_schedule = QLineEdit()
        self._update_schedule.setPlaceholderText("e.g. Weekly on Sundays")
        self._update_schedule.textChanged.connect(self._mark_dirty)
        mel.addRow("Update Schedule:", self._update_schedule)
        self._license = QComboBox()
        self._license.setEditable(True)
        self._license.addItems(["Copyrighted", "CC0", "Public Domain", "CC BY", "CC BY-SA"])
        self._license.currentTextChanged.connect(self._mark_dirty)
        mel.addRow("License:", self._license)
        fl.addWidget(meta)

        # --- Footer ---
        footer = QGroupBox("Footer (Override)")
        ftl = QFormLayout(footer)
        self._footer_text = QLineEdit()
        self._footer_text.textChanged.connect(self._mark_dirty)
        ftl.addRow("Custom Footer:", self._footer_text)
        self._footer_links = QTextEdit()
        self._footer_links.setMaximumHeight(80)
        self._footer_links.setPlaceholderText("One per line: text | url")
        self._footer_links.textChanged.connect(self._mark_dirty)
        ftl.addRow("Footer Links:", self._footer_links)
        fl.addWidget(footer)

        # --- Arcs ---
        arcs_group = QGroupBox("Arcs & Chapters")
        al = QVBoxLayout(arcs_group)
        self._arcs_list = QListWidget()
        self._arcs_list.setMaximumHeight(250)
        al.addWidget(self._arcs_list)

        arc_btns = QHBoxLayout()
        add_arc_btn = QPushButton("Add Arc")
        add_arc_btn.clicked.connect(self._add_arc)
        arc_btns.addWidget(add_arc_btn)
        add_ch_btn = QPushButton("Add Chapter to Arc")
        add_ch_btn.clicked.connect(self._add_chapter_to_arc)
        arc_btns.addWidget(add_ch_btn)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_arc_item)
        arc_btns.addWidget(remove_btn)
        move_up_btn = QPushButton("Move Up")
        move_up_btn.clicked.connect(self._move_up)
        arc_btns.addWidget(move_up_btn)
        move_down_btn = QPushButton("Move Down")
        move_down_btn.clicked.connect(self._move_down)
        arc_btns.addWidget(move_down_btn)
        al.addLayout(arc_btns)
        fl.addWidget(arcs_group)

        fl.addStretch()
        scroll.setWidget(form_widget)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Populate
    # ------------------------------------------------------------------

    def _populate(self) -> None:
        n = self._novel
        raw = n._raw

        self._title.setText(n.title)
        self._slug.setText(n.slug)
        self._description.setPlainText(n.description)
        idx = self._status.findText(n.status)
        if idx >= 0:
            self._status.setCurrentIndex(idx)
        self._primary_lang.setText(n.primary_language)
        ct_idx = self._chapter_type.findText(n.chapter_type)
        if ct_idx >= 0:
            self._chapter_type.setCurrentIndex(ct_idx)
        self._tags.setText(", ".join(n.tags))
        self._cover_art.setText(n.cover_art)

        fp = raw.get("front_page", {})
        self._show_front.setChecked(fp.get("show_on_front_page", True))

        self._author_name.setText(n.author_name)
        self._copyright.setText(n.copyright)
        self._lang_default.setText(n.languages_default)
        self._lang_available.setText(", ".join(n.languages_available))

        ld = raw.get("length_display", {})
        lu_idx = self._length_unit.findText(ld.get("default_unit", "words"))
        if lu_idx >= 0:
            self._length_unit.setCurrentIndex(lu_idx)
        lu = ld.get("language_units", {})
        self._length_overrides.setText(", ".join(f"{k}:{v}" for k, v in lu.items()))

        disp = raw.get("display", {})
        self._show_tags.setChecked(disp.get("show_tags", True))
        self._show_metadata.setChecked(disp.get("show_metadata", True))
        self._show_tn.setChecked(disp.get("show_translation_notes", True))

        nav = raw.get("navigation", {})
        self._show_tags_link.setChecked(nav.get("show_tags_link", True))

        se = raw.get("social_embeds", {})
        self._se_image.setText(se.get("image", ""))
        self._se_desc.setText(se.get("description", ""))
        self._se_keywords.setText(", ".join(se.get("keywords", [])))

        seo = raw.get("seo", {})
        self._seo_index.setChecked(seo.get("allow_indexing", True))
        self._seo_desc.setText(seo.get("meta_description", ""))

        self._epub.setChecked(n.epub_enabled)
        dl = raw.get("downloads", {})
        self._epub_arcs.setChecked(dl.get("include_arcs", True))
        self._comments.setChecked(n.comments_enabled)
        self._comments_toc.setChecked(n.comments_toc)
        self._comments_chapter.setChecked(n.comments_chapter)

        nct = raw.get("new_chapter_tags", {})
        self._nct_enabled.setChecked(nct.get("enabled", True))
        self._nct_days.setValue(nct.get("threshold_days", 7))

        # Manga
        rd = raw.get("reading_direction", "ltr")
        idx = self._reading_dir.findText(rd)
        if idx >= 0:
            self._reading_dir.setCurrentIndex(idx)
        md = raw.get("manga_defaults", {})
        vm_idx = self._view_mode.findText(md.get("view_mode", "single"))
        if vm_idx >= 0:
            self._view_mode.setCurrentIndex(vm_idx)
        self._cover_separate.setChecked(md.get("cover_separate", True))
        ip = raw.get("image_processing", {})
        self._skip_compression.setChecked(ip.get("skip_compression", False))

        meta = raw.get("metadata", {})
        self._update_schedule.setText(meta.get("update_schedule", ""))
        lic = meta.get("license", "")
        li_idx = self._license.findText(lic)
        if li_idx >= 0:
            self._license.setCurrentIndex(li_idx)
        else:
            self._license.setCurrentText(lic)

        footer = raw.get("footer", {})
        self._footer_text.setText(footer.get("custom_text", ""))
        links = footer.get("links", [])
        self._footer_links.setPlainText(
            "\n".join(f"{l.get('text', '')} | {l.get('url', '')}" for l in links)
        )

        self._refresh_arcs_list()
        self._dirty = False

    def _refresh_arcs_list(self) -> None:
        self._arcs_list.clear()
        for arc in self._novel.arcs:
            arc_item = QListWidgetItem(f"[Arc] {arc.title}")
            arc_item.setData(Qt.ItemDataRole.UserRole, ("arc", arc))
            arc_item.setBackground(Qt.GlobalColor.lightGray)
            self._arcs_list.addItem(arc_item)
            for ch in arc.chapters:
                ch_item = QListWidgetItem(f"    {ch.id}: {ch.title}")
                ch_item.setData(Qt.ItemDataRole.UserRole, ("chapter", arc, ch))
                self._arcs_list.addItem(ch_item)

    # ------------------------------------------------------------------
    # Arc management
    # ------------------------------------------------------------------

    def _add_arc(self) -> None:
        title, ok = QInputDialog.getText(self, "Add Arc", "Arc title:")
        if ok and title.strip():
            self._novel.arcs.append(Arc(title=title.strip()))
            self._refresh_arcs_list()
            self._mark_dirty()

    def _add_chapter_to_arc(self) -> None:
        if not self._novel.arcs:
            QMessageBox.warning(self, "No Arcs", "Add an arc first.")
            return
        item = self._arcs_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Select", "Select an arc or chapter in the list.")
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        arc = data[1]

        ch_id, ok = QInputDialog.getText(self, "Add Chapter", "Chapter ID:")
        if not ok or not ch_id.strip():
            return
        ch_title, ok2 = QInputDialog.getText(self, "Chapter Title", "Title:", text=ch_id.replace("-", " ").title())
        if not ok2:
            return
        arc.chapters.append(ArcChapter(id=ch_id.strip(), title=ch_title.strip()))
        self._refresh_arcs_list()
        self._mark_dirty()

    def _remove_arc_item(self) -> None:
        item = self._arcs_list.currentItem()
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if data[0] == "arc":
            self._novel.arcs.remove(data[1])
        elif data[0] == "chapter":
            data[1].chapters.remove(data[2])
        self._refresh_arcs_list()
        self._mark_dirty()

    def _move_up(self) -> None:
        item = self._arcs_list.currentItem()
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if data[0] == "arc":
            idx = self._novel.arcs.index(data[1])
            if idx > 0:
                self._novel.arcs[idx], self._novel.arcs[idx - 1] = self._novel.arcs[idx - 1], self._novel.arcs[idx]
        elif data[0] == "chapter":
            arc, ch = data[1], data[2]
            idx = arc.chapters.index(ch)
            if idx > 0:
                arc.chapters[idx], arc.chapters[idx - 1] = arc.chapters[idx - 1], arc.chapters[idx]
        self._refresh_arcs_list()
        self._mark_dirty()

    def _move_down(self) -> None:
        item = self._arcs_list.currentItem()
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if data[0] == "arc":
            idx = self._novel.arcs.index(data[1])
            if idx < len(self._novel.arcs) - 1:
                self._novel.arcs[idx], self._novel.arcs[idx + 1] = self._novel.arcs[idx + 1], self._novel.arcs[idx]
        elif data[0] == "chapter":
            arc, ch = data[1], data[2]
            idx = arc.chapters.index(ch)
            if idx < len(arc.chapters) - 1:
                arc.chapters[idx], arc.chapters[idx + 1] = arc.chapters[idx + 1], arc.chapters[idx]
        self._refresh_arcs_list()
        self._mark_dirty()

    def _browse_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Cover Image", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            novel_dir = self._config_path.parent
            try:
                rel = Path(path).relative_to(novel_dir)
                self._cover_art.setText(str(rel).replace("\\", "/"))
            except ValueError:
                self._cover_art.setText(path)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self) -> None:
        n = self._novel
        raw = n._raw

        n.title = self._title.text()
        n.slug = self._slug.text()
        n.description = self._description.toPlainText()
        n.status = self._status.currentText()
        n.primary_language = self._primary_lang.text()
        n.chapter_type = self._chapter_type.currentText()
        n.tags = [t.strip() for t in self._tags.text().split(",") if t.strip()]
        n.cover_art = self._cover_art.text()
        n.author_name = self._author_name.text()
        n.copyright = self._copyright.text()
        n.languages_default = self._lang_default.text()
        n.languages_available = [l.strip() for l in self._lang_available.text().split(",") if l.strip()]
        n.epub_enabled = self._epub.isChecked()
        n.comments_enabled = self._comments.isChecked()
        n.comments_toc = self._comments_toc.isChecked()
        n.comments_chapter = self._comments_chapter.isChecked()

        # Extra fields saved directly to raw
        raw.setdefault("front_page", {})["show_on_front_page"] = self._show_front.isChecked()

        # Length display
        lu_text = self._length_overrides.text().strip()
        lu = {}
        if lu_text:
            for pair in lu_text.split(","):
                pair = pair.strip()
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    lu[k.strip()] = v.strip()
        raw["length_display"] = {
            "default_unit": self._length_unit.currentText(),
            "language_units": lu,
        }

        # Display
        raw["display"] = {
            "show_tags": self._show_tags.isChecked(),
            "show_metadata": self._show_metadata.isChecked(),
            "show_translation_notes": self._show_tn.isChecked(),
        }
        raw["navigation"] = {"show_tags_link": self._show_tags_link.isChecked()}

        # Social
        se_keywords = [k.strip() for k in self._se_keywords.text().split(",") if k.strip()]
        if self._se_image.text() or self._se_desc.text() or se_keywords:
            raw["social_embeds"] = {}
            if self._se_image.text():
                raw["social_embeds"]["image"] = self._se_image.text()
            if self._se_desc.text():
                raw["social_embeds"]["description"] = self._se_desc.text()
            if se_keywords:
                raw["social_embeds"]["keywords"] = se_keywords

        # SEO
        raw["seo"] = {
            "allow_indexing": self._seo_index.isChecked(),
        }
        if self._seo_desc.text():
            raw["seo"]["meta_description"] = self._seo_desc.text()

        # Downloads
        raw.setdefault("downloads", {})
        raw["downloads"]["epub_enabled"] = n.epub_enabled
        raw["downloads"]["include_arcs"] = self._epub_arcs.isChecked()

        # New chapter tags
        raw["new_chapter_tags"] = {
            "enabled": self._nct_enabled.isChecked(),
            "threshold_days": self._nct_days.value(),
        }

        # Manga
        raw["reading_direction"] = self._reading_dir.currentText()
        raw["manga_defaults"] = {
            "view_mode": self._view_mode.currentText(),
            "cover_separate": self._cover_separate.isChecked(),
        }
        raw["image_processing"] = {
            "skip_compression": self._skip_compression.isChecked(),
        }

        # Metadata
        meta = {}
        if self._update_schedule.text():
            meta["update_schedule"] = self._update_schedule.text()
        if self._license.currentText():
            meta["license"] = self._license.currentText()
        if meta:
            raw["metadata"] = meta

        # Footer
        footer_links = []
        for line in self._footer_links.toPlainText().strip().splitlines():
            if "|" in line:
                parts = line.split("|", 1)
                footer_links.append({"text": parts[0].strip(), "url": parts[1].strip()})
        ft = self._footer_text.text()
        if ft or footer_links:
            raw["footer"] = {}
            if ft:
                raw["footer"]["custom_text"] = ft
            if footer_links:
                raw["footer"]["links"] = footer_links

        try:
            n.save()
            self._dirty = False
            QMessageBox.information(self, "Saved", "Novel configuration saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
