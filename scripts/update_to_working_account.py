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
    更新邮箱账号信息，用工作正常的账号替换其他账号
    """
    # 定义文件路径
    data_dir = Path("E:/projects/GXGen2/Apps/Email/data/oauth")
    working_account_file = data_dir / "cfesck92733a_at_outlook.com.json"
    
    # 要更新的账号文件列表
    accounts_to_update = [
        data_dir / "jnospyn23617_at_outlook.com.json",
        data_dir / "cxvsadj39117_at_outlook.com.json"
    ]
    
    # 检查工作账号文件是否存在
    if not working_account_file.exists():
        logging.error(f"工作账号文件不存在: {working_account_file}")
        return False
    
    try:
        # 读取工作账号信息
        with open(working_account_file, 'r', encoding='utf-8') as f:
            working_account_data = json.load(f)
        
        # 更新每个账号文件
        for account_file in accounts_to_update:
            if account_file.exists():
                # 备份原始文件
                backup_file = account_file.with_suffix('.json.bak')
                if not backup_file.exists():  # 只有在备份不存在时才创建备份
                    shutil.copy2(account_file, backup_file)
                    logging.info(f"已备份账号文件到: {backup_file}")
                
                # 更新账号文件
                with open(account_file, 'r', encoding='utf-8') as f:
                    account_data = json.load(f)
                
                # 保留原始邮箱地址和密码，但使用工作账号的refresh_token
                account_data['refresh_token'] = working_account_data['refresh_token']
                
                with open(account_file, 'w', encoding='utf-8') as f:
                    json.dump(account_data, f, indent=4, ensure_ascii=False)
                
                logging.info(f"已更新账号 {account_file.stem} 的refresh_token")
            else:
                logging.warning(f"账号文件不存在: {account_file}")
        
        logging.info("所有账号更新完成")
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
