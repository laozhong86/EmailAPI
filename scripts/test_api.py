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

def test_get_latest_email(refresh_token, client_id, email, mailbox="INBOX"):
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
        response = requests.get(api_url, params=params, timeout=30)
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
        result = test_get_latest_email(refresh_token, client_id, email)
        
        if result:
            if result.get("success"):
                logging.info("API调用成功")
                email_data = result.get("data")
                if email_data:
                    logging.info(f"邮件主题: {email_data.get('subject', '无主题')}")
                    logging.info(f"发件人: {email_data.get('from', '未知')}")
                    logging.info(f"日期: {email_data.get('date', '未知')}")
                else:
                    logging.warning("API返回成功但没有邮件数据")
            else:
                logging.error(f"API调用失败: {result.get('message', '未知错误')}")
        else:
            logging.error("API调用失败，无返回数据")
    
    except Exception as e:
        logging.error(f"执行过程中发生错误: {e}", exc_info=True)

if __name__ == "__main__":
    main()
