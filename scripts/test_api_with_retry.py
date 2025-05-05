#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import logging
import sys
import os
import time
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

def test_get_latest_email(refresh_token, client_id, email, mailbox="INBOX", timeout=30, max_retries=3, retry_delay=5):
    """测试获取最新邮件的API调用，带有重试逻辑"""
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
    logging.info(f"超时设置: {timeout}秒, 最大重试次数: {max_retries}, 重试延迟: {retry_delay}秒")
    
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"尝试 #{attempt}...")
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
                    # 解析错误，继续重试
            else:
                logging.error(f"请求失败，状态码: {response.status_code}")
                logging.error(f"响应内容: {response.text}")
                # 检查是否是超时错误
                if response.status_code == 500 and "Timed out" in response.text:
                    logging.warning("检测到超时错误，将在延迟后重试")
                else:
                    # 其他错误，可能不适合重试
                    logging.warning("非超时错误，但仍将尝试重试")
            
            # 如果不是最后一次尝试，则等待后重试
            if attempt < max_retries:
                logging.info(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                logging.error(f"已达到最大重试次数 ({max_retries})，放弃")
                
        except requests.exceptions.Timeout:
            logging.error(f"请求超时 (客户端超时设置: {timeout}秒)")
            if attempt < max_retries:
                logging.info(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                logging.error(f"已达到最大重试次数 ({max_retries})，放弃")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"请求异常: {e}")
            if attempt < max_retries:
                logging.info(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                logging.error(f"已达到最大重试次数 ({max_retries})，放弃")
    
    return None

def test_alternative_endpoint(refresh_token, client_id, email, timeout=30):
    """测试备用端点 - 获取所有邮件而不是最新邮件"""
    endpoint = "/api/mail-all"
    api_url = BASE_URL + endpoint
    
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "email": email,
        "mailbox": "INBOX"
    }
    
    logging.info(f"尝试备用端点: {api_url}...")
    
    try:
        response = requests.get(api_url, params=params, timeout=timeout)
        logging.info(f"备用端点响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logging.info(f"备用端点响应: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
                return data
            except json.JSONDecodeError:
                logging.error(f"无法解析备用端点JSON响应")
                return None
        else:
            logging.error(f"备用端点请求失败: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"备用端点请求异常: {e}")
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
        
        # 1. 尝试使用更长的超时时间
        logging.info("=== 测试 1: 增加超时时间 ===")
        result1 = test_get_latest_email(refresh_token, client_id, email, timeout=60, max_retries=2)
        
        # 2. 尝试备用端点
        logging.info("\n=== 测试 2: 尝试备用端点 ===")
        result2 = test_alternative_endpoint(refresh_token, client_id, email, timeout=60)
        
        # 总结结果
        logging.info("\n=== 测试结果总结 ===")
        logging.info(f"测试 1 (增加超时): {'成功' if result1 and result1.get('success') else '失败'}")
        logging.info(f"测试 2 (备用端点): {'成功' if result2 and result2.get('success') else '失败'}")
        
        if not (result1 and result1.get('success')) and not (result2 and result2.get('success')):
            logging.warning("所有测试都失败，可能是API服务器问题或凭据问题")
            logging.info("建议:")
            logging.info("1. 稍后重试，API服务器可能暂时不可用")
            logging.info("2. 检查refresh_token是否需要更新")
            logging.info("3. 联系API服务提供商获取支持")
    
    except Exception as e:
        logging.error(f"执行过程中发生错误: {e}", exc_info=True)

if __name__ == "__main__":
    main()
