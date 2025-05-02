<#
.SYNOPSIS
    Email 应用打包脚本（PowerShell 版本）

.DESCRIPTION
    本脚本放在 scripts 目录下，会自动切换到项目根目录。
    支持 --skip-install 开关和自定义输出文件名。

.PARAMETER SkipInstall
    如果指定此开关，则跳过依赖安装。

.PARAMETER OutputName
    指定生成的可执行文件名，默认为 emailAPI.exe。
#>

param (
    [switch]$SkipInstall,
    [string]$OutputName = 'emailAPI.exe'
)

# 1. 计算脚本所在目录和项目根目录
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "===== Email App Packaging Script ====="
Write-Host "Output file: $OutputName"
Write-Host "Project root: $(Get-Location)"

# 2. 提取版本号
$Version = '0.0.0'
$verFile = Join-Path $ProjectRoot '__version__.py'
if (Test-Path $verFile) {
    $match = Get-Content $verFile | Select-String -Pattern "__version__\s*=\s*['""](.*)['""]"
    if ($match) { $Version = $match.Matches[0].Groups[1].Value }
}
Write-Host "Current version: $Version"

# 3. 安装依赖（可选）
if (-not $SkipInstall) {
    Write-Host; Write-Host "Installing dependencies..."
    & python -m pip install --upgrade pip
    & python -m pip install -r (Join-Path $ProjectRoot 'requirements.txt')
    Write-Host "Dependencies installation complete"
}

# 4. 检查 Python 环境
Write-Host; Write-Host "Checking Python environment..."
& python -c "import sys; print('Python version:', sys.version)"
& python -c "import sys; print('Platform:', sys.platform)"
& python -c "import sys; print('Prefix:', sys.prefix)"

# 5. 构建 PyInstaller 参数
Write-Host; Write-Host "Starting packaging..."
$psiArgs = @(
    '--clean',
    '--onefile',
    "--name=$OutputName",
    '--paths', '.\src',
    '--hidden-import=flask',
    '--hidden-import=src.api.cloud_email_api',
    '--hidden-import=src.config.config_manager',
    '--add-data=__version__.py;.',
    '--add-data=.env.example;.'
)

if (Test-Path 'config.ini.example') { $psiArgs += '--add-data=config.ini.example;.' }

# 6. 修复运行时模块缺失
$psiArgs += @(
    '--hidden-import=xml.parsers.expat',
    '--collect-all=xml',
    '--collect-all=email',
    '--collect-all=pkg_resources',
    '--collect-all=plistlib'
)

# 7. 查找 Python DLLs 目录
$pythonExe    = (Get-Command python).Source
$pythonBinDir = Split-Path -Parent $pythonExe
$pythonDllDir = Join-Path $pythonBinDir 'DLLs'
Write-Host "Python DLLs path: $pythonDllDir"

foreach ($dll in @('pyexpat.pyd','libexpat.dll')) {
    $path = Join-Path $pythonDllDir $dll
    if (Test-Path $path) {
        $psiArgs += "--add-binary=$path;."
        Write-Host "Added $dll"
    }
}

# 8. 收集可能的 Anaconda DLL 路径
$condaBins = @()
if ($env:CONDA_PREFIX) {
    $p = Join-Path $env:CONDA_PREFIX 'Library\bin'
    if (Test-Path $p) { $condaBins += $p }
}
# 兼容默认安装位置
if (Test-Path 'C:\ProgramData\anaconda3\Library\bin') {
    $condaBins += 'C:\ProgramData\anaconda3\Library\bin'
}

# 9. 添加 Anaconda 相关 DLL
foreach ($bin in $condaBins) {
    foreach ($dll in @('libexpat.dll','libssl-3-x64.dll','libcrypto-3-x64.dll','ffi.dll')) {
        $path = Join-Path $bin $dll
        if (Test-Path $path) {
            $psiArgs += "--add-binary=$path;."
            Write-Host "Added $dll from $bin"
        }
    }
}

# 10. 指定 dist 目录和主脚本
$psiArgs += '--distpath=dist'
$psiArgs += 'main.py'

Write-Host "Executing PyInstaller with arguments:"
Write-Host ($psiArgs -join ' ') 

# 执行打包
& pyinstaller @psiArgs

# 11. 检查打包结果
$distFile = Join-Path 'dist' $OutputName
if (Test-Path $distFile) {
    Write-Host "Packaging successful: $distFile"
    $hash = (Get-FileHash -Algorithm SHA256 $distFile).Hash.ToLower()
    $hash | Out-File -Encoding ASCII "$distFile.sha256"
    Write-Host "SHA-256 hash saved to: $distFile.sha256"

    $sizeBytes = (Get-Item $distFile).Length
    $sizeMB    = [math]::Round($sizeBytes / 1MB, 2)
    Write-Host "File size: $sizeBytes bytes ($sizeMB MB)"
    if ($sizeMB -gt 150) { Write-Warning "Warning: File size exceeds 150MB limit" }
}
else {
    Write-Error "Packaging failed: Output file not found"
    exit 1
}

Write-Host; Write-Host "===== Packaging complete ====="
