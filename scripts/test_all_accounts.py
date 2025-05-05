#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import logging
import sys
import os
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

def test_get_latest_email(account_file):
    """测试单个账号的获取最新邮件API调用"""
    try:
        with open(account_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)
        
        email = account_data.get('email')
        refresh_token = account_data.get('refresh_token')
        client_id = account_data.get('client_id')
        
        if not all([email, refresh_token, client_id]):
            return (email, False, "账号文件缺少必要信息")
        
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
                    return (email, True, "成功")
                else:
                    return (email, False, f"API返回失败: {data.get('message', '未知错误')}")
            except json.JSONDecodeError:
                return (email, False, "无法解析JSON响应")
        else:
            return (email, False, f"请求失败，状态码: {response.status_code}")
    
    except Exception as e:
        return (email if 'email' in locals() else account_file.stem, False, f"异常: {str(e)}")

def main():
    # 读取所有账号文件
    data_dir = Path("E:/projects/GXGen2/Apps/Email/data/oauth")
    account_files = list(data_dir.glob("*.json"))
    
    # 排除备份文件
    account_files = [f for f in account_files if not f.name.endswith('.bak')]
    
    if not account_files:
        logging.error("未找到账号文件")
        return
    
    logging.info(f"找到 {len(account_files)} 个账号文件")
    
    # 测试所有账号
    results = []
    working_accounts = []
    
    # 使用线程池加速测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_account = {executor.submit(test_get_latest_email, account_file): account_file for account_file in account_files}
        for future in concurrent.futures.as_completed(future_to_account):
            account_file = future_to_account[future]
            try:
                email, success, message = future.result()
                results.append((email, success, message))
                if success:
                    working_accounts.append(account_file)
            except Exception as e:
                logging.error(f"处理 {account_file} 时发生错误: {e}")
    
    # 输出结果
    logging.info("\n=== 测试结果 ===")
    
    # 成功的账号
    successful_accounts = [r[0] for r in results if r[1]]
    logging.info(f"成功获取邮件的账号 ({len(successful_accounts)}/{len(results)}):")
    for email in successful_accounts:
        logging.info(f"  - {email}")
    
    # 失败的账号
    failed_accounts = [(r[0], r[2]) for r in results if not r[1]]
    logging.info(f"\n获取邮件失败的账号 ({len(failed_accounts)}/{len(results)}):")
    for email, message in failed_accounts:
        logging.info(f"  - {email}: {message}")
    
    # 如果找到工作账号，提供更新建议
    if working_accounts:
        logging.info(f"\n找到 {len(working_accounts)} 个工作正常的账号，可以用于更新应用程序")
        logging.info(f"建议使用的账号: {working_accounts[0].stem.replace('_at_', '@')}")
    else:
        logging.error("未找到任何工作正常的账号，请检查API服务器状态或获取新的账号")

if __name__ == "__main__":
    main()
