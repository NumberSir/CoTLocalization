import requests
import zipfile
import os
import shutil
from . import config

def download_and_unzip(upload_id, password=None):
    """使用upload_id下载并解压文件，可选择提供密码"""
    download_url = config.DOWNLOAD_URL_TEMPLATE.format(id=upload_id)
    print(f"  - 正在从 {download_url} 下载文件...")
    
    # 确保临时目录存在
    os.makedirs(config.TEMP_DIR, exist_ok=True)

    try:
        # 下载文件
        auth_header = {"Authorization": config.API_KEY,"password":password}
        with requests.get(download_url+("" if not password else "?password="+password), headers=auth_header, stream=True) as r:
            r.raise_for_status()
            with open(config.TEMP_ZIP_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"  - 文件已成功下载到 {config.TEMP_ZIP_PATH}")

        # 解压文件
        if os.path.exists(config.TEMP_EXTRACT_DIR):
            shutil.rmtree(config.TEMP_EXTRACT_DIR)
        os.makedirs(config.TEMP_EXTRACT_DIR)
        
        print(f"  - 正在解压到 {config.TEMP_EXTRACT_DIR}...")
        with zipfile.ZipFile(config.TEMP_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(config.TEMP_EXTRACT_DIR)
        print("  - 解压完成。")
        return True
    except Exception as e:
        print(f"  - 错误: 下载或解压过程中发生错误: {e}")
        return False

def find_and_move_html(version):
    """查找HTML文件，重命名并移动，然后返回新路径"""
    print("  - 正在查找、重命名并移动HTML文件...")
    for root, dirs, files in os.walk(config.TEMP_EXTRACT_DIR):
        for file in files:
            if file.endswith(".html"):
                original_html_path = os.path.join(root, file)
                new_filename = f"{file.replace('.html', '')}{version}.html"
                destination_path = os.path.join(config.DESTINATION_DIR, new_filename)
                
                print(f"  - 找到HTML文件: {original_html_path}")
                print(f"  - 新文件名: {new_filename}")
                
                os.makedirs(config.DESTINATION_DIR, exist_ok=True)
                shutil.move(original_html_path, destination_path)
                print(f"  - 文件已成功移动到: {destination_path}")
                return destination_path
    print("  - 错误: 在解压的文件夹中未找到HTML文件。")
    return None

def cleanup_temp_files():
    """清理临时文件和文件夹"""
    print("  - 清理临时文件...")
    if os.path.exists(config.TEMP_DIR):
        shutil.rmtree(config.TEMP_DIR)
        print(f"  - 已删除临时目录: {config.TEMP_DIR}")
    
    # 清理下载的zip文件
    if os.path.exists(config.FINAL_EXPORT_ZIP_PATH):
        os.remove(config.FINAL_EXPORT_ZIP_PATH)
        print(f"  - 已删除导出的zip文件: {config.FINAL_EXPORT_ZIP_PATH}")
    print("  - 清理完成。")

def unzip_story_export(version):
    """解压 story_export.zip 到 source/version 目录"""
    target_dir = os.path.join(config.SOURCE_DIR, version)
    print(f"  - 正在解压 '{config.FINAL_EXPORT_ZIP_NAME}' 到 '{target_dir}'...")
    
    if not os.path.exists(config.FINAL_EXPORT_ZIP_PATH):
        print(f"  - 错误: 未找到 '{config.FINAL_EXPORT_ZIP_NAME}'。")
        return False
        
    try:
        with zipfile.ZipFile(config.FINAL_EXPORT_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        print("  - 解压完成。")
        return True
    except Exception as e:
        print(f"  - 错误: 解压失败: {e}")
        return False

def sync_fetch_dirs():
    """同步fetch目录，并返回最后一个目录名"""
    print("  - 正在同步 'fetch' 目录...")
    try:
        # 获取所有子目录并排序
        dirs = sorted([d for d in os.listdir(config.FETCH_DIR) if os.path.isdir(os.path.join(config.FETCH_DIR, d))])
        if len(dirs) < 2:
            print("  - 错误: 'fetch' 目录中没有足够的子目录进行同步。")
            return None

        last_dir_name = dirs[-1]
        second_last_dir_name = dirs[-2]
        
        source_path = os.path.join(config.FETCH_DIR, second_last_dir_name)
        dest_path = os.path.join(config.FETCH_DIR, last_dir_name)
        
        print(f"  - 源目录: {source_path}")
        print(f"  - 目标目录: {dest_path}")

        # 复制文件，跳过已存在的
        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        print("  - 同步完成。")
        return last_dir_name
        
    except Exception as e:
        print(f"  - 错误: 同步 'fetch' 目录失败: {e}")
        return None