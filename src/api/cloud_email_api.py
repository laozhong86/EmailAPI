import requests
import logging
import os
from typing import Optional, List, Dict, Any

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API 配置 - 从环境变量获取
BASE_URL = os.getenv('API_BASE_URL', 'https://oauth.882263.xyz')

def _make_request(endpoint: str, params: Dict[str, Any], timeout: int) -> Optional[requests.Response]:
    """内部辅助函数，用于发送 GET 请求并处理基本错误。"""
    api_url = BASE_URL + endpoint
    try:
        response = requests.get(api_url, params=params, timeout=timeout)
        response.raise_for_status() # 检查 HTTP 错误状态码 (4xx or 5xx)
        return response
    except requests.exceptions.Timeout:
        logging.error(f"请求 {api_url} 超时 ({timeout} 秒)。")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"请求 {api_url} 失败: {e}")
        return None
    except Exception as e:
        logging.error(f"请求 {api_url} 时发生未知错误: {e}")
        return None

def get_latest_email(refresh_token: str, client_id: str, email: str, mailbox: str = "INBOX", timeout: int = 30) -> Optional[Dict[str, Any]]:
    """
    调用云端 API 获取指定邮箱的最新一封邮件。

    Args:
        refresh_token: 用于认证的 OAuth refresh token。
        client_id: 应用程序的 client ID。
        email: 目标邮箱地址。
        mailbox: 要查询的邮箱文件夹 (默认为 "INBOX")。
        timeout: 请求超时时间 (秒，默认为 30)。

    Returns:
        包含邮件信息的字典 (如 'send', 'subject', 'date', 'content')，
        如果 API 调用失败或未找到邮件则返回 None。
    """
    endpoint = "/api/mail-new"
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "email": email,
        "mailbox": mailbox
    }
    logging.info(f"正在向 {BASE_URL}{endpoint} 请求最新邮件 (邮箱: {email}, 邮箱文件夹: {mailbox})...")
    response = _make_request(endpoint, params, timeout)

    if response:
        try:
            data = response.json()
            if data.get("success"):
                logging.info(f"成功获取最新邮件。")
                return data.get("data") # data 可能为 null 或包含邮件内容的字典
            else:
                error_msg = data.get("message", "未知错误")
                logging.error(f"API 调用失败 (最新邮件): {error_msg}")
                return None
        except requests.exceptions.JSONDecodeError:
            logging.error(f"无法解析 API 响应 (最新邮件): {response.text}")
            return None
    return None

def get_all_emails(refresh_token: str, client_id: str, email: str, mailbox: str = "INBOX", timeout: int = 60) -> Optional[List[Dict[str, Any]]]:
    """
    调用云端 API 获取指定邮箱的所有邮件。

    Args:
        refresh_token: 用于认证的 OAuth refresh token。
        client_id: 应用程序的 client ID。
        email: 目标邮箱地址。
        mailbox: 要查询的邮箱文件夹 (默认为 "INBOX")。
        timeout: 请求超时时间 (秒，默认为 60，因为获取所有邮件可能耗时更长)。

    Returns:
        包含邮件信息字典的列表，如果 API 调用失败或没有邮件则返回 None。
    """
    endpoint = "/api/mail-all"
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "email": email,
        "mailbox": mailbox
    }
    logging.info(f"正在向 {BASE_URL}{endpoint} 请求所有邮件 (邮箱: {email}, 邮箱文件夹: {mailbox})...")
    # 注意：获取所有邮件可能需要更长的超时时间
    response = _make_request(endpoint, params, timeout)

    if response:
        try:
            data = response.json()
            if data.get("success"):
                emails = data.get("data", []) # data 应该是一个列表
                logging.info(f"成功获取 {len(emails)} 封邮件。")
                return emails
            else:
                error_msg = data.get("message", "未知错误")
                logging.error(f"API 调用失败 (所有邮件): {error_msg}")
                return None
        except requests.exceptions.JSONDecodeError:
            logging.error(f"无法解析 API 响应 (所有邮件): {response.text}")
            return None
    return None

def clear_mailbox(refresh_token: str, client_id: str, email: str, mailbox: str = "INBOX", timeout: int = 30) -> bool:
    """
    调用云端 API 清空指定邮箱的文件夹。

    Args:
        refresh_token: 用于认证的 OAuth refresh token。
        client_id: 应用程序的 client ID。
        email: 目标邮箱地址。
        mailbox: 要清空的邮箱文件夹 (默认为 "INBOX")。
        timeout: 请求超时时间 (秒，默认为 30)。

    Returns:
        如果清空操作成功则返回 True，否则返回 False。
    """
    # endpoint = "/api/mail-clear" # Incorrect endpoint based on previous tests
    endpoint = "/api/process-inbox" # Correct endpoint based on testing
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "email": email,
        "mailbox": mailbox
    }
    logging.info(f"正在向 {BASE_URL}{endpoint} 请求清空邮箱 (邮箱: {email}, 邮箱文件夹: {mailbox})...")
    response = _make_request(endpoint, params, timeout)

    if response:
        try:
            data = response.json()
            if data.get("success"):
                logging.info(f"成功清空邮箱文件夹 {mailbox}。")
                return True
            else:
                error_msg = data.get("message", "未知错误")
                logging.error(f"API 调用失败 (清空邮箱): {error_msg}")
                return False
        except requests.exceptions.JSONDecodeError:
            logging.error(f"无法解析 API 响应 (清空邮箱): {response.text}")
            return False
    return False

# 可以在这里添加一些简单的测试代码
if __name__ == '__main__':
    print("这是一个 API 封装模块，请在其他脚本中导入并使用这些函数。")
    # 示例：需要从某处获取真实的凭证来测试
    # test_email = "your_test_email@example.com"
    # test_client_id = "your_client_id"
    # test_refresh_token = "your_refresh_token"
    #
    # latest = get_latest_email(test_refresh_token, test_client_id, test_email)
    # if latest:
    #     print("\nLatest Email:")
    #     print(latest)
    #
    # all_emails = get_all_emails(test_refresh_token, test_client_id, test_email)
    # if all_emails:
    #     print(f"\nAll Emails ({len(all_emails)}):")
    #     # print(all_emails) # 打印所有邮件可能很长
    #
    # cleared = clear_mailbox(test_refresh_token, test_client_id, test_email)
    # print(f"\nMailbox cleared: {cleared}")
