"""Site config editor — form-based UI for site_config.yaml."""

from __future__ import annotations

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
    QDoubleSpinBox,
    QPushButton,
    QLabel,
    QMessageBox,
)

from app.models.project import Project
from app.utils.yaml_helper import load_yaml, save_yaml


class ConfigEditor(QWidget):
    """Form editor for site_config.yaml with all documented settings."""

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._data = project.load_site_config()
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
        header.addWidget(QLabel("<b>Site Configuration</b>"))
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
        self._site_name = QLineEdit()
        self._site_name.textChanged.connect(self._mark_dirty)
        bl.addRow("Site Name:", self._site_name)
        self._site_desc = QTextEdit()
        self._site_desc.setMaximumHeight(60)
        self._site_desc.textChanged.connect(self._mark_dirty)
        bl.addRow("Description:", self._site_desc)
        self._site_url = QLineEdit()
        self._site_url.textChanged.connect(self._mark_dirty)
        bl.addRow("Site URL:", self._site_url)
        self._site_author = QLineEdit()
        self._site_author.textChanged.connect(self._mark_dirty)
        bl.addRow("Site Author:", self._site_author)
        fl.addWidget(basic)

        # --- Languages ---
        lang = QGroupBox("Languages")
        ll = QFormLayout(lang)
        self._languages = QLineEdit()
        self._languages.setPlaceholderText("en, jp  (comma separated)")
        self._languages.textChanged.connect(self._mark_dirty)
        ll.addRow("Available:", self._languages)
        fl.addWidget(lang)

        # --- Social Embeds ---
        social = QGroupBox("Social Embeds (Open Graph / Twitter Cards)")
        sl = QFormLayout(social)
        self._social_image = QLineEdit()
        self._social_image.textChanged.connect(self._mark_dirty)
        sl.addRow("Default Image:", self._social_image)
        self._social_title_fmt = QLineEdit()
        self._social_title_fmt.textChanged.connect(self._mark_dirty)
        sl.addRow("Title Format:", self._social_title_fmt)
        self._social_desc = QLineEdit()
        self._social_desc.textChanged.connect(self._mark_dirty)
        sl.addRow("Default Description:", self._social_desc)
        self._twitter = QLineEdit()
        self._twitter.textChanged.connect(self._mark_dirty)
        sl.addRow("Twitter Handle:", self._twitter)
        self._fb_app_id = QLineEdit()
        self._fb_app_id.textChanged.connect(self._mark_dirty)
        sl.addRow("Facebook App ID:", self._fb_app_id)
        fl.addWidget(social)

        # --- SEO ---
        seo = QGroupBox("SEO & Indexing")
        sel = QFormLayout(seo)
        self._allow_indexing = QCheckBox("Allow search engine indexing")
        self._allow_indexing.stateChanged.connect(self._mark_dirty)
        sel.addRow(self._allow_indexing)
        self._robots_txt = QCheckBox("Generate robots.txt")
        self._robots_txt.stateChanged.connect(self._mark_dirty)
        sel.addRow(self._robots_txt)
        self._sitemap = QCheckBox("Generate sitemap.xml")
        self._sitemap.stateChanged.connect(self._mark_dirty)
        sel.addRow(self._sitemap)
        fl.addWidget(seo)

        # --- RSS ---
        rss = QGroupBox("RSS Feeds")
        rl = QFormLayout(rss)
        self._rss_enabled = QCheckBox("Generate RSS feeds")
        self._rss_enabled.stateChanged.connect(self._mark_dirty)
        rl.addRow(self._rss_enabled)
        self._rss_title = QLineEdit()
        self._rss_title.textChanged.connect(self._mark_dirty)
        rl.addRow("Feed Title:", self._rss_title)
        self._rss_desc = QLineEdit()
        self._rss_desc.textChanged.connect(self._mark_dirty)
        rl.addRow("Feed Description:", self._rss_desc)
        self._story_feeds = QCheckBox("Per-story RSS feeds")
        self._story_feeds.stateChanged.connect(self._mark_dirty)
        rl.addRow(self._story_feeds)
        fl.addWidget(rss)

        # --- EPUB ---
        epub = QGroupBox("EPUB Generation")
        el = QFormLayout(epub)
        self._epub_enabled = QCheckBox("Enable EPUB generation")
        self._epub_enabled.stateChanged.connect(self._mark_dirty)
        el.addRow(self._epub_enabled)
        fl.addWidget(epub)

        # --- Author Pages ---
        ap = QGroupBox("Author Pages")
        apl = QFormLayout(ap)
        self._author_max_chapters = QSpinBox()
        self._author_max_chapters.setRange(0, 999)
        self._author_max_chapters.setToolTip("0 = unlimited")
        self._author_max_chapters.valueChanged.connect(self._mark_dirty)
        apl.addRow("Max Recent Chapters:", self._author_max_chapters)
        fl.addWidget(ap)

        # --- Comments ---
        comments = QGroupBox("Comments (Utterances)")
        cl = QFormLayout(comments)
        self._comments_enabled = QCheckBox("Enable comments site-wide")
        self._comments_enabled.stateChanged.connect(self._mark_dirty)
        cl.addRow(self._comments_enabled)
        self._utterances_repo = QLineEdit()
        self._utterances_repo.setPlaceholderText("username/repo-name")
        self._utterances_repo.textChanged.connect(self._mark_dirty)
        cl.addRow("GitHub Repo:", self._utterances_repo)
        self._utterances_theme = QComboBox()
        self._utterances_theme.addItems([
            "github-light", "github-dark", "preferred-color-scheme",
            "github-dark-orange", "icy-dark", "dark-blue", "photon-dark",
        ])
        self._utterances_theme.currentTextChanged.connect(self._mark_dirty)
        cl.addRow("Theme:", self._utterances_theme)
        self._utterances_term = QComboBox()
        self._utterances_term.addItems(["pathname", "url", "title", "og:title"])
        self._utterances_term.currentTextChanged.connect(self._mark_dirty)
        cl.addRow("Issue Term:", self._utterances_term)
        self._utterances_label = QLineEdit()
        self._utterances_label.textChanged.connect(self._mark_dirty)
        cl.addRow("Label:", self._utterances_label)
        fl.addWidget(comments)

        # --- Image Optimization ---
        img = QGroupBox("Image Optimization")
        il = QFormLayout(img)
        self._img_opt = QCheckBox("Enable automatic image optimization (WebP)")
        self._img_opt.stateChanged.connect(self._mark_dirty)
        il.addRow(self._img_opt)
        self._img_quality = QSpinBox()
        self._img_quality.setRange(1, 100)
        self._img_quality.valueChanged.connect(self._mark_dirty)
        il.addRow("Quality (0-100):", self._img_quality)
        fl.addWidget(img)

        # --- New Chapter Tags ---
        nct = QGroupBox("New Chapter Tags")
        ncl = QFormLayout(nct)
        self._nct_enabled = QCheckBox("Show (NEW!) tags on recent chapters")
        self._nct_enabled.stateChanged.connect(self._mark_dirty)
        ncl.addRow(self._nct_enabled)
        self._nct_days = QSpinBox()
        self._nct_days.setRange(1, 365)
        self._nct_days.valueChanged.connect(self._mark_dirty)
        ncl.addRow("Threshold (days):", self._nct_days)
        fl.addWidget(nct)

        # --- Accessibility ---
        a11y = QGroupBox("Accessibility")
        a11l = QFormLayout(a11y)
        self._a11y_enabled = QCheckBox("Enable accessibility features")
        self._a11y_enabled.stateChanged.connect(self._mark_dirty)
        a11l.addRow(self._a11y_enabled)
        self._a11y_alt = QCheckBox("Enforce alt text for images")
        self._a11y_alt.stateChanged.connect(self._mark_dirty)
        a11l.addRow(self._a11y_alt)
        self._a11y_aria = QCheckBox("Auto ARIA labels")
        self._a11y_aria.stateChanged.connect(self._mark_dirty)
        a11l.addRow(self._a11y_aria)
        self._a11y_kbd = QCheckBox("Keyboard navigation")
        self._a11y_kbd.stateChanged.connect(self._mark_dirty)
        a11l.addRow(self._a11y_kbd)
        self._a11y_reports = QCheckBox("Build accessibility reports")
        self._a11y_reports.stateChanged.connect(self._mark_dirty)
        a11l.addRow(self._a11y_reports)
        fl.addWidget(a11y)

        # --- Manga Reader ---
        manga = QGroupBox("Manga Reader")
        ml = QFormLayout(manga)
        self._manga_transitions = QCheckBox("Seamless page transitions")
        self._manga_transitions.stateChanged.connect(self._mark_dirty)
        ml.addRow(self._manga_transitions)
        self._manga_duration = QDoubleSpinBox()
        self._manga_duration.setRange(0.1, 1.0)
        self._manga_duration.setSingleStep(0.05)
        self._manga_duration.valueChanged.connect(self._mark_dirty)
        ml.addRow("Transition Duration (s):", self._manga_duration)
        fl.addWidget(manga)

        # --- Story Metadata Display ---
        smd = QGroupBox("Story Metadata Display")
        sml = QFormLayout(smd)
        self._sm_schedule = QCheckBox("Show update schedule")
        self._sm_schedule.stateChanged.connect(self._mark_dirty)
        sml.addRow(self._sm_schedule)
        self._sm_stats = QCheckBox("Show story statistics")
        self._sm_stats.stateChanged.connect(self._mark_dirty)
        sml.addRow(self._sm_stats)
        self._sm_contributions = QCheckBox("Show author contributions")
        self._sm_contributions.stateChanged.connect(self._mark_dirty)
        sml.addRow(self._sm_contributions)
        self._sm_updated = QCheckBox("Show last updated date")
        self._sm_updated.stateChanged.connect(self._mark_dirty)
        sml.addRow(self._sm_updated)
        self._sm_license = QCheckBox("Show license info")
        self._sm_license.stateChanged.connect(self._mark_dirty)
        sml.addRow(self._sm_license)
        fl.addWidget(smd)

        # --- Front Page ---
        fp = QGroupBox("Front Page")
        fpl = QFormLayout(fp)
        self._sort_method = QComboBox()
        self._sort_method.addItems(["recent_update", "alphabetical", "original"])
        self._sort_method.currentTextChanged.connect(self._mark_dirty)
        fpl.addRow("Sort Method:", self._sort_method)
        self._featured_order = QLineEdit()
        self._featured_order.setPlaceholderText("novel-slug-1, novel-slug-2 (comma separated)")
        self._featured_order.textChanged.connect(self._mark_dirty)
        fpl.addRow("Featured Order:", self._featured_order)
        self._primary_limit = QCheckBox("Limit primary stories shown in detail")
        self._primary_limit.stateChanged.connect(self._mark_dirty)
        fpl.addRow(self._primary_limit)
        self._primary_max = QSpinBox()
        self._primary_max.setRange(1, 50)
        self._primary_max.valueChanged.connect(self._mark_dirty)
        fpl.addRow("Max Primary Stories:", self._primary_max)
        self._fp_title = QLineEdit()
        self._fp_title.textChanged.connect(self._mark_dirty)
        fpl.addRow("Title Override:", self._fp_title)
        self._fp_subtitle = QLineEdit()
        self._fp_subtitle.textChanged.connect(self._mark_dirty)
        fpl.addRow("Subtitle:", self._fp_subtitle)
        fl.addWidget(fp)

        # --- Footer ---
        footer = QGroupBox("Footer")
        ftl = QFormLayout(footer)
        self._copyright = QLineEdit()
        self._copyright.textChanged.connect(self._mark_dirty)
        ftl.addRow("Copyright:", self._copyright)
        self._footer_links = QTextEdit()
        self._footer_links.setMaximumHeight(100)
        self._footer_links.setPlaceholderText("One link per line: text | url")
        self._footer_links.textChanged.connect(self._mark_dirty)
        ftl.addRow("Links:", self._footer_links)
        fl.addWidget(footer)

        fl.addStretch()
        scroll.setWidget(form_widget)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Populate
    # ------------------------------------------------------------------

    def _populate(self) -> None:
        d = self._data
        self._site_name.setText(d.get("site_name", ""))
        self._site_desc.setPlainText(d.get("site_description", ""))
        self._site_url.setText(d.get("site_url", ""))
        self._site_author.setText(d.get("site_author", ""))

        langs = d.get("languages", {}).get("available", [])
        self._languages.setText(", ".join(langs))

        se = d.get("social_embeds", {})
        self._social_image.setText(se.get("default_image", ""))
        self._social_title_fmt.setText(se.get("title_format", ""))
        self._social_desc.setText(se.get("default_description", ""))
        self._twitter.setText(se.get("twitter_handle", ""))
        self._fb_app_id.setText(se.get("facebook_app_id", ""))

        seo = d.get("seo", {})
        self._allow_indexing.setChecked(seo.get("allow_indexing", True))
        self._robots_txt.setChecked(seo.get("generate_robots_txt", True))
        self._sitemap.setChecked(seo.get("generate_sitemap", True))

        rss = d.get("rss", {})
        self._rss_enabled.setChecked(rss.get("generate_feeds", True))
        sf = rss.get("site_feed", {})
        self._rss_title.setText(sf.get("title", ""))
        self._rss_desc.setText(sf.get("description", ""))
        self._story_feeds.setChecked(rss.get("story_feeds_enabled", True))

        epub = d.get("epub", {})
        self._epub_enabled.setChecked(epub.get("generate_enabled", True))

        ap = d.get("author_pages", {})
        self._author_max_chapters.setValue(ap.get("max_recent_chapters", 20))

        comments = d.get("comments", {})
        self._comments_enabled.setChecked(comments.get("enabled", False))
        self._utterances_repo.setText(comments.get("utterances_repo", ""))
        theme = comments.get("utterances_theme", "github-light")
        idx = self._utterances_theme.findText(theme)
        if idx >= 0:
            self._utterances_theme.setCurrentIndex(idx)
        term = comments.get("utterances_issue_term", "pathname")
        idx = self._utterances_term.findText(term)
        if idx >= 0:
            self._utterances_term.setCurrentIndex(idx)
        self._utterances_label.setText(comments.get("utterances_label", ""))

        img = d.get("image_optimization", {})
        self._img_opt.setChecked(img.get("enabled", False))
        self._img_quality.setValue(img.get("quality", 85))

        nct = d.get("new_chapter_tags", {})
        self._nct_enabled.setChecked(nct.get("enabled", True))
        self._nct_days.setValue(nct.get("threshold_days", 7))

        a11y = d.get("accessibility", {})
        self._a11y_enabled.setChecked(a11y.get("enabled", True))
        self._a11y_alt.setChecked(a11y.get("enforce_alt_text", True))
        self._a11y_aria.setChecked(a11y.get("auto_aria_labels", True))
        self._a11y_kbd.setChecked(a11y.get("keyboard_navigation", True))
        self._a11y_reports.setChecked(a11y.get("build_reports", True))

        manga = d.get("manga", {}).get("seamless_transitions", {})
        self._manga_transitions.setChecked(manga.get("enabled", True))
        self._manga_duration.setValue(manga.get("duration", 0.15))

        sm = d.get("story_metadata", {})
        self._sm_schedule.setChecked(sm.get("show_update_schedule", True))
        self._sm_stats.setChecked(sm.get("show_story_stats", True))
        self._sm_contributions.setChecked(sm.get("show_author_contributions", True))
        self._sm_updated.setChecked(sm.get("show_last_updated", True))
        self._sm_license.setChecked(sm.get("show_license_info", True))

        fp = d.get("front_page", {})
        sort_m = fp.get("story_sort_method", "recent_update")
        idx = self._sort_method.findText(sort_m)
        if idx >= 0:
            self._sort_method.setCurrentIndex(idx)
        fo = fp.get("featured_order", [])
        self._featured_order.setText(", ".join(fo) if fo else "")
        ps = fp.get("primary_stories", {})
        self._primary_limit.setChecked(ps.get("limit_enabled", False))
        self._primary_max.setValue(ps.get("max_count", 2))
        self._fp_title.setText(fp.get("title_override", ""))
        self._fp_subtitle.setText(fp.get("subtitle", ""))

        footer = d.get("footer", {})
        self._copyright.setText(footer.get("copyright", ""))
        links = footer.get("links", [])
        link_lines = [f"{l.get('text', '')} | {l.get('url', '')}" for l in links]
        self._footer_links.setPlainText("\n".join(link_lines))

        self._dirty = False

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self) -> None:
        d = self._data

        d["site_name"] = self._site_name.text()
        d["site_description"] = self._site_desc.toPlainText()
        d["site_url"] = self._site_url.text()
        d["site_author"] = self._site_author.text()

        d["languages"] = {
            "available": [l.strip() for l in self._languages.text().split(",") if l.strip()]
        }

        d["social_embeds"] = {
            "default_image": self._social_image.text(),
            "title_format": self._social_title_fmt.text(),
            "default_description": self._social_desc.text(),
            "twitter_handle": self._twitter.text(),
            "facebook_app_id": self._fb_app_id.text(),
        }

        d["seo"] = {
            "allow_indexing": self._allow_indexing.isChecked(),
            "generate_robots_txt": self._robots_txt.isChecked(),
            "generate_sitemap": self._sitemap.isChecked(),
        }

        d["rss"] = {
            "generate_feeds": self._rss_enabled.isChecked(),
            "site_feed": {
                "title": self._rss_title.text(),
                "description": self._rss_desc.text(),
            },
            "story_feeds_enabled": self._story_feeds.isChecked(),
        }

        d["epub"] = {"generate_enabled": self._epub_enabled.isChecked()}
        d["author_pages"] = {"max_recent_chapters": self._author_max_chapters.value()}

        d["comments"] = {
            "enabled": self._comments_enabled.isChecked(),
            "utterances_repo": self._utterances_repo.text(),
            "utterances_theme": self._utterances_theme.currentText(),
            "utterances_issue_term": self._utterances_term.currentText(),
            "utterances_label": self._utterances_label.text(),
        }

        d["image_optimization"] = {
            "enabled": self._img_opt.isChecked(),
            "quality": self._img_quality.value(),
        }

        d["new_chapter_tags"] = {
            "enabled": self._nct_enabled.isChecked(),
            "threshold_days": self._nct_days.value(),
        }

        d["accessibility"] = {
            "enabled": self._a11y_enabled.isChecked(),
            "enforce_alt_text": self._a11y_alt.isChecked(),
            "auto_aria_labels": self._a11y_aria.isChecked(),
            "keyboard_navigation": self._a11y_kbd.isChecked(),
            "build_reports": self._a11y_reports.isChecked(),
        }

        d["manga"] = {
            "seamless_transitions": {
                "enabled": self._manga_transitions.isChecked(),
                "duration": self._manga_duration.value(),
            }
        }

        d["story_metadata"] = {
            "show_update_schedule": self._sm_schedule.isChecked(),
            "show_story_stats": self._sm_stats.isChecked(),
            "show_author_contributions": self._sm_contributions.isChecked(),
            "show_last_updated": self._sm_updated.isChecked(),
            "show_license_info": self._sm_license.isChecked(),
        }

        fp = d.setdefault("front_page", {})
        fp["story_sort_method"] = self._sort_method.currentText()
        fo_text = self._featured_order.text().strip()
        fp["featured_order"] = [s.strip() for s in fo_text.split(",") if s.strip()] if fo_text else []
        fp["primary_stories"] = {
            "limit_enabled": self._primary_limit.isChecked(),
            "max_count": self._primary_max.value(),
        }
        fp["title_override"] = self._fp_title.text()
        fp["subtitle"] = self._fp_subtitle.text()

        # Parse footer links
        links = []
        for line in self._footer_links.toPlainText().strip().splitlines():
            if "|" in line:
                parts = line.split("|", 1)
                links.append({"text": parts[0].strip(), "url": parts[1].strip()})
        d.setdefault("footer", {})
        d["footer"]["copyright"] = self._copyright.text()
        d["footer"]["links"] = links

        try:
            save_yaml(self._project.site_config_path, d)
            self._dirty = False
            QMessageBox.information(self, "Saved", "Site configuration saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
