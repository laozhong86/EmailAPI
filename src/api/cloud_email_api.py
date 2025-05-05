import requests
import logging
import os
import imaplib
import email as email_module
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
import chardet
import re
import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# IMAP 服务器配置
IMAP_SERVER = 'outlook.office365.com'
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

def get_new_access_token(refresh_token: str, client_id: str) -> Optional[str]:
    """
    使用刷新令牌获取新的访问令牌。

    Args:
        refresh_token: OAuth2 刷新令牌。
        client_id: 应用程序的 client ID。

    Returns:
        成功时返回访问令牌，失败时返回 None。
    """
    logging.info("正在尝试刷新 access token...")
    
    if not refresh_token:
        logging.error("无效或未配置 Refresh Token。")
        return None
    if not client_id:
        logging.error("无效或未配置 Client ID。")
        return None

    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'scope': 'https://outlook.office.com/IMAP.AccessAsUser.All offline_access',
    }

    try:
        logging.debug(f"请求 Token URL: {TOKEN_URL}")
        response = requests.post(TOKEN_URL, data=token_data)
        logging.debug(f"Token 响应状态码: {response.status_code}")
        response.raise_for_status()  # 对于错误状态码(4xx或5xx)抛出异常
        token_info = response.json()
        
        if 'access_token' in token_info:
            logging.info("成功获取新的 access token。")
            return token_info['access_token']
        else:
            logging.error(f"刷新 token 失败: {token_info.get('error_description', token_info.get('error', '未知错误'))}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"请求 token 时出错: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"响应状态码: {e.response.status_code}, 响应内容: {e.response.text}")
        return None
    except json.JSONDecodeError:
        logging.error(f"解析 token 响应时出错。响应内容: {response.text}")
        return None

