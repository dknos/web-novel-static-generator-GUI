"""Build integration — runs generate.py as a subprocess."""
import os
import subprocess
import threading


def get_generate_script():
    """Get the path to generate.py."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generator', 'generate.py')


def run_build(clean=False, include_drafts=False, include_scheduled=False,
              no_epub=False, optimize_images=False, no_minify=False):
    """Run the site generator and return (success, output).

    Returns:
        Tuple of (bool, str) — success flag and combined stdout/stderr.
    """
    script = get_generate_script()
    cmd = ['python', script]

    if clean:
        cmd.append('--clean')
    if include_drafts:
        cmd.append('--include-drafts')
    if include_scheduled:
        cmd.append('--include-scheduled')
    if no_epub:
        cmd.append('--no-epub')
    if optimize_images:
        cmd.append('--optimize-images')
    if no_minify:
        cmd.append('--no-minify')

    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(script),
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout
        if result.stderr:
            output += '\n--- STDERR ---\n' + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, 'Build timed out after 5 minutes.'
    except Exception as e:
        return False, f'Build failed: {e}'


def run_build_async(callback, **kwargs):
    """Run build in a background thread, calling callback(success, output) when done."""
    def _worker():
        success, output = run_build(**kwargs)
        callback(success, output)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


def run_preview_server(port=8080):
    """Start a preview server (generate.py --serve) and return the process.

    Returns:
        subprocess.Popen or None on error.
    """
    script = get_generate_script()
    try:
        proc = subprocess.Popen(
            ['python', script, '--serve', str(port)],
            cwd=os.path.dirname(script),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return proc
    except Exception:
        return None
