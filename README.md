# Email 模块

本模块负责处理与电子邮件相关的操作，包括通过云端 API 获取邮件、管理账户凭证以及本地邮件处理。

## 目录结构

```
Email/
├── data/
│   ├── oauth/        # 存储转换后的 JSON 格式账户凭证文件
│   └── temp/         # 临时文件存储目录
├── src/
│   ├── api/
│   │   └── cloud_email_api.py  # 与云邮件 API (oauth.882263.xyz) 交互的模块
│   ├── utils/
│   │   └── convert_txt_to_json.py # 将 email_user.txt 转换为 JSON 的脚本
│   ├── email_service.py   # Email 服务主程序，负责处理邮件任务
│   ├── oauth2_imap_demo.py   # (可能) OAuth/IMAP 演示或测试脚本
│   ├── process_email.py      # (可能) 包含邮件处理逻辑的脚本
│   └── __init__.py
├── email_user.txt      # 包含原始账户凭证的文本文件
└── README.md           # 本文档
```

## 数据文件

*   `email_user.txt`:
    *   用途: 提供原始的电子邮件账户凭证。
    *   格式: 每行一个账户，格式为 `email@example.com----password----client_id----refresh_token`。
*   `data/oauth/*.json`:
    *   来源: 由 `src/utils/convert_txt_to_json.py` 脚本生成或通过UI界面导入。
    *   命名方式: 使用邮箱地址作为文件名（例如：`example_at_gmail.com.json`），特殊字符如`@`会被替换为`_at_`。
    *   内容: 每个 JSON 文件代表一个账户，包含 `email`, `password`, `client_id`, `refresh_token` 键值对。
    *   示例 (`example_at_gmail.com.json`):
        ```json
        {
          "email": "example@gmail.com",
          "password": "password123",
          "client_id": "clientid_abc",
          "refresh_token": "refreshtoken_xyz"
        }
        ```

## 核心脚本说明

*   **`src/utils/convert_txt_to_json.py`**:
    *   **作用**: 读取 `email_user.txt` 文件，将每行账户信息解析并保存为独立的 JSON 文件到 `src/Email/data/oauth/` 目录。
    *   **更新**: 现在使用邮箱地址作为文件名，并会跳过已存在的邮箱账号，避免重复导入。
    *   **运行**:
        ```powershell
        # 确保当前目录在 E:\projects\kling-rpa-agent\src\Email\src\utils
        cd E:\projects\kling-rpa-agent\src\Email\src\utils
        # 使用你的 Python 解释器运行脚本
        & "D:\Comfyui_mi2\Comfyui_mi\python_embeded\python.exe" convert_txt_to_json.py
        ```
    *   **注意**: 脚本会根据 `__file__` 自动计算项目根目录，确保输入和输出路径正确。

*   **`src/api/cloud_email_api.py`**:
    *   **作用**: 提供函数与外部云邮件 API (`oauth.882263.xyz`) 进行交互。
    *   **主要函数**:
        *   `get_latest_email(refresh_token, client_id, email, mailbox="INBOX", timeout=30)`: 获取指定邮箱的最新邮件。
        *   `get_all_emails(refresh_token, client_id, email, mailbox="INBOX", timeout=60)`: 获取指定邮箱的所有邮件。
        *   `clear_mailbox(refresh_token, client_id, email, mailbox="INBOX", timeout=60)`: 清空指定邮箱。
    *   **使用**: 通常需要先从 `data/oauth/` 目录下的 JSON 文件中读取账户的 `refresh_token` 和 `client_id`，然后调用相应函数。
        ```python
        import json
        from src.api.cloud_email_api import get_latest_email

        # 假设读取 example_at_gmail.com.json
        account_file = 'E:/projects/kling-rpa-agent/src/Email/data/oauth/example_at_gmail.com.json'
        with open(account_file, 'r') as f:
            account_data = json.load(f)

        latest_email = get_latest_email(
            refresh_token=account_data['refresh_token'],
            client_id=account_data['client_id'],
            email=account_data['email']
        )

        if latest_email:
            print("获取到最新邮件:", latest_email)
        else:
            print("未能获取最新邮件或邮箱为空。")
        ```

*   **`src/email_service.py`**:
    *   **作用**: Email服务主程序，负责加载配置、处理邮件任务、管理工作线程，**并提供 HTTP API 用于获取验证码**。
    *   **功能**:
        *   自动加载 `data/oauth/` 目录下的所有JSON账号文件
        *   根据配置的并发数创建工作线程处理邮件任务
        *   提供任务队列管理和错误处理
    *   **配置**: 通过主程序传递的配置文件设置并发数等参数

## UI界面功能

Email模块提供了图形用户界面，可以通过主程序的Email设置页面进行操作：

*   **批量导入**:
    *   支持通过文本框粘贴多个账号信息
    *   支持通过文件选择器导入.txt文件
    *   自动将账号信息转换为JSON文件，并使用邮箱地址作为文件名
    *   自动跳过已存在的邮箱账号，避免重复导入

