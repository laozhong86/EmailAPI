import time
import sys
import logging
import json
import os
import pathlib
import threading
import random
import queue
from flask import Flask, request, jsonify
from typing import Optional, Dict, Any

# --- Path Setup ---
# Add project root to sys.path to allow importing src.api etc.
script_path = pathlib.Path(__file__).resolve()
project_root = script_path.parent.parent.parent # Navigate up from src/Email/src to project root
src_root = project_root / 'src' # Just the src directory, might be needed if api expects imports relative to src
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_root))
# Try importing the API module after path setup
try:
    # Adjust the import path based on the actual structure if needed
    # Assuming cloud_email_api.py is directly inside src/Email/src/api
    from src.api import cloud_email_api
    email_api_available = True
    logging.info("Successfully imported cloud_email_api.")
except ImportError as e:
    logging.error(f"Failed to import cloud_email_api: {e}. Email processing will be skipped.")
    email_api_available = False
# --- End Path Setup ---

# --- 导入配置管理器 ---
try:
    from src.config.config_manager import load_config
    config = load_config()
    logging.info("成功加载配置")
except ImportError as e:
    logging.error(f"加载配置管理器失败: {e}，将使用默认配置")
    config = {
        'api': {
            'base_url': os.getenv('API_BASE_URL', 'https://oauth.882263.xyz'),
            'host': os.getenv('API_HOST', 'localhost'),
            'port': int(os.getenv('API_PORT', 5001)),
            'debug': os.getenv('API_DEBUG', 'false').lower() == 'true'
        },
        'email': {
            'lease_duration_seconds': int(os.getenv('LEASE_DURATION_SECONDS', 600)),
            'cleanup_interval_seconds': int(os.getenv('CLEANUP_INTERVAL_SECONDS', 3600)),
            'concurrency': 1
        }
    }

# --- Flask App Setup ---
app = Flask(__name__)
API_PORT = config['api']['port']  # 从配置获取端口
email_accounts_path = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'email_accounts.json'
# --- End Flask App Setup ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s')

# --- Configuration ---
# 使用配置中的并发设置
if 'email' in config and 'concurrency' in config['email']:
    concurrency_value = config['email']['concurrency']
else:
    concurrency_value = 1

# 兼容旧格式
config_local = {
    'concurrency': concurrency_value
}

# --- Lease Mechanism (Scheme 2) ---
email_leases = {}  # {"email@example.com": timestamp}
lease_lock = threading.Lock()  # Thread lock for accessing email_leases
LEASE_DURATION_SECONDS = config['email']['lease_duration_seconds']
cleanup_interval_seconds = config['email']['cleanup_interval_seconds']
cleanup_timer = None

# --- API Endpoints ---

