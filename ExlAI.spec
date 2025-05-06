# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app/ui/integrated_ui.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('app/ui/history_rules.json', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='ExlAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico',
) 