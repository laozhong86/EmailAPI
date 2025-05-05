#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import shutil
from pathlib import Path
import logging
import sys

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def update_email_account():
    """
    更新邮箱账号信息，用新账号替换旧账号
    """
    # 定义文件路径
    data_dir = Path("E:/projects/GXGen2/Apps/Email/data/oauth")
    old_account_file = data_dir / "jnospyn23617_at_outlook.com.json"
    new_account_file = data_dir / "cfesck92733a_at_outlook.com.json"
    
    # 检查文件是否存在
    if not old_account_file.exists():
        logging.error(f"旧账号文件不存在: {old_account_file}")
        return False
    
    if not new_account_file.exists():
        logging.error(f"新账号文件不存在: {new_account_file}")
        return False
    
    try:
        # 备份旧账号文件
        backup_file = old_account_file.with_suffix('.json.bak')
        shutil.copy2(old_account_file, backup_file)
        logging.info(f"已备份旧账号文件到: {backup_file}")
        
        # 读取新账号信息
        with open(new_account_file, 'r', encoding='utf-8') as f:
            new_account_data = json.load(f)
        
        # 更新旧账号文件
        with open(old_account_file, 'w', encoding='utf-8') as f:
            json.dump(new_account_data, f, indent=4, ensure_ascii=False)
        
        logging.info(f"已成功将账号 {old_account_file.stem} 更新为新账号 {new_account_file.stem} 的信息")
        return True
    
    except Exception as e:
        logging.error(f"更新账号时发生错误: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = update_email_account()
    if success:
        logging.info("账号更新成功，请重新启动应用程序以使用新账号")
    else:
        logging.error("账号更新失败")
