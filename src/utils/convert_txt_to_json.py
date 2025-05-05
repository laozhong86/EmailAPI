import os
import json
import pathlib
import logging
import argparse
import sys

# 配置日志记录 - Log to stderr for easier capture by Node.js
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)

# 获取数据目录路径的辅助函数
def get_data_dir(subdir=None):
    """
    获取数据目录路径，根据运行环境自动选择正确的路径
    
    Args:
        subdir: 可选的子目录名称
        
    Returns:
        pathlib.Path: 数据目录的路径
    """
    # 检查是否在 exe 模式下运行
    if getattr(sys, 'frozen', False):
        # 如果是 exe 模式，使用 exe 所在目录
        base_dir = pathlib.Path(sys.executable).parent / 'data'
    else:
        # 如果是开发模式，使用相对路径
        script_path = pathlib.Path(__file__).resolve()
        base_dir = script_path.parent.parent.parent / 'data'
    
    # 确保目录存在
    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"已创建数据目录: {base_dir}")
    
    # 如果指定了子目录，则返回子目录路径
    if subdir:
        subdir_path = base_dir / subdir
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"已创建子目录: {subdir_path}")
        return subdir_path
    
    return base_dir

# 定义路径 (使用新的辅助函数)
OUTPUT_DIR = get_data_dir('oauth')

def convert_txt_to_json(input_file_path_str):
    """
    读取指定的文本文件，将每一行账户信息解析并保存为单独的 JSON 文件。
    返回一个包含处理结果的字典。
    """
    input_file_path = pathlib.Path(input_file_path_str).resolve()
    logging.info(f"开始处理输入文件: {input_file_path}")
    logging.info(f"JSON 文件将输出到目录: {OUTPUT_DIR}")

    # 确保输出目录存在
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        logging.info(f"输出目录已确认/创建: {OUTPUT_DIR}")
    except OSError as e:
        logging.error(f"无法创建输出目录 {OUTPUT_DIR}: {e}")
        # Return error status
        return {"success": False, "error": f"Cannot create output directory: {e}", "total": 0, "successCount": 0, "failedCount": 0, "skippedCount": 0}

    total_lines = 0
    successful_conversions = 0
    failed_conversions = 0
    skipped_conversions = 0  # 新增：跳过的转换计数
    errors = [] # Collect specific line errors

    try:
        # Use the passed input_file_path
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            for i, line in enumerate(infile):
                total_lines += 1
                line_number = i + 1
                line = line.strip()

                if not line:
                    logging.warning(f"第 {line_number} 行是空行，已跳过。")
                    continue

                parts = line.split('----')

                if len(parts) >= 4:
                    email = parts[0]
                    password = parts[1] # 注意：仍然包含密码，按计划执行
                    client_id = parts[2]
                    refresh_token = parts[3]

                    account_data = {
                        "email": email,
                        "password": password,
                        "client_id": client_id,
                        "refresh_token": refresh_token
                    }

                    # 使用邮箱作为文件名，替换特殊字符
                    # 将 @ 替换为 _at_，保留 .
                    safe_email = email.replace('@', '_at_')
                    filename = f"{safe_email}.json"
                    output_path = OUTPUT_DIR / filename

                    # 检查是否已存在相同邮箱的文件
                    if output_path.exists():
                        logging.info(f"邮箱 {email} 已存在，跳过导入。")
                        skipped_conversions += 1
                        continue

                    try:
                        with open(output_path, 'w', encoding='utf-8') as outfile:
                            json.dump(account_data, outfile, ensure_ascii=False, indent=4)
                        successful_conversions += 1
                        # logging.debug(f"成功将第 {line_number} 行转换为 {filename}")
                    except IOError as e:
                        error_msg = f"无法写入文件 {output_path} (来自第 {line_number} 行): {e}"
                        logging.error(error_msg)
                        errors.append(error_msg)
                        failed_conversions += 1
                    except Exception as e:
                        error_msg = f"写入 JSON 文件 {output_path} 时发生意外错误 (来自第 {line_number} 行): {e}"
                        logging.error(error_msg)
                        errors.append(error_msg)
                        failed_conversions += 1
                else:
                    error_msg = f"第 {line_number} 行格式错误 (预期至少 4 部分，实际 {len(parts)} 部分)"
                    logging.error(error_msg + f": {line}")
                    errors.append(error_msg)
                    failed_conversions += 1

    except FileNotFoundError:
        error_msg = f"输入文件未找到: {input_file_path}"
        logging.error(error_msg)
        # Return error status
        return {"success": False, "error": error_msg, "total": 0, "successCount": 0, "failedCount": 0, "skippedCount": 0}
    except Exception as e:
        error_msg = f"读取输入文件 {input_file_path} 时发生错误: {e}"
        logging.error(error_msg)
        # Return error status
        return {"success": False, "error": error_msg, "total": total_lines, "successCount": successful_conversions, "failedCount": failed_conversions, "skippedCount": skipped_conversions}

    # 打印总结报告到 stderr
    logging.info("="*30 + " 处理完成 " + "="*30)
    logging.info(f"总共处理行数: {total_lines}")
    logging.info(f"成功转换文件数: {successful_conversions}")
    logging.info(f"跳过重复邮箱数: {skipped_conversions}")
    logging.info(f"失败行数/转换数: {failed_conversions}")
    logging.info("="*60)

    # Return results dictionary
    return {
        "success": failed_conversions == 0, # Overall success if no failures
        "error": "; ".join(errors) if errors else None,
        "total": total_lines,
        "successCount": successful_conversions,
        "failedCount": failed_conversions,
        "skippedCount": skipped_conversions
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert email account text file to JSON files.')
    parser.add_argument('--input-file', type=str, required=True,
                        help='Path to the input text file (format: email----password----client_id----refresh_token per line).')
    args = parser.parse_args()

    result = convert_txt_to_json(args.input_file)

    # Print JSON result to stdout for Node.js
    print(json.dumps(result))

    # Set exit code based on success
    if result["success"]:
        sys.exit(0)
    else:
        # Optionally check for specific critical errors like file not found
        if "输入文件未找到" in (result.get("error") or "") or "无法创建输出目录" in (result.get("error") or ""):
             sys.exit(2) # Different code for critical setup errors
        else:
             sys.exit(1) # General failure (e.g., some lines failed)
