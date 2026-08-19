"""
Build the Windows .exe for RollerCoin Auto-Play Bot.

Usage (from the project root):
    pip install -r dev-requirements.txt
    python build_exe.py

Output: dist/RollerCoinBot.exe  (a single self-contained file).
The exe includes the GUI, all game bots, the automation engine and the
"routine mode" - no Python install is needed on the target machine.

Note: Windows SmartScreen / antivirus may flag freshly built PyInstaller
.exe files. It is a known false-positive issue with all auto-generated
unsigned executables.
"""

import os
import shutil
import sys

# Optional icon (leave None to skip). Drop any .ico in the project root and
# name it "icon.ico" (or change the path below).
ICON = "icon.ico" if os.path.exists("icon.ico") else None

MODULES = [
    "main.py",
]

class Options:
    pass


def main():
    # Make sure PyInstaller is available
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed. Run:  pip install -r dev-requirements.txt")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",            # GUI only, no black console window
        "--name", "RollerCoinBot",
        # numpy 2.x needs ALL its submodules+data collected or the frozen exe
        # fails with "No module named 'numpy._core._exceptions'".
        "--collect-all", "numpy",
        # Routine_config.py is generated at runtime next to the .exe - never
        # bundle the developer's local copy (orchestrator.py imports it).
        "--exclude-module", "Routine_config",
    ]
    if ICON:
        cmd += ["--icon", ICON]

    cmd += MODULES

    print("Running PyInstaller...")
    os.system(" ".join(f'"{c}"' if " " in c else c for c in cmd))

    dist = os.path.join("dist", "RollerCoinBot.exe")
    if os.path.exists(dist):
        size_mb = os.path.getsize(dist) / (1024 * 1024)
        print(f"\nDone!  {dist}  ({size_mb:.1f} MB)")
        print("Share this single file with other users - no Python needed.")
    else:
        print("\nBuild failed - no dist/RollerCoinBot.exe produced. Check the logs above.")


if __name__ == "__main__":
    main()