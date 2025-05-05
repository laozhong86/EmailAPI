#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import logging
import sys
import os
from pathlib import Path

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
    
    logging.info(f"正在向 {api_url} 发送请求...")
    logging.info(f"参数: email={email}, mailbox={mailbox}, client_id={client_id}")
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

def test_clear_mailbox(refresh_token, client_id, email, timeout=30):
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

def test_multiple_times(account_file, num_tests=5):
    """多次测试同一个账号，检查结果的一致性"""
    try:
        with open(account_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)
            
        email = account_data.get('email')
        refresh_token = account_data.get('refresh_token')
        client_id = account_data.get('client_id')
        
        if not all([email, refresh_token, client_id]):
            logging.error("账号文件缺少必要信息")
            return
        
        logging.info(f"测试账号: {email}")
        logging.info(f"将进行 {num_tests} 次连续测试")
        
        # 多次测试获取邮件
        success_count = 0
        failure_count = 0
        
        for i in range(num_tests):
            logging.info(f"\n=== 测试 #{i+1}: 获取最新邮件 ===")
            result = test_get_latest_email(refresh_token, client_id, email)
            
            if result and result.get("success"):
                success_count += 1
                logging.info(f"测试 #{i+1} 成功")
            else:
                failure_count += 1
                logging.info(f"测试 #{i+1} 失败")
            
            # 短暂暂停，避免API限制
            if i < num_tests - 1:
                logging.info("等待2秒后进行下一次测试...")
                import time
                time.sleep(2)
        
        # 测试清空邮箱
        logging.info("\n=== 测试: 清空邮箱 ===")
        clear_result = test_clear_mailbox(refresh_token, client_id, email)
        
        # 总结结果
        logging.info("\n=== 测试结果总结 ===")
        logging.info(f"获取邮件成功率: {success_count}/{num_tests} ({success_count/num_tests*100:.1f}%)")
        logging.info(f"清空邮箱: {'成功' if clear_result and clear_result.get('success') else '失败'}")
        
    except Exception as e:
        logging.error(f"执行过程中发生错误: {e}", exc_info=True)

def main():
    # 测试特定账号
    account_file = Path("E:/projects/GXGen2/Apps/Email/data/oauth/ustfybr21084_at_outlook.com.json")
    
    if not account_file.exists():
        logging.error(f"账号文件不存在: {account_file}")
        return
    
    test_multiple_times(account_file, num_tests=5)

if __name__ == "__main__":
    main()
