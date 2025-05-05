#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import logging
import sys
import os
import shutil
from pathlib import Path
import concurrent.futures

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# API 配置
BASE_URL = "https://oauth.882263.xyz"

def test_account(account_file):
    """测试单个账号的获取最新邮件API调用"""
    try:
        with open(account_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)
        
        email = account_data.get('email')
        refresh_token = account_data.get('refresh_token')
        client_id = account_data.get('client_id')
        
        if not all([email, refresh_token, client_id]):
            return (account_file, email, False, "账号文件缺少必要信息")
        
        endpoint = "/api/mail-new"
        api_url = BASE_URL + endpoint
        
        params = {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "email": email,
            "mailbox": "INBOX"
        }
        
        response = requests.get(api_url, params=params, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("success"):
                    return (account_file, email, True, "成功")
                else:
                    return (account_file, email, False, f"API返回失败: {data.get('message', '未知错误')}")
            except json.JSONDecodeError:
                return (account_file, email, False, "无法解析JSON响应")
        else:
            return (account_file, email, False, f"请求失败，状态码: {response.status_code}")
    
    except Exception as e:
        email = account_data.get('email') if 'account_data' in locals() and account_data.get('email') else account_file.stem
        return (account_file, email, False, f"异常: {str(e)}")

def remove_failed_accounts():
    """删除所有请求失败的账号文件"""
    # 读取所有账号文件
    data_dir = Path("E:/projects/GXGen2/Apps/Email/data/oauth")
    account_files = list(data_dir.glob("*.json"))
    
    # 排除备份文件
    account_files = [f for f in account_files if not f.name.endswith('.bak')]
    
    if not account_files:
        logging.error("未找到账号文件")
        return
    
    logging.info(f"找到 {len(account_files)} 个账号文件")
    
    # 创建备份目录
    backup_dir = data_dir / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    # 测试所有账号
    results = []
    
    # 使用线程池加速测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_account = {executor.submit(test_account, account_file): account_file for account_file in account_files}
        for future in concurrent.futures.as_completed(future_to_account):
            account_file = future_to_account[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logging.error(f"处理 {account_file} 时发生错误: {e}")
    
    # 分类结果
    successful_accounts = [(f, e) for f, e, s, m in results if s]
    failed_accounts = [(f, e, m) for f, e, s, m in results if not s]
    
    # 输出结果
    logging.info("\n=== 测试结果 ===")
    logging.info(f"成功获取邮件的账号: {len(successful_accounts)}/{len(results)}")
    logging.info(f"获取邮件失败的账号: {len(failed_accounts)}/{len(results)}")
    
    # 移动失败的账号文件到备份目录
    if failed_accounts:
        logging.info("\n=== 开始移动失败账号文件 ===")
        for account_file, email, message in failed_accounts:
            try:
                # 检查是否是500错误
                if "状态码: 500" in message:
                    backup_path = backup_dir / account_file.name
                    shutil.move(account_file, backup_path)
                    logging.info(f"已移动失败账号文件: {email} -> {backup_path}")
            except Exception as e:
                logging.error(f"移动账号文件 {email} 时发生错误: {e}")
        
        logging.info(f"已移动 {len([f for f, e, m in failed_accounts if '状态码: 500' in m])} 个失败账号文件到 {backup_dir}")
    else:
        logging.info("没有找到失败的账号文件")
    
    # 输出成功账号列表
    if successful_accounts:
        logging.info("\n=== 成功账号列表 ===")
        for _, email in successful_accounts:
            logging.info(f"  - {email}")

if __name__ == "__main__":
    remove_failed_accounts()
