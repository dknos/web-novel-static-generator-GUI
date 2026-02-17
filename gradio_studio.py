"""Gradio Collaboration Studio for Web Novel App.

Launch with:  python gradio_studio.py [--port PORT] [--share]
"""
import argparse
import os
import sys
import secrets

# Add studio and generator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'studio'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generator'))

import gradio as gr
import yaml

from panels import (
    list_stories, list_chapters,
    load_site_config, save_site_config,
    load_story_config, save_story_config,
    load_authors_config, save_authors_config,
    get_content_dir, get_generator_dir,
)
from editor import load_chapter, save_chapter, preview_markdown
from builder import run_build, run_preview_server




def resolve_auth_credentials():
    """Resolve optional Gradio auth credentials from environment variables."""
    user = os.environ.get('WNSG_STUDIO_USER', '').strip()
    password = os.environ.get('WNSG_STUDIO_PASSWORD', '')
    if not user and not password:
        return None

    if not user or not password:
        raise ValueError('Both WNSG_STUDIO_USER and WNSG_STUDIO_PASSWORD must be set together.')

    if len(password) < 8:
        raise ValueError('WNSG_STUDIO_PASSWORD must be at least 8 characters long.')

    if secrets.compare_digest(password.lower(), 'changeme123'):
        raise ValueError('WNSG_STUDIO_PASSWORD must not use the default placeholder value.')

    return [(user, password)]

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def stories_dropdown_choices():
    """Return list of (display, slug) tuples for story dropdown."""
    return [(s['title'], s['slug']) for s in list_stories()]


def chapters_dropdown_choices(story_slug, language='en'):
    """Return list of (display, id) tuples for chapter dropdown."""
    if not story_slug:
        return []
    chs = list_chapters(story_slug, language)
    return [(f"{c['id']} — {c['title']}", c['id']) for c in chs]


def stories_table_data(status_filter='all'):
    """Return stories as list of lists for Dataframe display."""
    stories = list_stories()
    if status_filter and status_filter != 'all':
        stories = [s for s in stories if s['status'] == status_filter]
    return [[s['title'], s['slug'], s['status'], s['description'][:80]] for s in stories]


def chapters_table_data(story_slug, status_filter='all', language='en'):
    """Return chapters as list of lists for Dataframe display."""
    if not story_slug:
        return []
    chs = list_chapters(story_slug, language)
    if status_filter and status_filter != 'all':
        chs = [c for c in chs if c['status'] == status_filter]
    return [[c['id'], c['title'], c['status'], c['published'], ', '.join(c['tags'])] for c in chs]


# ------------------------------------------------------------------
# Tab: Stories & Chapters
# ------------------------------------------------------------------

def build_stories_tab():
    with gr.Tab("Stories & Chapters"):
        gr.Markdown("### Story Browser")
        with gr.Row():
            status_filter = gr.Dropdown(
                choices=['all', 'ongoing', 'complete', 'hiatus', 'unknown'],
                value='all', label='Filter by Status',
            )
            refresh_btn = gr.Button("Refresh", size='sm')

        stories_df = gr.Dataframe(
            headers=['Title', 'Slug', 'Status', 'Description'],
            interactive=False, wrap=True,
        )

        gr.Markdown("### Chapters")
        with gr.Row():
            story_select = gr.Dropdown(
                choices=stories_dropdown_choices(),
                label='Select Story', interactive=True,
            )
            lang_select = gr.Dropdown(
                choices=['en', 'jp'], value='en', label='Language',
            )
            ch_status_filter = gr.Dropdown(
                choices=['all', 'published', 'draft', 'review', 'scheduled'],
                value='all', label='Chapter Status',
            )

        chapters_df = gr.Dataframe(
            headers=['ID', 'Title', 'Status', 'Published', 'Tags'],
            interactive=False, wrap=True,
        )

        # Event handlers
        def refresh_stories(sf):
            return stories_table_data(sf)

        def refresh_chapters(slug, sf, lang):
            return chapters_table_data(slug, sf, lang)

        refresh_btn.click(refresh_stories, inputs=[status_filter], outputs=[stories_df])
        status_filter.change(refresh_stories, inputs=[status_filter], outputs=[stories_df])
        story_select.change(refresh_chapters, inputs=[story_select, ch_status_filter, lang_select], outputs=[chapters_df])
        ch_status_filter.change(refresh_chapters, inputs=[story_select, ch_status_filter, lang_select], outputs=[chapters_df])
        lang_select.change(refresh_chapters, inputs=[story_select, ch_status_filter, lang_select], outputs=[chapters_df])

        # Load initial data
        stories_df.value = stories_table_data()


