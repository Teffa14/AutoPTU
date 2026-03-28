# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['auto_ptu_web_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('auto_ptu', 'auto_ptu'),
        ('files', 'files'),
        ('Foundry', 'Foundry'),
        ('reports', 'reports'),
        ('IMPLEMENTATION FILES', 'IMPLEMENTATION FILES'),
        ('PTUDatabase-main\\PTUDataEditor\\Resources\\Types', 'PTUDatabase-main\\PTUDataEditor\\Resources\\Types'),
    ],
    hiddenimports=['uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.websockets', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['scripts\\pyinstaller_rth_env.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    [],
    exclude_binaries=True,
    name='AutoPTUWeb',
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoPTUWeb',
)
