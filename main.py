import os
import sys
import time
import pathlib
from pathlib import Path
import logging
import msvcrt  # 用于Windows下的按键检测

# 导入配置加载器
from src.config.config_manager import load_config

# 导入版本信息
try:
    from __version__ import __version__
    logging.info(f"当前版本: {__version__}")
except ImportError:
    __version__ = "0.0.0"
    logging.warning("无法导入版本信息，使用默认版本: 0.0.0")

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# <<< 新增：确定 .env 文件路径并加载配置 >>>
def get_env_path():
    """确定并返回有效的 .env 文件路径"""
    if getattr(sys, 'frozen', False):
        # 打包环境 (exe)
        exe_path = Path(sys.executable)
        env_path = exe_path.parent / '.env'
        logging.info(f"运行在打包环境，尝试加载 .env 文件于: {env_path}")
    else:
        # 源代码环境 (.py)
        script_path = Path(__file__).resolve()
        project_root = script_path.parent
        env_path = project_root / '.env'
        logging.info(f"运行在源代码环境，尝试加载 .env 文件于: {env_path}")

    if env_path.exists() and env_path.is_file():
        logging.info(f"找到有效的 .env 文件: {env_path}")
        return env_path
    else:
        logging.warning(f"未在预期位置找到 .env 文件: {env_path}")
        return None

effective_env_path = get_env_path()

# 提前加载配置
# 这将使用上面确定的路径来加载 .env
# 如果 effective_env_path 为 None, load_config 会使用其内部默认逻辑（这可能不是我们想要的）
# 或者我们可以在 load_config 中处理 None 的情况，或者在这里确保只有在找到文件时才调用
if effective_env_path:
    load_config(env_path=effective_env_path)
    logging.info(f"已使用 {effective_env_path} 加载配置")
else:
    logging.warning("未找到有效的 .env 文件，将使用默认配置或环境变量")
    # 可以选择在这里调用 load_config() 让其尝试默认行为，或依赖后续代码处理
    # load_config() # 如果需要 fallback 到 config_manager 的默认行为
# <<< 结束新增部分 >>>

# 添加项目根目录到sys.path
script_path = pathlib.Path(__file__).resolve()
project_root = script_path.parent  # 当前目录就是Email目录
sys.path.insert(0, str(project_root))

# 导入本地模块
initial_import_error = None # 新增变量来存储初始导入错误
try:
    from src.utils.convert_txt_to_json import convert_txt_to_json
    from src.email_service import start_service
    from src.utils.self_update import check_for_update, perform_update
    modules_available = True
    logging.info("成功导入所需模块")
except ImportError as e:
    logging.error(f"初始化导入模块失败: {e}")
    print(f"!!! 初始化导入错误: {e} !!!") # <-- 增加直接打印
    modules_available = False
    initial_import_error = e # <-- 存储错误信息

# 全局变量，用于存储更新信息
update_info = None


