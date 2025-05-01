# Email应用打包脚本
# 使用PyInstaller将Python应用打包为单文件exe

# 参数定义
param (
    [string]$OutputName = "img2vid.exe",  # 输出文件名
    [switch]$SkipInstall = $false         # 是否跳过依赖安装
)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 显示打包信息
Write-Host "===== Email应用打包脚本 =====" -ForegroundColor Cyan
Write-Host "输出文件: $OutputName" -ForegroundColor Cyan

# 获取脚本所在目录作为项目根目录
$ProjectRoot = $PSScriptRoot
Write-Host "项目根目录: $ProjectRoot" -ForegroundColor Cyan

# 导入版本信息
$VersionFile = Join-Path $ProjectRoot "__version__.py"
if (Test-Path $VersionFile) {
    $VersionContent = Get-Content $VersionFile -Raw
    if ($VersionContent -match "__version__\s*=\s*['""](.+)['""]") {
        $Version = $matches[1]
        Write-Host "当前版本: $Version" -ForegroundColor Green
    } else {
        Write-Host "无法从__version__.py解析版本号，将使用默认版本" -ForegroundColor Yellow
        $Version = "0.0.0"
    }
} else {
    Write-Host "未找到__version__.py，将使用默认版本" -ForegroundColor Yellow
    $Version = "0.0.0"
}

# 安装依赖
if (-not $SkipInstall) {
    Write-Host "`n正在安装依赖..." -ForegroundColor Cyan
    $RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
    
    if (Test-Path $RequirementsFile) {
        try {
            python -m pip install --upgrade pip
            python -m pip install -r $RequirementsFile
            Write-Host "依赖安装完成" -ForegroundColor Green
        } catch {
            Write-Host "依赖安装失败: $_" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "未找到requirements.txt文件" -ForegroundColor Yellow
    }
}

# 创建临时规范文件
$SpecContent = @"
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['$ProjectRoot'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 添加数据文件
a.datas += [('__version__.py', '$ProjectRoot\\__version__.py', 'DATA')]

# 添加.env.example文件作为示例配置
a.datas += [('.env.example', '$ProjectRoot\\.env.example', 'DATA')]

# 添加config.ini.example文件（如果存在）
if os.path.exists('$ProjectRoot\\config.ini.example'):
    a.datas += [('config.ini.example', '$ProjectRoot\\config.ini.example', 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='$OutputName',
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
    version='file_version_info.txt',
    icon=None,
)
"@

$SpecFile = Join-Path $ProjectRoot "email_app.spec"
$SpecContent | Out-File -FilePath $SpecFile -Encoding utf8

# 创建版本信息文件
$VersionInfoContent = @"
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=($($Version.Split('.') + @(0, 0, 0, 0) | Select-Object -First 4 -Skip 0 | ForEach-Object { $_ -replace "[^0-9]", "0" }) -join ', '),
    prodvers=($($Version.Split('.') + @(0, 0, 0, 0) | Select-Object -First 4 -Skip 0 | ForEach-Object { $_ -replace "[^0-9]", "0" }) -join ', '),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404b0',
        [StringStruct(u'CompanyName', u''),
        StringStruct(u'FileDescription', u'Email应用'),
        StringStruct(u'FileVersion', u'$Version'),
        StringStruct(u'InternalName', u'email_app'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2025'),
        StringStruct(u'OriginalFilename', u'$OutputName'),
        StringStruct(u'ProductName', u'Email应用'),
        StringStruct(u'ProductVersion', u'$Version')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
"@

$VersionInfoFile = Join-Path $ProjectRoot "file_version_info.txt"
$VersionInfoContent | Out-File -FilePath $VersionInfoFile -Encoding utf8

# 执行PyInstaller打包
Write-Host "`n开始打包..." -ForegroundColor Cyan
try {
    # 使用生成的spec文件进行打包
    $PyInstallerCmd = "pyinstaller --clean --onefile --distpath='$ProjectRoot\dist' '$SpecFile'"
    Write-Host "执行命令: $PyInstallerCmd" -ForegroundColor DarkGray
    Invoke-Expression $PyInstallerCmd
    
    # 检查打包结果
    $OutputPath = Join-Path $ProjectRoot "dist\$OutputName"
    if (Test-Path $OutputPath) {
        Write-Host "打包成功: $OutputPath" -ForegroundColor Green
        
        # 计算SHA-256哈希值
        $SHA256 = Get-FileHash -Path $OutputPath -Algorithm SHA256
        $HashValue = $SHA256.Hash.ToLower()
        
        # 保存哈希值到文件
        $HashPath = "$OutputPath.sha256"
        "$HashValue *$OutputName" | Out-File -FilePath $HashPath -Encoding utf8 -NoNewline
        Write-Host "SHA-256: $HashValue" -ForegroundColor Green
        Write-Host "哈希值已保存到: $HashPath" -ForegroundColor Green
        
        # 显示文件大小
        $FileSize = (Get-Item $OutputPath).Length
        $FileSizeMB = [math]::Round($FileSize / 1MB, 2)
        Write-Host "文件大小: $FileSizeMB MB" -ForegroundColor Cyan
        
        # 检查文件大小是否超过限制
        if ($FileSizeMB -gt 150) {
            Write-Host "警告: 文件大小超过150MB限制" -ForegroundColor Yellow
        }
    } else {
        Write-Host "打包失败: 未找到输出文件" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "打包过程中出错: $_" -ForegroundColor Red
    exit 1
} finally {
    # 清理临时文件
    if (Test-Path $SpecFile) { Remove-Item $SpecFile }
    if (Test-Path $VersionInfoFile) { Remove-Item $VersionInfoFile }
}

Write-Host "`n===== 打包完成 =====" -ForegroundColor Cyan