# ------------------------------------------------------------------
# Tab: Chapter Editor
# ------------------------------------------------------------------

def build_editor_tab():
    with gr.Tab("Chapter Editor"):
        gr.Markdown("### Edit Chapter")
        with gr.Row():
            ed_story = gr.Dropdown(
                choices=stories_dropdown_choices(),
                label='Story', interactive=True,
            )
            ed_lang = gr.Dropdown(choices=['en', 'jp'], value='en', label='Language')
            ed_chapter = gr.Dropdown(choices=[], label='Chapter', interactive=True)
            load_btn = gr.Button("Load", size='sm')

        with gr.Row():
            with gr.Column(scale=1):
                fm_editor = gr.Code(
                    label='Front Matter (YAML)', language='yaml', lines=8,
                )
                md_editor = gr.Code(
                    label='Markdown Body', language='markdown', lines=20,
                )
                with gr.Row():
                    save_btn = gr.Button("Save", variant='primary')
                    preview_btn = gr.Button("Preview")
                    save_msg = gr.Textbox(label='Status', interactive=False)

            with gr.Column(scale=1):
                preview_html = gr.HTML(label='Preview')

        # Update chapter dropdown when story changes
        def update_chapter_choices(slug, lang):
            choices = chapters_dropdown_choices(slug, lang)
            return gr.Dropdown(choices=choices, value=None)

        ed_story.change(update_chapter_choices, inputs=[ed_story, ed_lang], outputs=[ed_chapter])
        ed_lang.change(update_chapter_choices, inputs=[ed_story, ed_lang], outputs=[ed_chapter])

        # Load chapter
        def on_load(slug, chapter_id, lang):
            if not slug or not chapter_id:
                return '', '', ''
            fm, body = load_chapter(slug, chapter_id, lang)
            return fm, body, ''

        load_btn.click(on_load, inputs=[ed_story, ed_chapter, ed_lang], outputs=[fm_editor, md_editor, save_msg])

        # Save chapter
        def on_save(slug, chapter_id, fm_text, md_text, lang):
            if not slug or not chapter_id:
                return 'No story/chapter selected.'
            try:
                path = save_chapter(slug, chapter_id, fm_text, md_text, lang)
                return f'Saved to {path}'
            except Exception as e:
                return f'Error: {e}'

        save_btn.click(on_save, inputs=[ed_story, ed_chapter, fm_editor, md_editor, ed_lang], outputs=[save_msg])

        # Preview
        def on_preview(md_text):
            if not md_text:
                return '<p><em>Nothing to preview.</em></p>'
            return preview_markdown(md_text)

        preview_btn.click(on_preview, inputs=[md_editor], outputs=[preview_html])
        md_editor.change(on_preview, inputs=[md_editor], outputs=[preview_html])


# ------------------------------------------------------------------
# Tab: Config Editors
# ------------------------------------------------------------------

