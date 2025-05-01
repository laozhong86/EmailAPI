import os
import sys
import time
import pathlib
import logging
import msvcrt  # 用于Windows下的按键检测

# 导入版本信息
try:
    from __version__ import __version__
    logging.info(f"当前版本: {__version__}")
except ImportError:
    __version__ = "0.0.0"
    logging.warning("无法导入版本信息，使用默认版本: 0.0.0")

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加项目根目录到sys.path
script_path = pathlib.Path(__file__).resolve()
project_root = script_path.parent  # 当前目录就是Email目录
sys.path.insert(0, str(project_root))

# 导入本地模块
try:
    from src.utils.convert_txt_to_json import convert_txt_to_json
    from src.email_service import start_service
    from src.utils.self_update import check_for_update
    modules_available = True
    logging.info("成功导入所需模块")
except ImportError as e:
    logging.error(f"导入模块失败: {e}")
    modules_available = False


def clear_screen():
    """清除控制台屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')


def display_menu(countdown=3):
    """
    显示主菜单并处理用户选择
    
    Args:
        countdown: 默认倒计时秒数，超时后自动启动API服务
    """
    clear_screen()
    print("=" * 50)
    print("Email 管理系统".center(46))
    print("=" * 50)
    print("\n请选择操作:")
    print("1. 导入邮箱账号")
    print("2. 启动API服务")
    print("\n默认将在 {} 秒后自动启动API服务...".format(countdown))
    print("=" * 50)
    
    # 倒计时处理
    start_time = time.time()
    choice = None
    
    while time.time() - start_time < countdown:
        remaining = countdown - int(time.time() - start_time)
        sys.stdout.write(f"\r等待选择 ({remaining} 秒)... ")
        sys.stdout.flush()
        
        # 检查是否有按键输入
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8')
            if key in ['1', '2']:
                choice = key
                break
    
    print("\n")
    
    # 处理选择结果
    if choice == '1':
        import_email_accounts()
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
        input("\n按回车键返回主菜单...")
        display_menu()
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


def main():
    """主函数"""
    try:
        # 检查更新
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe，检查更新
            logging.info("正在检查更新...")
            try:
                # 检查更新但不阻塞主程序
                import threading
                update_thread = threading.Thread(
                    target=check_for_update,
                    args=("laozhong86", "EmailAPI", "emailAPI.exe"),
                    daemon=True
                )
                update_thread.start()
            except Exception as e:
                logging.error(f"检查更新失败: {e}")
        
        # 显示菜单，设置3秒倒计时
        display_menu(countdown=3)
    except KeyboardInterrupt:
        clear_screen()
        print("\nEmail管理系统已退出")
    except Exception as e:
        logging.error(f"程序运行出错: {e}")
        print(f"\n程序运行出错: {e}")
        input("\n按回车键退出...")


if __name__ == "__main__":
    main()