def connect_to_imap(email_address: str, access_token: str) -> Tuple[Optional[imaplib.IMAP4_SSL], bool]:
    """
    连接到 IMAP 服务器并使用 OAuth2 进行认证。

    Args:
        email_address: 邮箱地址。
        access_token: OAuth2 访问令牌。

    Returns:
        成功时返回 (IMAP 连接对象, True)，失败时返回 (None, False)。
    """
    try:
        logging.info(f"正在连接到 IMAP 服务器: {IMAP_SERVER}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        logging.info("连接成功。")
        
        auth_string = f"user={email_address}\1auth=Bearer {access_token}\1\1"
        logging.info("正在使用 XOAUTH2 进行认证...")
        mail.authenticate('XOAUTH2', lambda x: auth_string.encode('utf-8'))
        logging.info("认证成功。")
        
        return mail, True
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP 错误: {e}")
        return None, False
    except Exception as e:
        logging.error(f"连接到 IMAP 服务器时发生意外错误: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def decode_mime_words(s: str) -> str:
    """解码邮件头部（如主题）中可能使用 MIME 编码的文本。"""
    if not s:
        return ""
    try:
        decoded_fragments = decode_header(s)
        return ''.join([
            str(fragment, encoding or 'utf-8') if isinstance(fragment, bytes) else fragment
            for fragment, encoding in decoded_fragments
        ])
    except Exception as e:
        logging.error(f"解码头部时出错: {s}, 错误: {e}")
        return s  # 出错时返回原始字符串

def strip_html(content: str) -> str:
    """从字符串中移除 HTML 标签。"""
    if not content:
        return ""
    soup = BeautifulSoup(content, "html.parser")
    return soup.get_text()

def safe_decode(byte_content: bytes) -> str:
    """使用检测到的编码或 UTF-8 解码字节内容。"""
    if not byte_content:
        return ""
    try:
        result = chardet.detect(byte_content)
        encoding = result['encoding']
        if encoding:
            return byte_content.decode(encoding, errors='replace')
        else:
            # 如果检测失败，尝试常见编码
            for enc in ['utf-8', 'iso-8859-1', 'windows-1252']:
                try:
                    return byte_content.decode(enc)
                except UnicodeDecodeError:
                    continue
            return byte_content.decode('utf-8', errors='ignore')  # 最后的备选方案
    except Exception as e:
        logging.error(f"解码内容时出错: {e}")
        return ""

def remove_extra_blank_lines(text: str) -> str:
    """移除文本中多余的空行。"""
    if not text:
        return ""
    # 将多个空行替换为单个空行
    return re.sub(r'\n\s*\n', '\n\n', text)

def parse_email_message(msg: email_module.message.Message) -> Dict[str, Any]:
    """
    解析邮件消息为字典格式。

    Args:
        msg: email_module.message.Message 对象。

    Returns:
        包含邮件信息的字典。
    """
    try:
        # 解析基本信息
        subject = decode_mime_words(msg.get("subject", "No Subject"))
        sender = decode_mime_words(msg.get("from", "No Sender"))
        date_str = msg.get("date", "")
        
        # 尝试解析日期为 ISO 格式
        date_iso = ""
        try:
            if date_str:
                dt = parsedate_to_datetime(date_str)
                date_iso = dt.isoformat()
        except Exception as e:
            logging.warning(f"解析日期时出错: {date_str}, 错误: {e}")
        
        # 解析邮件正文
        body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # 提取文本或 HTML 部分（非附件）
                if part.get_content_maintype() == 'text' and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    if payload:
                        part_content = safe_decode(payload)
                        if content_type == "text/html":
                            html_body += part_content
                            body += strip_html(part_content) + "\n"
                        else:  # 假设是 text/plain
                            body += part_content + "\n"
        else:  # 非多部分邮件
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                part_content = safe_decode(payload)
                if content_type == "text/html":
                    html_body = part_content
                    body = strip_html(part_content)
                elif content_type == "text/plain":
                    body = part_content
        
        # 清理正文
        body = remove_extra_blank_lines(body.strip())
        
        # 构建返回的字典
        email_dict = {
            "sender": sender,
            "subject": subject,
            "date": date_str,
            "date_iso": date_iso,
            "content": body,
            "html_content": html_body if html_body else None,
            # 可以根据需要添加更多字段
        }
        
        return email_dict
    except Exception as e:
        logging.error(f"解析邮件时出错: {e}")
        import traceback
        traceback.print_exc()
        return {
            "sender": "解析错误",
            "subject": "解析错误",
            "date": "",
            "content": f"解析邮件时出错: {str(e)}",
            "error": str(e)
        }

def get_latest_email(refresh_token: str, client_id: str, email: str, mailbox: str = "INBOX", timeout: int = 30) -> Optional[Dict[str, Any]]:
    """
    使用 IMAP 获取指定邮箱的最新一封邮件。

    Args:
        refresh_token: 用于认证的 OAuth refresh token。
        client_id: 应用程序的 client ID。
        email: 目标邮箱地址。
        mailbox: 要查询的邮箱文件夹 (默认为 "INBOX")。
        timeout: 请求超时时间 (秒，默认为 30)。

    Returns:
        包含邮件信息的字典 (如 'sender', 'subject', 'date', 'content')，
        如果操作失败或未找到邮件则返回 None。
    """
    mail = None
    
    try:
        # 设置超时
        imaplib.IMAP4_SSL.timeout = timeout
        
        # 获取访问令牌
        access_token = get_new_access_token(refresh_token, client_id)
        if not access_token:
            return None
        
        # 连接到 IMAP 服务器
        mail, success = connect_to_imap(email, access_token)
        if not success or not mail:
            return None
        
        # 选择邮箱文件夹
        logging.info(f"正在选择邮箱文件夹: {mailbox}...")
        status, select_data = mail.select(mailbox, readonly=True)
        if status != 'OK':
            logging.error(f"选择邮箱文件夹 '{mailbox}' 失败: {status} - {select_data}")
            return None
        
        # 获取邮件数量
        message_count = int(select_data[0].decode())
        logging.info(f"文件夹 '{mailbox}' 包含 {message_count} 封邮件。")
        
        if message_count == 0:
            logging.info(f"文件夹 '{mailbox}' 中没有邮件。")
            return None
        
        # 获取最新一封邮件的 ID
        status, message_ids_bytes = mail.search(None, 'ALL')
        if status != 'OK':
            logging.error(f"搜索邮件失败: {status}")
            return None
        
        message_ids = message_ids_bytes[0].split()
        if not message_ids:
            logging.info(f"文件夹 '{mailbox}' 中没有找到邮件。")
            return None
        
        # 获取最新一封邮件（最后一个 ID）
        latest_id = message_ids[-1]
        logging.info(f"正在获取最新邮件 (ID: {latest_id.decode()})...")
        
        status, message_data = mail.fetch(latest_id, '(RFC822)')
        if status != 'OK':
            logging.error(f"获取邮件内容失败: {status}")
            return None
        
        # 解析邮件内容
        raw_email = message_data[0][1]
        
        # 添加详细的调试日志
        raw_email_type = type(raw_email)
        raw_email_preview = str(raw_email)[:100] + "..." if len(str(raw_email)) > 100 else str(raw_email)
        logging.debug(f"raw_email 类型: {raw_email_type}, 值预览: {raw_email_preview}")
        
        # 添加类型检查，根据 raw_email 的类型使用不同的函数
        if isinstance(raw_email, bytes):
            logging.debug("使用 email_module.message_from_bytes 处理字节类型数据")
            msg = email_module.message_from_bytes(raw_email)
        elif isinstance(raw_email, str):
            logging.debug("使用 email_module.message_from_string 处理字符串类型数据")
            msg = email_module.message_from_string(raw_email)
        else:
            logging.error(f"无法处理的邮件内容类型: {raw_email_type}")
            return None
        
        # 解析邮件为字典格式
        email_dict = parse_email_message(msg)
        logging.info(f"成功获取最新邮件: {email_dict.get('subject', '无主题')}")
        
        return email_dict
        
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP 错误: {e}")
        return None
    except Exception as e:
        logging.error(f"获取最新邮件时发生意外错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
                logging.info("IMAP 连接已关闭。")
            except Exception as e:
                logging.warning(f"关闭 IMAP 连接时出错: {e}")

def get_all_emails(refresh_token: str, client_id: str, email: str, mailbox: str = "INBOX", timeout: int = 60) -> Optional[List[Dict[str, Any]]]:
    """
    使用 IMAP 获取指定邮箱的所有邮件。

    Args:
        refresh_token: 用于认证的 OAuth refresh token。
        client_id: 应用程序的 client ID。
        email: 目标邮箱地址。
        mailbox: 要查询的邮箱文件夹 (默认为 "INBOX")。
        timeout: 请求超时时间 (秒，默认为 60，因为获取所有邮件可能耗时更长)。

    Returns:
        包含邮件信息字典的列表，如果操作失败或没有邮件则返回 None。
    """
    mail = None
    
    try:
        # 设置超时
        imaplib.IMAP4_SSL.timeout = timeout
        
        # 获取访问令牌
        access_token = get_new_access_token(refresh_token, client_id)
        if not access_token:
            return None
        
        # 连接到 IMAP 服务器
        mail, success = connect_to_imap(email, access_token)
        if not success or not mail:
            return None
        
        # 选择邮箱文件夹
        logging.info(f"正在选择邮箱文件夹: {mailbox}...")
        status, select_data = mail.select(mailbox, readonly=True)
        if status != 'OK':
            logging.error(f"选择邮箱文件夹 '{mailbox}' 失败: {status} - {select_data}")
            return None
        
        # 获取邮件数量
        message_count = int(select_data[0].decode())
        logging.info(f"文件夹 '{mailbox}' 包含 {message_count} 封邮件。")
        
        if message_count == 0:
            logging.info(f"文件夹 '{mailbox}' 中没有邮件。")
            return []
        
        # 获取所有邮件的 ID
        status, message_ids_bytes = mail.search(None, 'ALL')
        if status != 'OK':
            logging.error(f"搜索邮件失败: {status}")
            return None
        
        message_ids = message_ids_bytes[0].split()
        if not message_ids:
            logging.info(f"文件夹 '{mailbox}' 中没有找到邮件。")
            return []
        
        # 获取所有邮件
        all_emails = []
        logging.info(f"正在获取 {len(message_ids)} 封邮件...")
        
        # 为了提高性能，可以考虑批量获取或限制获取的邮件数量
        for msg_id in message_ids:
            try:
                status, message_data = mail.fetch(msg_id, '(RFC822)')
                if status != 'OK':
                    logging.warning(f"获取邮件 ID {msg_id.decode()} 内容失败: {status}")
                    continue
                
                # 解析邮件内容
                raw_email = message_data[0][1]
                
                # 添加详细的调试日志
                raw_email_type = type(raw_email)
                raw_email_preview = str(raw_email)[:100] + "..." if len(str(raw_email)) > 100 else str(raw_email)
                logging.debug(f"raw_email 类型: {raw_email_type}, 值预览: {raw_email_preview}")
                
                # 添加类型检查，根据 raw_email 的类型使用不同的函数
                if isinstance(raw_email, bytes):
                    logging.debug("使用 email_module.message_from_bytes 处理字节类型数据")
                    msg = email_module.message_from_bytes(raw_email)
                elif isinstance(raw_email, str):
                    logging.debug("使用 email_module.message_from_string 处理字符串类型数据")
                    msg = email_module.message_from_string(raw_email)
                else:
                    logging.warning(f"无法处理的邮件内容类型: {raw_email_type}, 邮件 ID: {msg_id.decode()}")
                    continue
                
                # 解析邮件为字典格式
                email_dict = parse_email_message(msg)
                all_emails.append(email_dict)
                
                logging.debug(f"已获取邮件: {email_dict.get('subject', '无主题')}")
            except Exception as e:
                logging.warning(f"处理邮件 ID {msg_id.decode()} 时出错: {e}")
        
        logging.info(f"成功获取 {len(all_emails)} 封邮件。")
        return all_emails
        
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP 错误: {e}")
        return None
    except Exception as e:
        logging.error(f"获取所有邮件时发生意外错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
                logging.info("IMAP 连接已关闭。")
            except Exception as e:
                logging.warning(f"关闭 IMAP 连接时出错: {e}")

def clear_mailbox(refresh_token: str, client_id: str, email: str, mailbox: str = "INBOX", timeout: int = 30) -> bool:
    """
    使用 IMAP 清空指定邮箱的文件夹。

    Args:
        refresh_token: 用于认证的 OAuth refresh token。
        client_id: 应用程序的 client ID。
        email: 目标邮箱地址。
        mailbox: 要清空的邮箱文件夹 (默认为 "INBOX")。
        timeout: 请求超时时间 (秒，默认为 30)。

    Returns:
        如果清空操作成功则返回 True，否则返回 False。
    """
    mail = None
    
    try:
        # 设置超时
        imaplib.IMAP4_SSL.timeout = timeout
        
        # 获取访问令牌
        access_token = get_new_access_token(refresh_token, client_id)
        if not access_token:
            return False
        
        # 连接到 IMAP 服务器
        mail, success = connect_to_imap(email, access_token)
        if not success or not mail:
            return False
        
        # 选择邮箱文件夹
        logging.info(f"正在选择邮箱文件夹: {mailbox}...")
        status, select_data = mail.select(mailbox)  # 非只读模式
        if status != 'OK':
            logging.error(f"选择邮箱文件夹 '{mailbox}' 失败: {status} - {select_data}")
            return False
        
        # 获取邮件数量
        message_count = int(select_data[0].decode())
        logging.info(f"文件夹 '{mailbox}' 包含 {message_count} 封邮件。")
        
        if message_count == 0:
            logging.info(f"文件夹 '{mailbox}' 中没有邮件需要清空。")
            return True  # 没有邮件也算成功
        
        # 搜索所有邮件
        logging.info(f"正在搜索文件夹 '{mailbox}' 中的所有邮件...")
        status, message_ids_bytes = mail.search(None, 'ALL')
        if status != 'OK':
            logging.error(f"搜索邮件失败: {status}")
            return False
        
        message_ids = message_ids_bytes[0].split()
        if not message_ids:
            logging.info(f"文件夹 '{mailbox}' 中没有找到邮件。")
            return True  # 没有邮件也算成功
        
        # 标记所有邮件为删除
        logging.info(f"正在标记 {len(message_ids)} 封邮件为删除...")
        marked_count = 0
        
        for msg_id in message_ids:
            status, store_data = mail.store(msg_id, '+FLAGS', r'\Deleted')
            if status == 'OK':
                marked_count += 1
            else:
                logging.warning(f"标记邮件 ID {msg_id.decode()} 为删除失败: {status} - {store_data}")
        
        logging.info(f"成功标记 {marked_count}/{len(message_ids)} 封邮件为删除。")
        
        # 执行永久删除
        if marked_count > 0:
            logging.info("正在永久删除已标记的邮件 (Expunge)...")
            status, expunge_data = mail.expunge()
            
            if status == 'OK':
                deleted_count = len(expunge_data) if expunge_data and expunge_data[0] is not None else marked_count
                if expunge_data and expunge_data[0] is None:
                    logging.info(f"Expunge 操作成功执行，但返回数据为 [None]。假定所有标记邮件已删除 ({marked_count} 封)。")
                else:
                    logging.info(f"成功永久删除 {deleted_count} 封邮件。")
                
                return True
            else:
                logging.error(f"永久删除邮件 (Expunge) 失败: {status} - {expunge_data}")
                return False
        else:
            logging.info("没有成功标记的邮件，无需执行 Expunge。")
            # 如果标记失败但没有邮件需要标记，也算成功
            return len(message_ids) == 0 or marked_count == len(message_ids)
        
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP 错误: {e}")
        return False
    except Exception as e:
        logging.error(f"清空邮箱时发生意外错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
                logging.info("IMAP 连接已关闭。")
            except Exception as e:
                logging.warning(f"关闭 IMAP 连接时出错: {e}")

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
