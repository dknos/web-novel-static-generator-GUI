"""Web Novel App — Installer & Launcher.

When run, installs dependencies from requirements.txt (if needed) then
launches the PySide6 desktop app.  Compiles to a standalone .exe via
build_exe.bat.
"""

import os
import sys
import subprocess
import ctypes

APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0] if not getattr(sys, 'frozen', False)
                                           else sys.executable))
REQUIREMENTS = os.path.join(APP_DIR, 'requirements.txt')
MAIN_SCRIPT = os.path.join(APP_DIR, 'main.py')


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def show_msg(title, text, icon=0x40):
    """Show a Windows message box.  icon: 0x10=error, 0x30=warn, 0x40=info."""
    ctypes.windll.user32.MessageBoxW(0, text, title, icon)


def install_dependencies():
    """Run pip install -r requirements.txt, skipping Gradio (large, optional)."""
    if not os.path.isfile(REQUIREMENTS):
        return True, 'requirements.txt not found — skipping install.'

    # Filter out gradio (optional, large) for the desktop app
    core_deps = []
    with open(REQUIREMENTS, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.lower().startswith('gradio'):
                continue
            core_deps.append(line)

    cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade'] + core_deps
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
    """Quick check if key packages are importable."""
    try:
        import PySide6      # noqa: F401
        import jinja2        # noqa: F401
        import yaml          # noqa: F401
        import markdown      # noqa: F401
        return True
    except ImportError:
        return False


def launch_app():
    """Launch main.py in the same Python interpreter."""
    if not os.path.isfile(MAIN_SCRIPT):
        show_msg('Error', f'main.py not found at:\n{MAIN_SCRIPT}', 0x10)
        return

    os.chdir(APP_DIR)
    sys.path.insert(0, APP_DIR)

    # Execute main.py in-process so the app window appears
    try:
        with open(MAIN_SCRIPT, 'r', encoding='utf-8') as f:
            code = f.read()
        exec(compile(code, MAIN_SCRIPT, 'exec'), {'__name__': '__main__', '__file__': MAIN_SCRIPT})
    except SystemExit:
        pass
    except Exception as e:
        show_msg('Error', f'App crashed:\n{e}', 0x10)


def main():
    os.chdir(APP_DIR)

    if not check_deps_installed():
        # Show a console window for install progress
        print('=' * 50)
        print('  Web Novel App — First-time Setup')
        print('=' * 50)
        print()
        print('Installing dependencies...')
        print()

        ok, output = install_dependencies()
        if not ok:
            print(f'\nInstall failed:\n{output}')
            show_msg('Install Failed', output, 0x10)
            input('\nPress Enter to exit...')
            return

        print('\nDependencies installed successfully.')
        print()

        # Verify
        if not check_deps_installed():
            msg = 'Dependencies installed but imports still fail.\nTry running: pip install -r requirements.txt'
            print(msg)
            show_msg('Warning', msg, 0x30)
            input('\nPress Enter to exit...')
            return

    launch_app()


if __name__ == '__main__':
    main()