@app.route('/request-email', methods=['GET'])
def request_email():
    """
    Allocates an available email address and creates a lease for it.
    Also performs cleanup of expired leases.
    """
    # Define oauth_dir_path within the function scope
    oauth_dir_path = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'oauth'

    # Perform lease cleanup
    with lease_lock:
        current_time = time.time()
        expired_leases = [email for email, timestamp in email_leases.items() 
                         if current_time - timestamp > LEASE_DURATION_SECONDS]
        for email in expired_leases:
            email_leases.pop(email, None)
            logging.info(f"Cleaned up expired lease for email: {email}")

    available_files = []
    try:
        # Ensure oauth_dir_path is accessible
        if not oauth_dir_path.exists():
            logging.error(f"OAuth directory not found: {oauth_dir_path}")
            return jsonify({"error": "Internal server error: Configuration issue."}), 500

        # Find all .json files that do NOT end with .used
        all_json_files = list(oauth_dir_path.glob('*.json'))
        available_files = [f for f in all_json_files if f.is_file() and not f.name.endswith('.used')]
        logging.debug(f"Found potential email files: {[f.name for f in available_files] if available_files else 'None'}")
    except Exception as e:
        logging.error(f"Error accessing oauth directory {oauth_dir_path}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error while listing email accounts."}), 500

    if not available_files:
        logging.warning("No available email account files found in oauth directory.")
        # Return 409 Conflict as specified in docs
        return jsonify({"error": "No available email accounts at the moment."}), 409

    random.shuffle(available_files)  # Shuffle to distribute usage

    assigned_email = None
    with lease_lock:  # Acquire lock to check and update email_leases safely
        current_leased_emails = set(email_leases.keys())
        logging.debug(f"Currently leased emails: {current_leased_emails}")

        for file_path in available_files:
            try:
                # Convert filename back to email (e.g., user_at_domain.com.json -> user@domain.com)
                if file_path.suffix == '.json' and '_at_' in file_path.stem:
                    email_candidate = file_path.stem.replace('_at_', '@')
                else:
                    logging.warning(f"Skipping file with unexpected name format: {file_path.name}")
                    continue

                if email_candidate not in current_leased_emails:
                    email_leases[email_candidate] = time.time()
                    assigned_email = email_candidate
                    logging.info(f"Assigned and leased email: {assigned_email}")
                    break  # Exit loop once assigned
            except Exception as e:
                logging.error(f"Error processing file {file_path.name} for leasing: {e}", exc_info=True)
                continue  # Try next file

    if assigned_email:
        return jsonify({"email": assigned_email, "lease_duration_seconds": LEASE_DURATION_SECONDS}), 200
    else:
        logging.warning("Found email files, but all are currently leased.")
        # Return 409 Conflict as specified in docs
        return jsonify({"error": "No available email accounts at the moment."}), 409

@app.route('/get-latest-email', methods=['POST'])
def get_latest_email():
    """
    Retrieves the latest email for a leased email address.
    Returns the raw email data to the client.
    """
    data = request.get_json()
    if not data or 'email' not in data:
        logging.warning("/get-latest-email request missing 'email' in body.")
        return jsonify({"error": "Missing 'email' in request body."}), 400

    email = data['email']
    logging.info(f"Received request for latest email for: {email}")

    # Check lease validity
    with lease_lock:
        if email not in email_leases:
            logging.warning(f"Request for non-leased email: {email}")
            return jsonify({"error": "Email not found or lease expired."}), 404
        
        lease_time = email_leases.get(email, 0)
        if time.time() - lease_time > LEASE_DURATION_SECONDS:
            # Lease expired
            email_leases.pop(email, None)
            logging.warning(f"Lease expired for email: {email}")
            return jsonify({"error": "Email lease expired."}), 404

    # Construct paths
    oauth_dir_path = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'oauth'
    filename_base = email.replace('@', '_at_')
    original_path = oauth_dir_path / f"{filename_base}.json"

    # Read credentials
    try:
        if not original_path.is_file():
            logging.error(f"Credential file not found for leased email {email}: {original_path}")
            return jsonify({"error": "Credential file not found."}), 500

        with open(original_path, 'r', encoding='utf-8') as f:
            account_data = json.load(f)
            refresh_token = account_data.get('refresh_token')
            client_id = account_data.get('client_id')
            
            if not refresh_token or not client_id:
                logging.error(f"Missing 'refresh_token' or 'client_id' in {original_path}")
                return jsonify({"error": "Invalid credential file."}), 500
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {original_path}", exc_info=True)
        return jsonify({"error": "Invalid JSON in credential file."}), 500
    except Exception as e:
        logging.error(f"Error reading credential file {original_path}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to read credential file: {str(e)}"}), 500

    # Call cloud API to get the latest email
    try:
        result = cloud_email_api.get_latest_email(refresh_token, client_id, email)
        if result:
            logging.info(f"Raw response from cloud_email_api for {email}: {json.dumps(result, indent=2, ensure_ascii=False)}") # Log the raw response
            logging.info(f"Successfully fetched email data for {email}")
            return jsonify({"success": True, "data": result}), 200
        else:
            logging.warning(f"Received empty response from cloud_email_api for {email}.")
            return jsonify({"success": True, "data": None}), 200
    except Exception as e:
        logging.error(f"Error calling cloud_email_api for {email}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to retrieve email from cloud API: {str(e)}"}), 500

