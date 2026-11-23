# -*- mode: python ; coding: utf-8 -*-
"""
CS-01 Full-Stack DPDP Compliance Auditor — PyInstaller Build Specification.

Produces a unified --onedir distribution directory containing:
  - cs01-gui.exe: Windowed desktop GUI application (zero console flicker)
  - cs01.exe:     Console CLI tool for terminal scans and CI scripting
  - _internal/:   Shared Python 3.11 runtime, PySide6 DLLs, and Tree-sitter binaries
"""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
PROJECT_ROOT = Path(SPECPATH).resolve()

# Collect data files
datas = [
    (str(PROJECT_ROOT / "cs01" / "rules"), "rules"),
    (str(PROJECT_ROOT / "assets"), "assets"),
    (
        str(PROJECT_ROOT / "cs01" / "cs01" / "pipeline" / "stage6_report" / "visualizer" / "vendor"),
        "cs01/pipeline/stage6_report/visualizer/vendor",
    ),
]

# Explicit hidden imports to guarantee dynamic reflection works
hiddenimports = [
    "cs01",
    "cs01.cli.main",
    "cs01.gui.__main__",
    "cs01.pipeline.runner",
    "tree_sitter",
    "tree_sitter_language_pack",
    "ruamel.yaml",
    "sqlglot",
    "hcl2",
    "dockerfile_parse",
    "jinja2",
    "pydantic",
    "pydantic_settings",
    "rich",
    "rich.console",
    "rich.progress",
    "rich.panel",
    "rich.table",
    "rich.markdown",
    "typer",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

# Collect any submodules for tree-sitter language pack
hiddenimports += collect_submodules("tree_sitter_language_pack")
hiddenimports += collect_submodules("sqlglot.dialects")

icon_path = str(PROJECT_ROOT / "assets" / "cs01.ico")

# 1. Analysis for GUI Application
a_gui = Analysis(
    [str(PROJECT_ROOT / "cs01" / "cs01" / "gui" / "__main__.py")],
    pathex=[str(PROJECT_ROOT), str(PROJECT_ROOT / "cs01")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "IPython", "notebook"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_gui = PYZ(a_gui.pure, a_gui.zipped_data, cipher=block_cipher)

exe_gui = EXE(
    pyz_gui,
    a_gui.scripts,
    [],
    exclude_binaries=True,
    name="cs01-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed GUI — no command prompt popup
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

# 2. Analysis for CLI Application
a_cli = Analysis(
    [str(PROJECT_ROOT / "cs01" / "cs01" / "cli" / "main.py")],
    pathex=[str(PROJECT_ROOT), str(PROJECT_ROOT / "cs01")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "IPython", "notebook"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_cli = PYZ(a_cli.pure, a_cli.zipped_data, cipher=block_cipher)

exe_cli = EXE(
    pyz_cli,
    a_cli.scripts,
    [],
    exclude_binaries=True,
    name="cs01",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Console enabled for CLI output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

# 3. Collect into single directory distribution
coll = COLLECT(
    exe_gui,
    a_gui.binaries,
    a_gui.zipfiles,
    a_gui.datas,
    exe_cli,
    a_cli.binaries,
    a_cli.zipfiles,
    a_cli.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CS-01",
)