def build_config_tab():
    with gr.Tab("Configuration"):
        gr.Markdown("### Site Configuration")
        with gr.Row():
            site_cfg_editor = gr.Code(
                label='site_config.yaml', language='yaml', lines=20,
            )
            with gr.Column():
                load_site_btn = gr.Button("Load Site Config")
                save_site_btn = gr.Button("Save Site Config", variant='primary')
                site_cfg_msg = gr.Textbox(label='Status', interactive=False)

        gr.Markdown("---")
        gr.Markdown("### Story Configuration")
        with gr.Row():
            cfg_story_select = gr.Dropdown(
                choices=stories_dropdown_choices(),
                label='Story', interactive=True,
            )
        with gr.Row():
            story_cfg_editor = gr.Code(
                label='Story config.yaml', language='yaml', lines=20,
            )
            with gr.Column():
                load_story_btn = gr.Button("Load Story Config")
                save_story_btn = gr.Button("Save Story Config", variant='primary')
                story_cfg_msg = gr.Textbox(label='Status', interactive=False)

        # Site config handlers
        def on_load_site_cfg():
            cfg = load_site_config()
            return yaml.dump(cfg, default_flow_style=False, allow_unicode=True), ''

        def on_save_site_cfg(yaml_text):
            try:
                data = yaml.safe_load(yaml_text) or {}
                save_site_config(data)
                return 'Site config saved.'
            except Exception as e:
                return f'Error: {e}'

        load_site_btn.click(on_load_site_cfg, outputs=[site_cfg_editor, site_cfg_msg])
        save_site_btn.click(on_save_site_cfg, inputs=[site_cfg_editor], outputs=[site_cfg_msg])

        # Story config handlers
        def on_load_story_cfg(slug):
            if not slug:
                return '', 'No story selected.'
            cfg = load_story_config(slug)
            return yaml.dump(cfg, default_flow_style=False, allow_unicode=True), ''

        def on_save_story_cfg(slug, yaml_text):
            if not slug:
                return 'No story selected.'
            try:
                data = yaml.safe_load(yaml_text) or {}
                save_story_config(slug, data)
                return 'Story config saved.'
            except Exception as e:
                return f'Error: {e}'

        load_story_btn.click(on_load_story_cfg, inputs=[cfg_story_select], outputs=[story_cfg_editor, story_cfg_msg])
        save_story_btn.click(on_save_story_cfg, inputs=[cfg_story_select, story_cfg_editor], outputs=[story_cfg_msg])


# ------------------------------------------------------------------
# Tab: Authors
# ------------------------------------------------------------------

def build_authors_tab():
    with gr.Tab("Authors"):
        gr.Markdown("### Authors Configuration")
        with gr.Row():
            authors_editor = gr.Code(
                label='authors.yaml', language='yaml', lines=20,
            )
            with gr.Column():
                load_authors_btn = gr.Button("Load Authors")
                save_authors_btn = gr.Button("Save Authors", variant='primary')
                authors_msg = gr.Textbox(label='Status', interactive=False)

        def on_load_authors():
            cfg = load_authors_config()
            return yaml.dump(cfg, default_flow_style=False, allow_unicode=True), ''

        def on_save_authors(yaml_text):
            try:
                data = yaml.safe_load(yaml_text) or {}
                save_authors_config(data)
                return 'Authors config saved.'
            except Exception as e:
                return f'Error: {e}'

        load_authors_btn.click(on_load_authors, outputs=[authors_editor, authors_msg])
        save_authors_btn.click(on_save_authors, inputs=[authors_editor], outputs=[authors_msg])


# ------------------------------------------------------------------
# Tab: Build & Preview
# ------------------------------------------------------------------

_preview_proc = None


def build_build_tab():
    with gr.Tab("Build & Preview"):
        gr.Markdown("### Build Site")
        with gr.Row():
            opt_clean = gr.Checkbox(label='Clean build', value=False)
            opt_drafts = gr.Checkbox(label='Include drafts', value=False)
            opt_scheduled = gr.Checkbox(label='Include scheduled', value=False)
            opt_no_epub = gr.Checkbox(label='No EPUB', value=False)
            opt_optimize = gr.Checkbox(label='Optimize images', value=False)
            opt_no_minify = gr.Checkbox(label='No minify', value=False)
            opt_incremental = gr.Checkbox(label='Incremental build', value=True)

        with gr.Row():
            build_btn = gr.Button("Build Site", variant='primary')
            preview_start_btn = gr.Button("Start Preview Server")
            preview_stop_btn = gr.Button("Stop Preview Server")

        build_output = gr.Textbox(label='Build Output', lines=15, interactive=False)
        preview_msg = gr.Textbox(label='Preview Server', interactive=False)

        def on_build(clean, drafts, scheduled, no_epub, optimize, no_minify, incremental):
            success, output = run_build(
                clean=clean, include_drafts=drafts, include_scheduled=scheduled,
                no_epub=no_epub, optimize_images=optimize, no_minify=no_minify, incremental=incremental,
            )
            status = 'Build succeeded.' if success else 'Build FAILED.'
            return f'{status}\n\n{output}'

        def on_start_preview():
            global _preview_proc
            if _preview_proc and _preview_proc.poll() is None:
                return 'Preview server already running on http://localhost:8080'
            _preview_proc = run_preview_server(8080)
            if _preview_proc:
                return 'Preview server started on http://localhost:8080'
            return 'Failed to start preview server.'

        def on_stop_preview():
            global _preview_proc
            if _preview_proc and _preview_proc.poll() is None:
                _preview_proc.terminate()
                _preview_proc = None
                return 'Preview server stopped.'
            return 'No preview server running.'

        build_btn.click(
            on_build,
            inputs=[opt_clean, opt_drafts, opt_scheduled, opt_no_epub, opt_optimize, opt_no_minify, opt_incremental],
            outputs=[build_output],
        )
        preview_start_btn.click(on_start_preview, outputs=[preview_msg])
        preview_stop_btn.click(on_stop_preview, outputs=[preview_msg])


