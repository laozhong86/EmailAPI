# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('__version__.py', '.'), ('.env.example', '.'), ('config.ini.example', '.')]
binaries = [('C:\\ProgramData\\anaconda3\\Library\\bin\\libexpat.dll', '.'), ('C:\\ProgramData\\anaconda3\\Library\\bin\\libssl-3-x64.dll', '.'), ('C:\\ProgramData\\anaconda3\\Library\\bin\\libcrypto-3-x64.dll', '.'), ('C:\\ProgramData\\anaconda3\\Library\\bin\\ffi.dll', '.')]
hiddenimports = ['flask', 'src.api.cloud_email_api', 'src.config.config_manager', 'xml.parsers.expat']
tmp_ret = collect_all('xml')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('email')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pkg_resources')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('plistlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=['.\\src'],
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
    a.binaries,
    a.datas,
    [],
    name='emailAPI.exe',
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
