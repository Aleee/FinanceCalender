# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FinanceCalender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='designer/icons/app.png',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='FinanceCalender',
)
app = BUNDLE(
    coll,
    name='Платежный календарь.app',
    icon='designer/icons/app.png',
    bundle_identifier=None,
    info_plist={
        'CFBundleName': 'Платежный календарь',
        'CFBundleDisplayName': 'Платежный календарь',
    },
)
