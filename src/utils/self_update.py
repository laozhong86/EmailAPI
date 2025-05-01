"""
自动更新模块
- 检查GitHub最新版本
- 下载新版本
- 校验SHA-256
- 替换当前文件并重启
"""

import os
import sys
import time
import json
import logging
import hashlib
import tempfile
import subprocess
import configparser
import requests
from packaging import version
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 获取应用版本
def get_app_version():
    """获取当前应用版本"""
    try:
        # 尝试从__version__.py导入版本
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        from __version__ import __version__
        return __version__
    except ImportError:
        logging.error("无法导入版本信息，将使用默认版本0.0.0")
        return "0.0.0"

def get_github_token():
    """从config.ini获取GitHub Token"""
    config_path = Path(sys.executable).parent / "config.ini" if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent.parent / "config.ini"
    
    if not config_path.exists():
        logging.info(f"配置文件不存在: {config_path}，将使用无认证模式访问GitHub API")
        return None
    
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        return config.get('GitHub', 'Token', fallback=None)
    except Exception as e:
        logging.error(f"读取GitHub Token失败: {e}")
        return None

def get_latest_release(owner="laozhong86", repo="EmailAPI"):
    """
    获取GitHub仓库的最新Release信息
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        
    Returns:
        dict: 包含最新版本信息的字典，如果出错则返回None
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {}
    
    # 如果有GitHub Token，添加到请求头
    token = get_github_token()
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"获取最新版本信息失败: {e}")
        return None

def download_file(url, target_path):
    """
    下载文件并保存到指定路径
    
    Args:
        url: 下载URL
        target_path: 保存路径
        
    Returns:
        bool: 下载成功返回True，否则返回False
    """
    headers = {}
    
    # 如果有GitHub Token，添加到请求头
    token = get_github_token()
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        # 保存文件
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.RequestException as e:
        logging.error(f"下载文件失败: {e}")
        return False

def calculate_sha256(file_path):
    """
    计算文件的SHA-256哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: SHA-256哈希值，如果出错则返回None
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.error(f"计算SHA-256失败: {e}")
        return None

def check_for_update(owner="laozhong86", repo="EmailAPI", exe_name="img2vid.exe"):
    """
    检查更新并在有新版本时自动更新
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        exe_name: 可执行文件名称
        
    Returns:
        bool: 如果有更新并成功更新返回True，否则返回False
    """
    logging.info("正在检查更新...")
    
    # 获取当前版本
    current_version = get_app_version()
    logging.info(f"当前版本: {current_version}")
    
    # 获取最新版本信息
    latest_release = get_latest_release(owner, repo)
    if not latest_release:
        logging.warning("无法获取最新版本信息，跳过更新检查")
        return False
    
    # 解析最新版本号（去掉v前缀）
    latest_version_str = latest_release.get("tag_name", "").lstrip("v")
    if not latest_version_str:
        logging.warning("无法解析最新版本号，跳过更新检查")
        return False
    
    logging.info(f"最新版本: {latest_version_str}")
    
    # 比较版本
    if version.parse(latest_version_str) <= version.parse(current_version):
        logging.info("已经是最新版本，无需更新")
        return False
    
    logging.info(f"发现新版本: {latest_version_str}，准备更新")
    
    # 查找可执行文件资源
    exe_asset = None
    for asset in latest_release.get("assets", []):
        if asset.get("name") == exe_name:
            exe_asset = asset
            break
    
    if not exe_asset:
        logging.warning(f"在最新版本中未找到{exe_name}，跳过更新")
        return False
    
    # 下载新版本
    download_url = exe_asset.get("browser_download_url")
    if not download_url:
        logging.warning("无法获取下载URL，跳过更新")
        return False
    
    # 创建临时目录用于下载
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, exe_name)
        logging.info(f"正在下载新版本到: {temp_file_path}")
        
        # 下载文件
        if not download_file(download_url, temp_file_path):
            logging.error("下载新版本失败，跳过更新")
            return False
        
        # 验证SHA-256（如果有提供）
        sha256_from_release = None
        for asset in latest_release.get("assets", []):
            if asset.get("name") == f"{exe_name}.sha256":
                sha_asset_url = asset.get("browser_download_url")
                if sha_asset_url:
                    try:
                        sha_response = requests.get(sha_asset_url, timeout=10)
                        sha_response.raise_for_status()
                        sha256_from_release = sha_response.text.strip().split(" ")[0]
                    except Exception as e:
                        logging.warning(f"获取SHA-256校验文件失败: {e}")
        
        if sha256_from_release:
            calculated_sha256 = calculate_sha256(temp_file_path)
            if calculated_sha256 != sha256_from_release:
                logging.error(f"SHA-256校验失败，跳过更新")
                logging.error(f"预期: {sha256_from_release}")
                logging.error(f"实际: {calculated_sha256}")
                return False
            logging.info("SHA-256校验通过")
        
        # 获取当前可执行文件路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            current_exe = sys.executable
        else:
            # 如果是开发环境，使用模拟路径
            current_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), exe_name)
        
        # 备份当前版本
        backup_path = f"{current_exe}.old"
        try:
            if os.path.exists(current_exe):
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(current_exe, backup_path)
                logging.info(f"已备份当前版本到: {backup_path}")
        except Exception as e:
            logging.error(f"备份当前版本失败: {e}")
            return False
        
        # 尝试替换文件
        try:
            # 复制新版本到当前位置
            import shutil
            shutil.copy2(temp_file_path, current_exe)
            logging.info(f"已更新到新版本: {latest_version_str}")
            
            # 启动新版本并退出当前进程
            logging.info("正在启动新版本...")
            subprocess.Popen([current_exe])
            sys.exit(0)
            
        except Exception as e:
            logging.error(f"替换文件失败: {e}")
            
            # 如果替换失败，尝试恢复备份
            try:
                if os.path.exists(backup_path):
                    os.rename(backup_path, current_exe)
                    logging.info("已恢复备份版本")
            except Exception as restore_error:
                logging.critical(f"恢复备份版本失败: {restore_error}，应用可能无法正常工作")
            
            return False
    
    # 不应该执行到这里，因为成功更新会退出进程
    return False

if __name__ == "__main__":
    # 测试更新功能
    check_for_update()
