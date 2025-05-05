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

def test_get_latest_email_post(refresh_token, client_id, email, mailbox="INBOX", timeout=30):
    """使用POST方法测试获取最新邮件的API调用"""
    endpoint = "/api/mail-new"
    api_url = BASE_URL + endpoint
    
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "email": email,
        "mailbox": mailbox
    }
    
    logging.info(f"正在向 {api_url} 发送POST请求...")
    logging.info(f"参数: email={email}, mailbox={mailbox}, client_id={client_id}")
    logging.info(f"refresh_token={refresh_token[:10]}...{refresh_token[-10:]}")
    
    try:
        # 使用POST方法而不是GET
        response = requests.post(api_url, data=params, timeout=timeout)
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

def test_get_junk_email(refresh_token, client_id, email, timeout=30):
    """测试获取垃圾邮件文件夹的最新邮件"""
    endpoint = "/api/mail-new"
    api_url = BASE_URL + endpoint
    
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "email": email,
        "mailbox": "Junk"  # 尝试垃圾邮件文件夹
    }
    
    logging.info(f"尝试获取垃圾邮件文件夹的邮件: {api_url}...")
    
    try:
        response = requests.get(api_url, params=params, timeout=timeout)
        logging.info(f"垃圾邮件文件夹响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logging.info(f"垃圾邮件文件夹响应: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
                return data
            except json.JSONDecodeError:
                logging.error(f"无法解析垃圾邮件文件夹JSON响应")
                return None
        else:
            logging.error(f"垃圾邮件文件夹请求失败: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"垃圾邮件文件夹请求异常: {e}")
        return None

def main():
    # 读取凭据文件
    oauth_file = Path("E:/projects/GXGen2/Apps/Email/data/oauth/jnospyn23617_at_outlook.com.json")
    
    if not oauth_file.exists():
        logging.error(f"凭据文件不存在: {oauth_file}")
        return
    
    try:
        with open(oauth_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)
            
        email = account_data.get('email')
        refresh_token = account_data.get('refresh_token')
        client_id = account_data.get('client_id')
        
        if not all([email, refresh_token, client_id]):
            logging.error("凭据文件缺少必要信息")
            return
        
        logging.info(f"测试邮箱: {email}")
        
        # 1. 尝试使用POST方法
        logging.info("=== 测试 1: 使用POST方法 ===")
        result1 = test_get_latest_email_post(refresh_token, client_id, email)
        
        # 2. 尝试获取垃圾邮件文件夹
        logging.info("\n=== 测试 2: 尝试获取垃圾邮件文件夹 ===")
        result2 = test_get_junk_email(refresh_token, client_id, email)
        
        # 总结结果
        logging.info("\n=== 测试结果总结 ===")
        logging.info(f"测试 1 (POST方法): {'成功' if result1 and result1.get('success') else '失败'}")
        logging.info(f"测试 2 (垃圾邮件文件夹): {'成功' if result2 and result2.get('success') else '失败'}")
        
        if not (result1 and result1.get('success')) and not (result2 and result2.get('success')):
            logging.warning("所有测试都失败，可能是API服务器问题")
            logging.info("建议:")
            logging.info("1. 检查API服务器状态，可能暂时不可用")
            logging.info("2. 检查refresh_token是否需要更新")
            logging.info("3. 联系API服务提供商获取支持")
    
    except Exception as e:
        logging.error(f"执行过程中发生错误: {e}", exc_info=True)

if __name__ == "__main__":
    main()