def clear_screen():
    """清除控制台屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')


def display_menu(countdown=3, update_info=None):
    """
    显示主菜单并处理用户选择
    
    Args:
        countdown: 默认倒计时秒数，超时后自动启动API服务
        update_info: 更新信息，如果有可用更新则不为None
    """
    clear_screen()
    print("=" * 50)
    print("Email 管理系统".center(46))
    print(f"当前版本: v{__version__}".center(46))
    print("=" * 50)
    print("\n请选择操作:")
    print("1. 导入邮箱账号")
    print("2. 启动API服务")
    
    # 如果有可用更新，显示更新选项
    if update_info:
        print(f"3. 立即更新到新版本 v{update_info['latest_version']}")
    
    print("\n默认将在 {} 秒后自动启动API服务...".format(countdown))
    print("=" * 50)
    
    # 倒计时处理
    start_time = time.time()
    choice = None
    
    # 设置有效按键列表
    valid_keys = ['1', '2']
    if update_info:
        valid_keys.append('3')
    
    while time.time() - start_time < countdown:
        remaining = countdown - int(time.time() - start_time)
        sys.stdout.write(f"\r等待选择 ({remaining} 秒)... ")
        sys.stdout.flush()
        
        # 检查是否有按键输入
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8')
            if key in valid_keys:
                choice = key
                break
    
    print("\n")
    
    # 处理选择结果
    if choice == '1':
        import_email_accounts()
    elif choice == '3' and update_info:
        update_app(update_info)
    else:
        # 默认选择或选择2
        start_api_service()


def import_email_accounts():
    """处理邮箱账号导入功能"""
    clear_screen()
    print("=" * 50)
    print("邮箱账号导入".center(46))
    print("=" * 50)
    
    if not modules_available:
        print("错误: 无法导入必要模块，请检查安装")
        input("\n按回车键返回主菜单...")
        display_menu()
        return
    
    print("\n请输入包含邮箱账号的文本文件路径:")
    input_file_path = input("> ").strip()
    
    if not input_file_path:
        print("错误: 未提供文件路径")
        input("\n按回车键返回主菜单...")
        display_menu()
        return
    
    try:
        # 调用导入函数
        result = convert_txt_to_json(input_file_path)
        
        # 显示处理结果
        print("\n处理结果:")
        print(f"总行数: {result.get('total', 0)}")
        print(f"成功导入: {result.get('successCount', 0)}")
        print(f"跳过重复: {result.get('skippedCount', 0)}")
        print(f"失败行数: {result.get('failedCount', 0)}")
        
        if not result.get('success', False):
            print(f"\n错误: {result.get('error', '未知错误')}")
        
    except Exception as e:
        print(f"处理文件时出错: {e}")
    
    # 询问是否继续
    print("\n操作完成。")
    choice = input("是否继续导入账号? (y/n, 默认n): ").strip().lower()
    
    if choice == 'y':
        import_email_accounts()
    else:
        # 返回主菜单
        display_menu()


def start_api_service():
    """启动Email API服务"""
    clear_screen()
    print("=" * 50)
    print("启动Email API服务".center(46))
    print("=" * 50)

    if not modules_available:
        print("错误: 无法导入必要模块，请检查安装")
        if initial_import_error: # <-- 检查是否有存储的初始错误
             print(f"详细错误: {initial_import_error}") # <-- 打印存储的错误
        input("\n按回车键返回主菜单...")
        display_menu(update_info=update_info)
        return

    print("\n正在启动Email API服务...")
    
    try:
        # 直接在主进程中启动服务，而不是使用子进程
        print("服务已启动，按Ctrl+C终止服务...")
        
        # 捕获Ctrl+C信号
        import signal
        
        # 定义信号处理函数
        def signal_handler(sig, frame):
            print("\nEmail服务已被用户中断")
            sys.exit(0)
        
        # 注册SIGINT信号处理器（Ctrl+C）
        signal.signal(signal.SIGINT, signal_handler)
        
        # 直接在主进程中启动Flask服务
        # 这将阻塞主进程，直到服务终止
        start_service(debug=False)
        
        # 如果服务正常结束，直接退出程序
        print("\nEmail服务已终止")
        sys.exit(0)
    except Exception as e:
        print(f"\n启动服务时出错: {e}")
        input("\n按回车键返回主菜单...")
        display_menu()


def update_app(update_info):
    """
    执行应用更新
    
    Args:
        update_info: 包含更新信息的字典
    """
    clear_screen()
    print("=" * 50)
    print("应用更新".center(46))
    print("=" * 50)
    
    print(f"\n当前版本: {update_info['current_version']}")
    print(f"最新版本: {update_info['latest_version']}")
    print("\n正在准备更新...")
    
    # 执行更新
    result = perform_update(
        download_url=update_info['download_url'],
        latest_version_str=update_info['latest_version'],
        exe_name="emailAPI.exe",
        sha256=update_info.get('sha256')
    )
    
    if not result:
        print("\n更新失败，请稍后再试")
        input("\n按回车键返回主菜单...")
        display_menu(update_info=update_info)


def main():
    """主函数"""
    global update_info
    try:
        # 检查更新
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe，检查更新
            logging.info("正在检查更新...")
            try:
                # 检查更新但不阻塞主程序
                import threading
                
                def check_update_thread():
                    global update_info
                    # 设置auto_update=False，仅检查不自动更新
                    result = check_for_update(
                        "laozhong86", "EmailAPI", "emailAPI.exe", auto_update=False
                    )
                    if isinstance(result, dict):
                        update_info = result
                
                update_thread = threading.Thread(
                    target=check_update_thread,
                    daemon=True
                )
                update_thread.start()
                # 等待更新检查完成，最多等待3秒
                update_thread.join(timeout=3)
            except Exception as e:
                logging.error(f"检查更新失败: {e}")
        
        # 显示菜单，设置3秒倒计时，传入更新信息
        display_menu(countdown=3, update_info=update_info)
    except KeyboardInterrupt:
        clear_screen()
        print("\nEmail管理系统已退出")
    except Exception as e:
        logging.error(f"程序运行出错: {e}")
        print(f"\n程序运行出错: {e}")
        input("\n按回车键退出...")


if __name__ == "__main__":
    main()
