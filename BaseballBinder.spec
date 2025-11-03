# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all checklist CSV files
import os
checklist_files = []
if os.path.exists('checklists'):
    for root, dirs, files in os.walk('checklists'):
        for file in files:
            if file.endswith('.csv'):
                full_path = os.path.join(root, file)
                checklist_files.append((full_path, 'checklists'))

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('index.html', '.'),
        ('version.json', '.'),
        ('checklists', 'checklists'),
        ('models.py', '.'),
        ('main.py', '.'),
        ('config.py', '.'),
        ('ebay_api.py', '.'),
        ('rate_limiter.py', '.'),
        ('checklist_api.py', '.'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'sqlalchemy.ext.baked',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BaseballBinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console for server logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BaseballBinder',
)
