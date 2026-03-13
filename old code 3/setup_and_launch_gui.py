#!/usr/bin/env python3
"""Create venv, install requirements, install Playwright browsers, and launch the GUI.

This script is cross-platform (Linux/macOS/Windows). Run from the project root:

  python3 scripts/setup_and_launch_gui.py

It will create a virtual environment in `.venv/`, install packages from
`requirements.txt`, run `playwright install`, then launch `gui.py` using the
venv Python. If the venv already exists it will reuse it.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run(cmd, **kwargs):
    print("=> ", " ".join(cmd))
    subprocess.run(cmd, check=True, **kwargs)


def main():
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)

    venv_dir = root / ".venv"
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    # 1) create venv if missing
    if not venv_dir.exists():
        print("Creating virtualenv at .venv/")
        run([sys.executable, "-m", "venv", str(venv_dir)])
    else:
        print("Using existing virtualenv at .venv/")

    # 2) ensure pip is upgraded
    run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"]) 

    # 3) install requirements
    req = root / "requirements.txt"
    if req.exists():
        print(f"Installing requirements from {req}")
        run([str(venv_python), "-m", "pip", "install", "-r", str(req)])
    else:
        print("No requirements.txt found; skipping pip install")

    # 4) install Playwright browsers (if playwright present)
    try:
        # try to import playwright using the venv python
        run([str(venv_python), "-m", "playwright", "install", "chromium"], stdout=subprocess.DEVNULL)
        print("Installed Playwright browsers (chromium)")
    except subprocess.CalledProcessError:
        print("Playwright not available or install failed; continuing")

    # 5) Launch GUI
    print("Launching GUI (gui.py) using the virtualenv Python")

    # On Unix systems without a DISPLAY set, attempt to use xvfb-run if available
    launch_cmd = [str(venv_python), str(root / "gui.py")]
    if sys.platform != "win32" and "DISPLAY" not in os.environ:
        xvfb = shutil.which("xvfb-run")
        if xvfb:
            print("No DISPLAY detected; wrapping launch with xvfb-run")
            launch_cmd = [xvfb, "-s", "-screen 0 1920x1080x24"] + launch_cmd
        else:
            print("Warning: DISPLAY not set and xvfb-run not found; launching without virtual frame buffer")

    os.execv(launch_cmd[0], launch_cmd)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("Command failed:", e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Cancelled")
        sys.exit(2)
