"""Gradio Studio — Installer & Launcher.

Installs dependencies (including Gradio) then launches the studio.
"""

import os
import sys
import subprocess
import ctypes
import webbrowser
import time

APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0] if not getattr(sys, 'frozen', False)
                                           else sys.executable))
REQUIREMENTS = os.path.join(APP_DIR, 'requirements.txt')
STUDIO_SCRIPT = os.path.join(APP_DIR, 'gradio_studio.py')


def show_msg(title, text, icon=0x40):
    ctypes.windll.user32.MessageBoxW(0, text, title, icon)


def install_dependencies():
    """Run pip install -r requirements.txt (all deps including Gradio)."""
    if not os.path.isfile(REQUIREMENTS):
        return True, 'requirements.txt not found — skipping install.'

    cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', '-r', REQUIREMENTS]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            return False, f'pip install failed:\n{result.stderr}'
        return True, result.stdout
    except FileNotFoundError:
        return False, 'Python/pip not found. Please install Python 3.11+ from python.org.'
    except subprocess.TimeoutExpired:
        return False, 'Dependency installation timed out.'
    except Exception as e:
        return False, str(e)


def check_deps_installed():
    try:
        import gradio   # noqa: F401
        import jinja2    # noqa: F401
        import yaml      # noqa: F401
        return True
    except ImportError:
        return False


def main():
    os.chdir(APP_DIR)

    if not check_deps_installed():
        print('=' * 50)
        print('  Web Novel Studio — First-time Setup')
        print('=' * 50)
        print()
        print('Installing dependencies (this may take a minute)...')
        print()

        ok, output = install_dependencies()
        if not ok:
            print(f'\nInstall failed:\n{output}')
            show_msg('Install Failed', output, 0x10)
            input('\nPress Enter to exit...')
            return

        print('\nDependencies installed successfully.')
        print()

    if not os.path.isfile(STUDIO_SCRIPT):
        show_msg('Error', f'gradio_studio.py not found at:\n{STUDIO_SCRIPT}', 0x10)
        return

    print('Starting Web Novel Studio...')
    print('Opening http://localhost:7860 in your browser...')
    print()
    print('Press Ctrl+C in this window to stop the server.')

    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:7860')

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Run gradio_studio.py
    try:
        subprocess.run([sys.executable, STUDIO_SCRIPT], cwd=APP_DIR)
    except KeyboardInterrupt:
        print('\nStudio stopped.')
    except Exception as e:
        show_msg('Error', f'Studio crashed:\n{e}', 0x10)


if __name__ == '__main__':
    main()