@app.route('/mark-email-used', methods=['POST'])
def mark_email_used():
    """
    Marks a leased email as used by renaming its credential file and removing the lease.
    """
    data = request.get_json()
    if not data or 'email' not in data:
        logging.warning("/mark-email-used request missing 'email' in body.")
        return jsonify({"error": "Missing 'email' in request body."}), 400

    email = data['email']
    logging.info(f"Received request to mark email as used: {email}")

    # Check lease validity
    with lease_lock:
        if email not in email_leases:
            logging.warning(f"Request to mark non-leased email as used: {email}")
            return jsonify({"error": "Email not found or lease expired."}), 404
        
        lease_time = email_leases.get(email, 0)
        if time.time() - lease_time > LEASE_DURATION_SECONDS:
            # Lease expired
            email_leases.pop(email, None)
            logging.warning(f"Lease expired for email: {email}")
            return jsonify({"error": "Email lease expired."}), 404

    # Construct paths
    oauth_dir_path = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'oauth'
    filename_base = email.replace('@', '_at_')
    original_path = oauth_dir_path / f"{filename_base}.json"
    used_path = oauth_dir_path / f"{filename_base}.json.used"

    # Rename the file to mark as used
    try:
        if used_path.exists():
            logging.warning(f"Used file {used_path.name} already exists. Assuming already marked.")
        elif original_path.exists():
            os.rename(original_path, used_path)
            logging.info(f"Marked email as used by renaming {original_path.name} to {used_path.name}")
        else:
            logging.error(f"Original file {original_path.name} not found for marking as used.")
            return jsonify({"error": "Credential file not found."}), 500
    except OSError as e:
        logging.error(f"Failed to rename {original_path.name} to {used_path.name}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to mark email as used: {str(e)}"}), 500

    # Remove the lease
    with lease_lock:
        email_leases.pop(email, None)
        logging.info(f"Removed lease for email: {email}")

    return jsonify({"message": "Email marked as used."}), 200

@app.route('/release-email', methods=['POST'])
def release_email():
    """
    Releases the lease on an email address.
    """
    data = request.get_json()
    if not data or 'email' not in data:
        logging.warning("/release-email request missing 'email' in body.")
        return jsonify({"error": "Missing 'email' in request body."}), 400

    email = data['email']
    logging.info(f"Received request to release email lease: {email}")

    # Remove the lease
    with lease_lock:
        if email in email_leases:
            email_leases.pop(email)
            logging.info(f"Released lease for email: {email}")
        else:
            logging.info(f"No active lease found for {email} during release request.")

    return jsonify({"message": "Email lease released."}), 200

