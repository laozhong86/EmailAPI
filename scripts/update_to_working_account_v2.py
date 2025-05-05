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

def update_to_working_account():
    """
    更新邮箱账号信息，用工作正常的账号替换有问题的账号
    """
    # 定义文件路径
    data_dir = Path("E:/projects/GXGen2/Apps/Email/data/oauth")
    
    # 工作正常的账号
    working_account_file = data_dir / "bgkoggc81767_at_outlook.com.json"
    
    # 要更新的账号文件
    problem_account_file = data_dir / "jnospyn23617_at_outlook.com.json"
    
    # 检查文件是否存在
    if not working_account_file.exists():
        logging.error(f"工作账号文件不存在: {working_account_file}")
        return False
    
    if not problem_account_file.exists():
        logging.error(f"问题账号文件不存在: {problem_account_file}")
        return False
    
    try:
        # 读取工作账号信息
        with open(working_account_file, 'r', encoding='utf-8') as f:
            working_account_data = json.load(f)
        
        # 读取问题账号信息
        with open(problem_account_file, 'r', encoding='utf-8') as f:
            problem_account_data = json.load(f)
        
        # 备份问题账号文件
        backup_file = problem_account_file.with_suffix('.json.bak2')
        shutil.copy2(problem_account_file, backup_file)
        logging.info(f"已备份问题账号文件到: {backup_file}")
        
        # 更新问题账号的refresh_token
        problem_account_data['refresh_token'] = working_account_data['refresh_token']
        
        # 保存更新后的问题账号文件
        with open(problem_account_file, 'w', encoding='utf-8') as f:
            json.dump(problem_account_data, f, indent=4, ensure_ascii=False)
        
        logging.info(f"已成功将账号 {problem_account_file.stem} 的refresh_token更新为工作账号 {working_account_file.stem} 的token")
        return True
    
    except Exception as e:
        logging.error(f"更新账号时发生错误: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = update_to_working_account()
    if success:
        logging.info("账号更新成功，请重新启动应用程序以使用更新后的账号")
    else:
        logging.error("账号更新失败")
