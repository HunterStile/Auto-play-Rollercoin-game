"""
Build the Windows .exe for RollerCoin Auto-Play Bot.

Usage (from the project root):
    pip install -r dev-requirements.txt
    python build_exe.py

Output: dist/RollerCoin-bot.exe  (a single self-contained file).
The exe includes the GUI, all game bots, the automation engine and the
"routine mode" - no Python install is needed on the target machine.

Note: Windows SmartScreen / antivirus may flag freshly built PyInstaller
.exe files. It is a known false-positive issue with all auto-generated
unsigned executables.
"""

import os
import subprocess
import sys
from pathlib import Path
from app_version import VERSION

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PNG_ICON = os.path.join(PROJECT_DIR, "logo-exe.png")
ICO_ICON = os.path.join(PROJECT_DIR, "build", "logo-exe.ico")


def prepare_icon():
    """Convert the project PNG logo to the ICO format required by Windows."""
    if not os.path.exists(PNG_ICON):
        return None

    try:
        from PIL import Image
    except ImportError:
        print("Pillow is required to convert logo-exe.png to an .ico file.")
        sys.exit(1)

    os.makedirs(os.path.dirname(ICO_ICON), exist_ok=True)
    with Image.open(PNG_ICON) as image:
        image = image.convert("RGBA")
        canvas_size = max(image.size)
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        offset = (
            (canvas_size - image.width) // 2,
            (canvas_size - image.height) // 2,
        )
        canvas.alpha_composite(image, offset)
        canvas.save(
            ICO_ICON,
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
        )
    return ICO_ICON

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

    icon = prepare_icon()
    version_file = Path(PROJECT_DIR) / 'build' / 'version_info.txt'
    version_file.parent.mkdir(exist_ok=True)
    version_tuple = tuple(int(part) for part in VERSION.split('.')) + (0,)
    version_file.write_text(f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers={version_tuple!r}, prodvers={version_tuple!r},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('FileDescription', 'RollerCoin Auto-Play Bot'),
    StringStruct('FileVersion', '{VERSION}'),
    StringStruct('ProductName', 'RollerCoin Auto-Play Bot'),
    StringStruct('ProductVersion', '{VERSION}'),
    StringStruct('OriginalFilename', 'RollerCoin-bot.exe')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)''', encoding='utf-8')
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",            # GUI only, no black console window
        "--name", "RollerCoin-bot",
        "--version-file", str(version_file),
        "--hidden-import", "functions",
        "--hidden-import", "cerca_posizione",
        "--hidden-import", "Elezioni",
        # numpy 2.x needs ALL its submodules+data collected or the frozen exe
        # fails with "No module named 'numpy._core._exceptions'".
        "--collect-all", "numpy",
        # Routine_config.py is generated at runtime next to the .exe - never
        # bundle the developer's local copy (orchestrator.py imports it).
        "--exclude-module", "Routine_config",
    ]
    if icon:
        cmd += ["--icon", icon]
    if os.path.exists(PNG_ICON):
        cmd += ["--splash", PNG_ICON]

    cmd += MODULES

    print("Running PyInstaller...")
    result = subprocess.run(cmd, check=False)

    dist = os.path.join("dist", "RollerCoin-bot.exe")
    if result.returncode == 0 and os.path.exists(dist):
        size_mb = os.path.getsize(dist) / (1024 * 1024)
        print(f"\nDone!  {dist}  ({size_mb:.1f} MB)")
        print("Share this single file with other users - no Python needed.")
    else:
        print("\nBuild failed. Check the logs above and make sure dist/RollerCoin-bot.exe is not running.")
        sys.exit(result.returncode or 1)


if __name__ == "__main__":
    main()