@app.route('/clear-mailbox', methods=['POST'])
def clear_mailbox_route():
    """
    Clears the mailbox for a specified email address using the external API.
    """
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"error": "Missing 'email' in request body"}), 400

    email = data['email']
    logging.info(f"Received request to clear mailbox for: {email}")

    # Define oauth_dir_path within the function scope
    oauth_dir_path = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'oauth'
    # credential_file = oauth_dir_path / f"{email}.json"
    # Use the consistent '_at_' format for the filename
    credential_file = oauth_dir_path / f"{email.replace('@', '_at_')}.json"

    if not credential_file.exists():
        logging.error(f"Credential file not found for {email} at {credential_file}")
        return jsonify({"error": f"Email credentials not found or email not leased: {email}"}), 404

    try:
        with open(credential_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)

        refresh_token = account_data.get('refresh_token')
        client_id = account_data.get('client_id')

        if not refresh_token or not client_id:
            logging.error(f"Missing credentials in file for {email}")
            return jsonify({"error": "Incomplete credentials for email"}), 500

        # Attempt to clear the mailbox using the imported API module
        success = cloud_email_api.clear_mailbox(
            refresh_token=refresh_token,
            client_id=client_id,
            email=email,
            mailbox="INBOX" # Assuming INBOX is always the target
        )

        if success:
            logging.info(f"Successfully cleared mailbox for {email}")
            return jsonify({"success": True, "message": f"Mailbox for {email} cleared successfully."}), 200
        else:
            logging.error(f"Failed to clear mailbox for {email} via API.")
            return jsonify({"success": False, "error": f"Failed to clear mailbox for {email}. Check API logs."}), 500

    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in credential file for {email}: {credential_file}")
        return jsonify({"error": "Internal server error reading credentials"}), 500
    except FileNotFoundError:
         # This case might be redundant due to the initial check, but good practice
        logging.error(f"Credential file disappeared for {email}: {credential_file}")
        return jsonify({"error": "Email credentials not found"}), 404
    except Exception as e:
        logging.error(f"Error during mailbox clearing for {email}: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error while clearing mailbox for {email}"}), 500

# 添加清理函数
def cleanup_used_emails(max_age_hours=48):
    """
    清理超过指定时间的已使用邮箱文件
    """
    oauth_dir_path = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'oauth'
    current_time = time.time()
    deleted_count = 0
    
    try:
        for file_path in oauth_dir_path.glob('*.json.used'):
            file_stat = file_path.stat()
            file_age_hours = (current_time - file_stat.st_mtime) / 3600
            
            if file_age_hours > max_age_hours:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logging.info(f"已删除超过{max_age_hours}小时的已使用邮箱文件: {file_path.name}")
                except OSError as e:
                    logging.error(f"删除文件失败 {file_path.name}: {e}")
        
        logging.info(f"清理完成，共删除{deleted_count}个过期邮箱文件")
        return deleted_count
    except Exception as e:
        logging.error(f"清理已使用邮箱文件时出错: {e}")
        return 0

# 添加API端点
@app.route('/cleanup-used-emails', methods=['POST'])
def cleanup_used_emails_route():
    """
    清理超过指定时间的已使用邮箱文件的API端点
    """
    data = request.get_json() or {}
    max_age_hours = data.get('max_age_hours', 48)  # 默认48小时
    
    try:
        deleted_count = cleanup_used_emails(max_age_hours)
        return jsonify({
            "success": True,
            "message": f"清理完成，共删除{deleted_count}个过期邮箱文件",
            "deleted_count": deleted_count
        }), 200
    except Exception as e:
        logging.error(f"清理已使用邮箱文件API出错: {e}")
        return jsonify({
            "success": False,
            "error": f"清理过程中出错: {str(e)}"
        }), 500

# --- Main Execution / Service Start ---
def start_service(host=None, port=None, debug=None):
    """Starts the Flask email service."""
    global cleanup_timer
    
    # 使用参数或配置值
    host = host or config['api']['host']
    port = port or config['api']['port']
    debug = debug if debug is not None else config['api']['debug']
    
    # Load configuration (example - adjust path as needed)
    # config_file = pathlib.Path(__file__).resolve().parent.parent / 'config' / 'email_config.json'
    # load_config(config_file)

    # Clear any stale leases from previous runs
    logging.info("Clearing any stale in-memory leases...")
    with lease_lock:
        email_leases.clear()
    
    # 启动定期清理任务
    def schedule_cleanup():
        global cleanup_timer
        cleanup_used_emails()
        cleanup_timer = threading.Timer(cleanup_interval_seconds, schedule_cleanup)
        cleanup_timer.daemon = True
        cleanup_timer.start()
    
    # Start initial cleanup
    schedule_cleanup()
    
    # Use threaded=True if Flask's default development server needs to handle concurrent requests better
    # For production, consider using a proper WSGI server like Gunicorn or Waitress
    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except Exception as e:
        logging.exception(f"Flask server encountered an error: {e}")  # Log exception before exit
        # 取消定时器
        if cleanup_timer:
            cleanup_timer.cancel()
            cleanup_timer = None
        # Perform any necessary cleanup before exiting
        raise  # Re-raise the exception if needed

