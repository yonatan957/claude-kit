# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller --onedir build spec for the claude-kit CLI (research.md #8).

Build with:
    pyinstaller claude-kit.spec

Output: dist/claude-kit/ — a self-contained directory containing the
claude-kit executable and its runtime dependencies. The npm package's
postinstall.js (see npm/) fetches/unpacks the matching platform build of
this output; it is never committed to the repo itself.
"""

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
for pkg in ("textual", "typer", "pydantic"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ["src/cli.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="claude-kit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="claude-kit",
)
