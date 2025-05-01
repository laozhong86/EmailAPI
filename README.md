# Email 模块使用指南

## 概述

Email 模块是一个用于处理电子邮件相关操作的工具，包括通过云端 API 获取邮件、管理账户凭证以及本地邮件处理。本文档提供了模块的使用方法和主要功能说明。

## 主要功能

1. **邮箱账号管理**：
   - 导入邮箱账号（从文本文件）
   - 管理邮箱账号凭证（存储为 JSON 格式）

2. **Email API 服务**：
   - 提供 HTTP API 用于获取验证码
   - 管理邮箱租约
   - 清理过期邮箱

## 使用方法

### 启动主程序

在项目根目录下运行：

```bash
python main.py
```

启动后会显示主菜单，有以下选项：
- 1. 导入邮箱账号
- 2. 启动API服务

如果在 3 秒内没有选择，将自动启动 API 服务。

### 导入邮箱账号

1. 在主菜单中选择 "1"
2. 输入包含邮箱账号的文本文件路径
3. 文本文件格式要求：每行一个账户，格式为 `email@example.com----password----client_id----refresh_token`

导入后，账号信息将被转换为 JSON 格式并保存在 `data/oauth/` 目录下。

### 启动 API 服务

1. 在主菜单中选择 "2" 或等待自动选择
2. 服务将在配置的端口上启动（默认为 16881）
3. 使用 Ctrl+C 终止服务

## API 端点

### 获取验证码

- **端点**: `POST /get-verification-code`
- **描述**: 获取指定邮箱收到的最新邮件中的 6 位数字验证码
- **请求 Body (JSON)**:
  ```json
  {
      "email": "user@example.com"
  }
  ```
- **成功响应 (200)**:
  ```json
  {
      "verification_code": "123456"
  }
  ```

### 请求邮箱

- **端点**: `GET /request-email`
- **描述**: 分配一个可用的邮箱地址并创建租约
- **成功响应 (200)**:
  ```json
  {
      "email": "example@gmail.com",
      "lease_expires_in": 600
  }
  ```

### 获取最新邮件

- **端点**: `GET /get-latest-email`
- **描述**: 获取指定邮箱的最新邮件
- **参数**: `?email=user@example.com`
- **成功响应 (200)**:
  ```json
  {
      "subject": "邮件主题",
      "body": "邮件内容",
      "from": "sender@example.com",
      "date": "2025-05-01T12:00:00Z"
  }
  ```

## 配置

配置文件位于 `.env`，主要配置项包括：

```
# API配置
API_BASE_URL=https://oauth.882263.xyz
API_HOST=localhost
API_PORT=16881
API_DEBUG=true

# 邮箱管理配置
LEASE_DURATION_SECONDS=600
CLEANUP_INTERVAL_SECONDS=3600

# 环境设置
ENVIRONMENT=dev
```

可以根据需要修改这些配置项。

## 注意事项

1. 确保在导入邮箱账号前，文本文件格式正确
2. API 服务启动后，终止服务将直接退出程序
3. 邮箱租约有效期默认为 600 秒，过期后自动释放
4. 已使用的邮箱凭证文件会被定期清理

## 自动更新功能

本应用支持自动更新功能，每次启动时会自动检查GitHub上是否有新版本。如果发现新版本，将自动下载并替换当前版本。

### 自动更新流程

1. 应用启动时，会检查GitHub上的最新版本
2. 如果发现新版本，会自动下载到临时目录
3. 下载完成后，会校验SHA-256确保文件完整性
4. 然后将当前版本备份为`.old`文件，并用新版本替换
5. 最后自动启动新版本并退出当前程序

### 配置GitHub Token（私有仓库）

如果您使用的是私有仓库，需要配置GitHub Token才能访问发布信息：

1. 复制`config.ini.example`为`config.ini`
2. 在GitHub上创建一个具有只读权限的Personal Access Token
3. 将Token填入`config.ini`文件中

### 故障回滚

如果新版本无法正常工作，可以通过以下步骤回滚到旧版本：

1. 找到备份文件`emailAPI.exe.old`
2. 删除或重命名当前的`emailAPI.exe`
3. 将`emailAPI.exe.old`重命名为`emailAPI.exe`
4. 重新启动应用