# ------------------------------------------------------------------
# Tab: Asset Manager
# ------------------------------------------------------------------

def build_assets_tab():
    with gr.Tab("Assets"):
        gr.Markdown("### Image Assets per Story")
        asset_story = gr.Dropdown(
            choices=stories_dropdown_choices(),
            label='Story', interactive=True,
        )
        asset_list = gr.Dataframe(
            headers=['Filename', 'Size (KB)', 'Path'],
            interactive=False,
        )
        upload = gr.File(label='Upload Image', file_types=['image'])
        upload_msg = gr.Textbox(label='Status', interactive=False)

        def list_assets(slug):
            if not slug:
                return []
            content_dir = get_content_dir()
            images_dir = os.path.join(content_dir, slug, 'images')
            if not os.path.isdir(images_dir):
                return []
            rows = []
            for fname in sorted(os.listdir(images_dir)):
                fpath = os.path.join(images_dir, fname)
                if os.path.isfile(fpath):
                    size_kb = round(os.path.getsize(fpath) / 1024, 1)
                    rows.append([fname, size_kb, fpath])
            return rows

        def upload_asset(slug, file):
            if not slug:
                return 'No story selected.', []
            if file is None:
                return 'No file selected.', list_assets(slug)
            content_dir = get_content_dir()
            images_dir = os.path.join(content_dir, slug, 'images')
            os.makedirs(images_dir, exist_ok=True)
            dest = os.path.join(images_dir, os.path.basename(file.name))
            import shutil
            shutil.copy2(file.name, dest)
            return f'Uploaded to {dest}', list_assets(slug)

        asset_story.change(list_assets, inputs=[asset_story], outputs=[asset_list])
        upload.upload(upload_asset, inputs=[asset_story, upload], outputs=[upload_msg, asset_list])


# ------------------------------------------------------------------
# Main App
# ------------------------------------------------------------------

def create_app():
    with gr.Blocks(
        title='Web Novel Studio',
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown("# Web Novel Studio")
        gr.Markdown("Collaboration studio for managing web novel content, configs, and builds.")

        build_stories_tab()
        build_editor_tab()
        build_config_tab()
        build_authors_tab()
        build_build_tab()
        build_assets_tab()

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Web Novel Gradio Studio')
    parser.add_argument('--port', type=int, default=7860, help='Port to run on')
    parser.add_argument('--share', action='store_true', help='Create public share link')
    parser.add_argument('--require-auth', action='store_true',
                        help='Require auth using WNSG_STUDIO_USER/WNSG_STUDIO_PASSWORD env vars')
    args = parser.parse_args()

    app = create_app()

    auth_credentials = None
    if args.require_auth or args.share:
        auth_credentials = resolve_auth_credentials()
        if auth_credentials is None and args.share:
            raise ValueError('Refusing to start with --share without credentials. Set WNSG_STUDIO_USER and WNSG_STUDIO_PASSWORD.')

    app.launch(server_port=args.port, share=args.share, auth=auth_credentials)
