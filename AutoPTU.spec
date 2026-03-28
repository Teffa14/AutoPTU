# -*- mode: python ; coding: utf-8 -*-


from PyInstaller.utils.hooks import collect_data_files
from rich._unicode_data._versions import VERSIONS

rich_datas = collect_data_files("rich")
rich_unicode_modules = [f"rich._unicode_data.unicode{version.replace('.', '-')}" for version in VERSIONS]

a = Analysis(
    ['auto_ptu_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('auto_ptu\\data', 'auto_ptu\\data'),
        ('files', 'files'),
        ('Foundry', 'Foundry'),
        ('reports', 'reports'),
        ('IMPLEMENTATION FILES', 'IMPLEMENTATION FILES'),
        ('PTUDatabase-main\\PTUDataEditor\\Resources\\Types', 'PTUDatabase-main\\PTUDataEditor\\Resources\\Types'),
    ] + rich_datas,
    hiddenimports=rich_unicode_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['scripts\\pyinstaller_rth_env.py'],
    excludes=["numba", "llvmlite"],
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
    name='AutoPTU',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
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
    name='AutoPTU',
)
