# -*- mode: python ; coding: utf-8 -*-
import os

openssl_dlls = [os.path.join('openssl', name) for name in ('libssl-3-x64.dll', 'libcrypto-3-x64.dll')]
missing = [path for path in openssl_dlls if not os.path.exists(path)]
if missing:
    raise SystemExit(f'Не найдены библиотеки OpenSSL: {missing}. Положите их в папку openssl/ (см. объяснение в чате).')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[(path, '.') for path in openssl_dlls],
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
