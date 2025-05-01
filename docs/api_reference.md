# Email Service API 参考

本文档描述了 Email 服务提供的一次性邮箱分配和邮件获取 API。
该 API 设计用于需要临时邮箱进行注册验证的场景，并确保邮箱地址的安全使用。

## 核心机制与状态

1.  **邮箱账号来源**: 服务管理位于 `src/Email/data/oauth/` 目录下的 `.json` 文件，每个文件代表一个邮箱账号及其凭证。
2.  **状态流转**:
    *   **Available (可用)**: 对应的 `.json` 文件存在且**没有** `.used` 后缀，并且该邮箱当前未在内存中被租用。
    *   **Leased (已租用)**: 邮箱被 `/request-email` 成功分配，并在内存中记录了租约状态和时间戳。租约时长为 10 分钟，超时后自动释放（从内存租约中移除）。
    *   **Used/Deleted (已使用/已删除)**: 当 `/mark-email-used` 被调用处理一个租用的邮箱时，对应的 `.json` 文件会被重命名为 `.json.used`。这标志着该邮箱永久作废，无法再被分配。
3.  **租约清理**: 在每次 `/request-email` 请求时，系统会自动清理过期的租约（超过 10 分钟未使用的租约）。
4.  **安全性**: 凭证保留在服务器端，不暴露给客户端。客户端通过租约机制获取邮箱地址，然后使用该地址请求邮件内容。

## API 端点

### 1. 请求分配邮箱

*   **方法**: `GET`
*   **路径**: `/request-email`
*   **功能**: 从当前可用的邮箱池中选择一个邮箱，将其租用 10 分钟，并返回该邮箱地址。
*   **请求**: 无需参数或 Body。
*   **成功响应 (200 OK)**:
    ```json
    {
      "email": "example_user@outlook.com",
      "lease_duration_seconds": 600
    }
    ```
*   **错误响应 (409 Conflict)**:
    ```json
    {
      "error": "No available email accounts at the moment."
    }
    ```
*   **行为**:
    *   清理过期的租约（超过 10 分钟未使用的租约）。
    *   查找可用的（`.json` 存在且未被租用）邮箱。
    *   在内存中添加租约记录（邮箱地址 + 时间戳）。
    *   10 分钟后若未被标记使用或释放，租约会自动从内存中移除。

### 2. 获取最新邮件

*   **方法**: `POST`
*   **路径**: `/get-latest-email`
*   **功能**: 获取指定邮箱地址（当前已租用）的最新邮件内容（原始数据）。服务内部处理凭证管理。
*   **请求 Body (JSON)**:
    ```json
    {
      "email": "example_user@outlook.com"
    }
    ```
*   **成功响应 (200 OK)**:
    ```json
    {
      "success": true,
      "data": { 
        "id": "AAMk...", 
        "subject": "Your Verification Code", 
        "bodyPreview": "Your code is 123456...",
        "body": { 
          "contentType": "html/text", 
          "content": "<html>...Your code is <b>123456</b>...</html>"
        },
        "from": { "emailAddress": { "address": "sender@domain.com" } },
        "receivedDateTime": "2023-10-27T10:30:00Z"
        // ... other fields from the cloud email API
      }
    }
    ```
    *或者如果没有找到新邮件:* 
    ```json
    {
      "success": true,
      "data": null 
    }
    ```
*   **错误响应 (400 Bad Request)**:
    ```json
    {
      "error": "Missing 'email' in request body."
    }
    ```
*   **错误响应 (404 Not Found)**:
    ```json
    {
      "error": "Email not found or lease expired."
    }
    ```
*   **错误响应 (500 Internal Server Error)**:
    ```json
    {
      "error": "Failed to retrieve email from cloud API."
      // or other specific internal errors
    }
    ```
*   **行为**:
    *   检查邮箱是否在内存租约中且未过期。
    *   从文件中读取凭证。
    *   调用外部云 API 获取邮件。
    *   返回原始邮件数据。内存租约仍然存在，直到超时、被标记为已使用或被释放。

### 3. 标记邮箱为已使用

*   **方法**: `POST`
*   **路径**: `/mark-email-used`
*   **功能**: 永久标记一个已租用的邮箱为已使用，将其从可用池中移除。这应该在成功完成所需操作（如注册）后调用。
*   **请求 Body (JSON)**:
    ```json
    {
      "email": "example_user@outlook.com"
    }
    ```
*   **成功响应 (200 OK)**:
    ```json
    {
      "message": "Email marked as used."
    }
    ```
*   **错误响应 (400 Bad Request)**:
    ```json
    {
      "error": "Missing 'email' in request body."
    }
    ```
*   **错误响应 (404 Not Found)**:
    ```json
    {
      "error": "Email not found or lease expired."
    }
    ```
*   **错误响应 (500 Internal Server Error)**:
    ```json
    {
      "error": "Failed to mark email as used."
    }
    ```
*   **行为**:
    *   检查邮箱是否在内存租约中且未过期。
    *   将对应的 `.json` 文件重命名为 `.json.used`。
    *   从内存 `email_leases` 字典中移除该邮箱条目。

### 4. 释放邮箱租约

*   **方法**: `POST`
*   **路径**: `/release-email`
*   **功能**: 在租约期限到期前释放邮箱地址的租约。这使得邮箱可以更快地被其他请求使用。
*   **请求 Body (JSON)**:
    ```json
    {
      "email": "example_user@outlook.com"
    }
    ```
*   **成功响应 (200 OK)**:
    ```json
    {
      "message": "Email lease released."
    }
    ```
*   **错误响应 (400 Bad Request)**:
    ```json
    {
      "error": "Missing 'email' in request body."
    }
    ```
*   **行为**:
    *   从内存 `email_leases` 字典中移除该邮箱条目。

## 注意事项

*   **线程安全**: 服务内部确保对内存租约字典 `email_leases` 的并发访问是线程安全的（使用 `threading.Lock`）。
*   **文件系统权限**: 服务需要有对 `src/Email/data/oauth/` 目录的读、写、重命名和删除权限。
*   **外部依赖**: 邮件获取功能依赖于一个外部云邮件 API。
*   **客户端职责**: 客户端负责从原始邮件数据中提取验证码或其他所需信息。
*   **租约管理**: 客户端应当在完成操作后调用 `/mark-email-used` 或 `/release-email` 以适当管理租约。
