# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# 收集所有XML相关模块
xml_datas, xml_binaries, xml_hiddenimports = collect_all('xml')
email_datas, email_binaries, email_hiddenimports = collect_all('email')

# 寻找缺少的DLL文件路径
dll_paths = []
anaconda_lib = os.path.join(os.path.dirname(sys.executable), 'Library', 'bin')
conda_dll_path = r'C:\ProgramData\anaconda3\Library\bin'

dll_files = ['libexpat.dll', 'libssl-3-x64.dll', 'libcrypto-3-x64.dll', 'liblzma.dll', 'LIBBZ2.dll', 'ffi.dll']
dll_locations = [anaconda_lib, conda_dll_path]

for location in dll_locations:
    if os.path.exists(location):
        for dll in dll_files:
            dll_path = os.path.join(location, dll)
            if os.path.exists(dll_path):
                dll_paths.append((dll_path, '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=xml_binaries + email_binaries + dll_paths,
    datas=xml_datas + email_datas + [
        ('__version__.py', '.'),
        ('.env.example', '.'),
    ],
    hiddenimports=['xml.parsers.expat'] + xml_hiddenimports + email_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 如果存在config.ini.example，也添加到打包中
if os.path.exists('config.ini.example'):
    a.datas.append(('config.ini.example', 'config.ini.example', 'DATA'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='emailAPI',
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
