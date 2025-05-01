# 你的角色
你是持续交付（CD）专家，精通 PyInstaller、GitHub Actions、SemVer、Windows 代码签名和自动更新机制。

# 项目背景
- 这是一个纯 **Python** CLI 项目，启动入口：  main.py
- 目标：把项目打包成 **单文件 exe**（无源码泄露），发送给客户（仅 Windows）。
- 客户双击 exe 运行时，应先自动检查 GitHub Releases 是否有新版本；如有则静默下载新版 exe、替换自身并重启。
- 发布触发方式：每次 `git tag vX.Y.Z` 推送到 GitHub。
- 单文件体积 ≤ 150 MB，不要求差分补丁。
- 仓库地址： [https://github.com/laozhong86/EmailAPI](https://github.com/laozhong86/EmailAPI)

# 交付目标
1. **本地打包脚本**  
   - 使用 **PyInstaller --onefile**（或你的最佳实践）生成 `emailAPI.exe`  
   - 支持将第三方依赖和资源打进 exe  
2. **GitHub Actions**  
   - 触发：`push --tags`  
   - 步骤：安装 Python 3.12 → 安装依赖 → 打包 exe → 创建/更新 Release，上传 exe Asset  
3. **自更新代码 self_update.py**  
   - 启动时读取 `__version__`（与 tag 同步）  
   - 请求 `https://api.github.com/repos/<owner>/<repo>/releases/latest`  
   - 比较版本；若新版则下载对应 exe 到 `%TEMP%`，校验 SHA-256，再覆盖当前文件  
   - 静默重启：`subprocess.Popen([new_exe_path]); sys.exit(0)`  
   - 若当前 exe 被占用，先保存为 `emailAPI_new.exe`，下次启动再替换  
4. **安全**  
   - 私有仓库场景：下载时使用只读 `GH_TOKEN`；此 Token 不能硬编码在源码里，可放到 exe 外侧的 `config.ini`  
5. **文档**  
   - *README.md*：客户第一次下载、运行方式，自动更新提示，故障回滚（保留 `_old.exe`）  
6. **输出清单**  
   - `pyproject.toml` / `requirements.txt` 最小示例  
   - `build_exe.ps1`（本地打包脚本，可被 Actions 复用）  
   - `.github/workflows/release.yml` 完整内容  
   - `self_update.py` 代码  
   - `main.py` 如何调用 `self_update.check_for_update()` 示例  
7. **编码约束**  
   - 必须兼容 Windows 10+（x64）  
   - 依赖尽量少；网络请求用 `requests`，版本比较用 `packaging.version`  
   - CI 运行器：`windows-latest`；Python 版本锁 `3.12.x`   
   - 脚本中所有路径、参数都写中文注释，便于后续维护  
8. **文档输出格式**  
   - 使用 **Markdown**，章标题依次为  
     - `# 总览`  
     - `# requirements.txt / pyproject.toml`  
     - `# 本地打包脚本 build_exe.ps1`  
     - `# GitHub Actions Workflow`  
     - `# self_update.py`  
     - `# main.py 调用示例`  
     - `# 客户端首次使用 & 回滚说明`  
     - `# 常见坑与解决方案`  

请一次性给出所有文件与说明，确保我复制进仓库后：  
```powershell
git tag -a v0.1.0 -m "first python release"
git push --tags
