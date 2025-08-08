import subprocess
import sys
from . import itch_api, file_handler, browser_automation, config

def run_post_export_tasks(version):
    """执行导出后的所有任务"""
    print("\n--- 步骤 4: 执行导出后任务 ---")
    
    if not file_handler.unzip_story_export(version):
        print("流程终止：解压 'story_export.zip' 失败。")
        return

    last_fetch_dir = file_handler.sync_fetch_dirs()
    if not last_fetch_dir:
        print("流程终止：同步 'fetch' 目录失败。")
        return

    print("  - 正在运行 versionUpdate.py 脚本...")
    try:
        args = [sys.executable, config.VERSION_UPDATE_SCRIPT_PATH, last_fetch_dir, version]
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        print("  - versionUpdate.py 输出:")
        print(result.stdout)
        if result.stderr:
            print("  - versionUpdate.py 错误输出:")
            print(result.stderr)
        print("  - versionUpdate.py 脚本成功执行。")
    except FileNotFoundError:
        print(f"  - 错误: 未找到脚本 {config.VERSION_UPDATE_SCRIPT_PATH}")
    except subprocess.CalledProcessError as e:
        print(f"  - 错误: versionUpdate.py 执行失败，返回码 {e.returncode}")
        print(f"  - 输出: \n{e.stdout}")
        print(f"  - 错误: \n{e.stderr}")


def run_update_and_export(game_id, password=None):
    """
    执行完整的游戏更新和故事导出流程。
    :param game_id: 要更新的游戏的ID。
    :param password: (可选) EA版所需的密码。
    """
    mode = "抢先体验版" if password else "稳定版"
    print(f"开始为 {mode} 执行游戏更新和导出流程...")

    # 步骤 1: 从itch.io获取信息
    print("\n--- 步骤 1: 获取API信息 ---")
    upload_id, version = itch_api.get_latest_upload_info(game_id, password)
    if not upload_id or not version:
        print("流程终止：未能获取上传信息或版本号。")
        return

    # 步骤 2: 下载和处理文件
    print("\n--- 步骤 2: 处理游戏文件 ---")
    if not file_handler.download_and_unzip(upload_id, password):
        print("流程终止：下载或解压失败。")
        file_handler.cleanup_temp_files()
        return
    
    new_html_path = file_handler.find_and_move_html(version)
    if not new_html_path:
        print("流程终止：未能找到并移动HTML文件。")
        file_handler.cleanup_temp_files()
        return

    # 步骤 3: 浏览器自动化
    print("\n--- 步骤 3: 执行浏览器自动化 ---")
    if browser_automation.export_story_from_html(new_html_path):
        run_post_export_tasks(version)

    # 步骤 5: 清理
    print("\n--- 步骤 5: 清理临时文件 ---")
    file_handler.cleanup_temp_files()

    print("\n所有操作已完成！")