*   **清空当前账号**:
    *   一键清空所有已导入的邮箱账号
    *   操作前会显示确认对话框，防止误操作
    *   操作后会显示清空的账号数量

*   **并发设置**:
    *   可以设置Email服务的并发任务数
    *   设置保存后会自动应用到Email服务

## 基本工作流程

### 通过UI界面操作（推荐）

1.  **打开Email设置**: 在主程序中点击"Email设置"按钮。
2.  **导入账号**: 
    *   方式一：在"粘贴账号列表"文本框中粘贴账号信息，然后点击"批量导入"。
    *   方式二：点击"选择账号文件"，选择包含账号信息的.txt文件，然后点击"批量导入"。
3.  **设置并发数**: 在"并发任务数"输入框中设置需要的并发数，然后点击"保存设置"。
4.  **启动服务**: 返回主界面，点击Email插件的"启动"按钮。
5.  **清空账号**: 如需清空所有账号，在Email设置页面点击"清空当前账号"按钮。

### 通过脚本操作（高级用户）

1.  **准备凭证**: 在 `email_user.txt` 文件中按指定格式添加账户信息。
2.  **转换凭证**: 运行 `src/utils/convert_txt_to_json.py` 脚本，将文本凭证转换为 JSON 文件存入 `data/oauth/`。
3.  **使用 API**: 在其他脚本中，导入 `src/api/cloud_email_api.py`，读取 `data/oauth/` 中的 JSON 文件获取凭证，然后调用 API 函数执行邮件操作。

## HTTP API (新功能)

`email_service.py` 在运行时会启动一个内置的 HTTP 服务器（默认监听 `http://127.0.0.1:5001`），提供以下 API 端点：

### 获取验证码

*   **端点**: `POST /get-verification-code`
*   **描述**: 获取指定邮箱收到的最新邮件中的 6 位数字验证码。
*   **请求 Body (JSON)**:
    ```json
    {
        "email": "user@example.com"
    }
    ```
*   **响应 (JSON)**:
    *   **成功 (200)**:
        ```json
        {
            "verification_code": "123456"
        }
        ```
    *   **邮箱未找到或无凭证 (404)**:
        ```json
        {
            "error": "Email account 'user@example.com' not found or missing credentials."
        }
        ```
    *   **未找到邮件或无法解析验证码 (404)**:
        ```json
        {
            "error": "Email account not found or no recent verification email."
        }
        // 或
        {
            "error": "Could not parse verification code from the latest email."
        }
        ```
    *   **请求格式错误 (400)**:
        ```json
        {
            "error": "Missing 'email' in request body"
        }
        ```
    *   **内部服务器错误 (500)**:
        ```json
        {
            "error": "Internal server error processing request."
        }
        ```
    *   **Email API 模块不可用 (503)**:
        ```json
        {
            "error": "Email API module not available."
        }
        ```

**使用示例 (Python requests)**:

```python
import requests
import json

api_url = "http://127.0.0.1:5001/get-verification-code"
email_to_check = "your_target_email@example.com"

try:
    response = requests.post(api_url, json={"email": email_to_check}, timeout=60) # 设置超时
    response.raise_for_status() # 如果状态码不是 2xx，则抛出异常

    result = response.json()
    if 'verification_code' in result:
        print(f"成功获取验证码: {result['verification_code']}")
    elif 'error' in result:
        print(f"获取验证码失败: {result['error']}")
    else:
        print(f"收到未知响应: {result}")

except requests.exceptions.RequestException as e:
    print(f"请求 API 出错: {e}")
except json.JSONDecodeError:
    print(f"无法解析 API 响应: {response.text}")

```

## 环境配置

Email模块现在支持基于环境变量和配置文件的分层配置结构：

### 配置文件

* **`.env`**: 包含环境变量的主配置文件（不提交到版本控制）
* **`.env.example`**: 环境变量模板，提供所有必要配置项的示例
* **`src/config/dev.json`**: 开发环境特定配置
* **`src/config/test.json`**: 测试环境特定配置
* **`src/config/prod.json`**: 生产环境特定配置

### 环境变量

主要环境变量包括：

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| API_BASE_URL | 外部云API的基础URL | https://oauth.882263.xyz |
| API_HOST | API服务主机 | localhost |
| API_PORT | API服务端口 | 5001 |
| API_DEBUG | 是否启用调试模式 | false |
| LEASE_DURATION_SECONDS | 邮箱租约持续时间（秒） | 600 |
| CLEANUP_INTERVAL_SECONDS | 清理间隔时间（秒） | 3600 |
| ENVIRONMENT | 当前环境（dev/test/prod） | dev |

### 配置优先级

配置加载优先级（从高到低）：
1. 环境特定配置文件（如`dev.json`）
2. `.env`文件中的环境变量
3. 代码中定义的默认值

### 使用方法

1. 复制`.env.example`为`.env`并根据需要修改
2. 根据环境选择适当的配置文件：`dev.json`、`test.json`或`prod.json`
3. 在`.env`中设置`ENVIRONMENT=dev|test|prod`来选择正确的环境配置
