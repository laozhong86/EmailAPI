import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

def load_config(env_path=None, config_dir=None):
    """
    加载配置信息，包括.env文件和JSON配置
    
    Args:
        env_path: .env文件路径，默认为项目根目录下的.env
        config_dir: 配置文件目录，默认为当前文件所在目录
    
    Returns:
        包含所有配置的字典
    """
    # 设置默认路径
    if env_path is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        env_path = project_root / '.env'
    
    if config_dir is None:
        config_dir = Path(__file__).resolve().parent
    
    # 加载.env文件
    load_dotenv(dotenv_path=env_path)
    
    # 创建基本配置字典
    config = {
        'api': {
            'base_url': os.getenv('API_BASE_URL', 'https://oauth.882263.xyz'),
            'host': os.getenv('API_HOST', 'localhost'),
            'port': int(os.getenv('API_PORT', 5001)),
            'debug': os.getenv('API_DEBUG', 'false').lower() == 'true'
        },
        'email': {
            'lease_duration_seconds': int(os.getenv('LEASE_DURATION_SECONDS', 600)),
            'cleanup_interval_seconds': int(os.getenv('CLEANUP_INTERVAL_SECONDS', 3600))
        }
    }
    
    # 加载环境特定配置
    environment = os.getenv('ENVIRONMENT', 'dev')
    env_config_path = config_dir / f"{environment}.json"
    
    if env_config_path.exists():
        try:
            with open(env_config_path, 'r') as f:
                env_config = json.load(f)
                # 递归合并配置
                deep_merge(config, env_config)
        except Exception as e:
            logging.error(f"加载环境配置文件失败: {e}")
    
    # 加载通用服务配置（向后兼容）
    service_config_path = config_dir / "email_service_config.json"
    if service_config_path.exists():
        try:
            with open(service_config_path, 'r') as f:
                service_config = json.load(f)
                # 将并发配置从旧文件迁移到新结构
                if 'concurrency' in service_config:
                    config['email']['concurrency'] = service_config['concurrency']
        except Exception as e:
            logging.error(f"加载服务配置文件失败: {e}")
    
    return config

def deep_merge(source, update):
    """递归合并两个字典"""
    for key, value in update.items():
        if key in source and isinstance(source[key], dict) and isinstance(value, dict):
            deep_merge(source[key], value)
        else:
            source[key] = value