# --- Task Loading ---
def load_tasks():
    script_dir = pathlib.Path(__file__).parent.resolve()
    # 正确导航到OAuth目录：从src/Email/src到Email/data/oauth
    oauth_dir = script_dir.parent / 'data' / 'oauth'
    oauth_dir = oauth_dir.resolve()

    logging.info(f"Scanning for task files in: {oauth_dir}")
    if not oauth_dir.is_dir():
        logging.warning(f"OAuth directory not found: {oauth_dir}. No tasks loaded.")
        # 创建目录以确保它存在
        oauth_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created OAuth directory: {oauth_dir}")
        return 0

    count = 0
    for item in oauth_dir.glob('*.json'):
        if item.is_file():
            task_queue.put(str(item))  # Add absolute path string to queue
            count += 1
            logging.debug(f"Added task: {item}")
    logging.info(f"Loaded {count} tasks into the queue.")
    return count

# --- Worker Logic ---
def email_worker():
    if not email_api_available:
        logging.warning("Email API not available, worker cannot process tasks.")
        return  # Stop the worker if API cannot be loaded

    while True:
        task_file_path = None  # Ensure variable is defined
        try:
            task_file_path = task_queue.get(timeout=1)  # Wait 1 sec then check again
            if task_file_path is None:  # Sentinel value to stop
                logging.info("Worker received stop signal. Exiting.")
                break

            logging.info(f"Processing task: {os.path.basename(task_file_path)}")

            # --- Actual Task Processing ---
            try:
                with open(task_file_path, 'r', encoding='utf-8') as f:
                    account_data = json.load(f)

                email = account_data.get('email')
                client_id = account_data.get('client_id')  # Or appropriate key
                refresh_token = account_data.get('refresh_token')  # Or appropriate key

                if not all([email, client_id, refresh_token]):
                    logging.error(f"Missing required data (email, client_id, refresh_token) in {task_file_path}. Skipping.")
                else:
                    # Call the API function - replace 'process_email_task' if needed
                    result = cloud_email_api.process_email_task(email, client_id, refresh_token)
                    logging.info(f"API call result for {email}: {result}")  # Log the result

            except json.JSONDecodeError:
                logging.error(f"Invalid JSON in task file: {task_file_path}. Skipping.")
            except KeyError as e:
                logging.error(f"Missing key {e} in task file: {task_file_path}. Skipping.")
            except FileNotFoundError:
                logging.error(f"Task file not found (maybe deleted?): {task_file_path}. Skipping.")
            except Exception as e:
                # Catch errors from the API call itself or other issues
                logging.error(f"Error during processing task {os.path.basename(task_file_path)}: {e}")
            # --- End Task Processing ---

            logging.info(f"Finished task: {os.path.basename(task_file_path)}")

            task_queue.task_done()
        except queue.Empty:
            # Queue is empty, loop again to check for sentinel or new tasks
            continue
        except Exception as e:
            logging.error(f"Error processing task {os.path.basename(task_file_path) if task_file_path else 'unknown'}: {e}")
            # Decide if the task should be marked done or retried
            if task_file_path is not None:
                task_queue.task_done()  # Mark as done to avoid blocking queue join

if __name__ == "__main__":
    # Example: Start the service directly if this script is run
    # In a real application, this might be called from another module or managed process
    try:
        start_service()  # 使用配置中的值
    except KeyboardInterrupt:
        logging.info("Email service stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logging.critical(f"Email service failed to start or crashed: {e}", exc_info=True)
