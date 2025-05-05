#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import logging
import sys
import os
from pathlib import Path
import shutil

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

def restore_original_account():
    """恢复原始账号文件"""
    data_dir = Path("E:/projects/GXGen2/Apps/Email/data/oauth")
    account_file = data_dir / "jnospyn23617_at_outlook.com.json"
    backup_file = data_dir / "jnospyn23617_at_outlook.com.json.bak"
    
    if backup_file.exists():
        shutil.copy2(backup_file, account_file)
        logging.info(f"已恢复原始账号文件")
        return True
    else:
        logging.error(f"备份文件不存在: {backup_file}")
        return False

def test_clear_mailbox(refresh_token, client_id, email, mailbox="INBOX", timeout=30):
    """测试清空邮箱的API调用"""
    endpoint = "/api/process-inbox"
    api_url = BASE_URL + endpoint
    
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "email": email
    }
    
    logging.info(f"正在向 {api_url} 发送清空邮箱请求...")
    logging.info(f"参数: email={email}, client_id={client_id}")
    logging.info(f"refresh_token={refresh_token[:10]}...{refresh_token[-10:]}")
    
    try:
        response = requests.get(api_url, params=params, timeout=timeout)
        logging.info(f"响应状态码: {response.status_code}")
        
        # 打印原始响应内容
        logging.info(f"原始响应内容: {response.text[:500]}...")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logging.info(f"响应JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return data
            except json.JSONDecodeError:
                logging.error(f"无法解析JSON响应: {response.text}")
                return None
        else:
            logging.error(f"请求失败，状态码: {response.status_code}")
            logging.error(f"响应内容: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"请求异常: {e}")
        return None

def test_get_latest_email(refresh_token, client_id, email, mailbox="INBOX", timeout=30):
    """测试获取最新邮件的API调用"""
    endpoint = "/api/mail-new"
    api_url = BASE_URL + endpoint
    
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "email": email,
        "mailbox": mailbox
    }
    
    logging.info(f"正在向 {api_url} 发送获取邮件请求...")
    logging.info(f"参数: email={email}, mailbox={mailbox}, client_id={client_id}")
    
    try:
        response = requests.get(api_url, params=params, timeout=timeout)
        logging.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logging.info(f"响应JSON: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
                return data
            except json.JSONDecodeError:
                logging.error(f"无法解析JSON响应: {response.text}")
                return None
        else:
            logging.error(f"请求失败，状态码: {response.status_code}")
            logging.error(f"响应内容: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"请求异常: {e}")
        return None

def main():
    # 恢复原始账号文件
    if not restore_original_account():
        logging.error("无法恢复原始账号文件，使用当前账号文件继续测试")
    
    # 读取账号文件
    oauth_file = Path("E:/projects/GXGen2/Apps/Email/data/oauth/jnospyn23617_at_outlook.com.json")
    
    if not oauth_file.exists():
        logging.error(f"账号文件不存在: {oauth_file}")
        return
    
    try:
        with open(oauth_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)
            
        email = account_data.get('email')
        refresh_token = account_data.get('refresh_token')
        client_id = account_data.get('client_id')
        
        if not all([email, refresh_token, client_id]):
            logging.error("账号文件缺少必要信息")
            return
        
        logging.info(f"测试邮箱: {email}")
        
        # 1. 先测试获取邮件
        logging.info("=== 测试 1: 获取最新邮件 ===")
        result1 = test_get_latest_email(refresh_token, client_id, email)
        
        # 2. 测试清空邮箱
        logging.info("\n=== 测试 2: 清空邮箱 ===")
        result2 = test_clear_mailbox(refresh_token, client_id, email)
        
        # 总结结果
        logging.info("\n=== 测试结果总结 ===")
        logging.info(f"测试 1 (获取邮件): {'成功' if result1 and result1.get('success') else '失败'}")
        logging.info(f"测试 2 (清空邮箱): {'成功' if result2 and result2.get('success') else '失败'}")
        
    except Exception as e:
        logging.error(f"执行过程中发生错误: {e}", exc_info=True)

if __name__ == "__main__":
    main()
