import requests
import zipfile
import os
import shutil
import json

# --- 配置 ---
GAME_ID = "2151565"
API_KEY = "ZvGKukkx9B9oY6rsEuqeNvBzs6EXTXGm6Jaboc4X"
DESTINATION_DIR = r"D:\Game\CourseOfTemptation_desktop_v0.5.2d"
TEMP_ZIP_PATH = "temp_download.zip"
TEMP_EXTRACT_DIR = "temp_extract"

# --- API端点 ---
UPLOADS_URL = f"https://api.itch.io/games/{GAME_ID}/uploads"
DOWNLOAD_URL_TEMPLATE = "https://api.itch.io/uploads/{id}/download"
LATEST_VERSION_URL = f"https://itch.io/api/1/x/wharf/latest?game_id={GAME_ID}&channel_name=desktop"

# --- 请求头 ---
AUTH_HEADER = {
    "Authorization": API_KEY
}

def get_first_upload_id():
    """获取最新的上传ID"""
    print("步骤 1: 正在向itch.io API请求上传列表...")
    try:
        response = requests.get(UPLOADS_URL, headers=AUTH_HEADER)
        response.raise_for_status()  # 如果请求失败则抛出异常
        data = response.json()
        if "uploads" in data and len(data["uploads"]) > 0:
            upload_id = data["uploads"][1]["id"]
            print(f"  - 成功获取 Upload ID: {upload_id}")
            return upload_id
        else:
            print("  - 错误: 未找到任何上传记录。")
            return None
    except requests.exceptions.RequestException as e:
        print(f"  - 错误: 请求上传列表失败: {e}")
        return None

def get_latest_version():
    """获取最新的版本号字符串"""
    print("步骤 2: 正在获取最新版本号...")
    try:
        response = requests.get(LATEST_VERSION_URL)
        response.raise_for_status()
        data = response.json()
        if "latest" in data:
            version = data["latest"].lstrip('v') # 去掉开头的 'v'
            print(f"  - 成功获取版本号: {version}")
            return version
        else:
            print("  - 错误: 返回的JSON中没有找到'latest'键。")
            return None
    except requests.exceptions.RequestException as e:
        print(f"  - 错误: 请求最新版本号失败: {e}")
        return None

def download_and_unzip(upload_id):
    """直接使用upload_id下载并解压文件"""
    download_url = DOWNLOAD_URL_TEMPLATE.format(id=upload_id)
    print(f"步骤 3: 正在从 {download_url} 下载文件...")
    try:
        # 下载文件 (使用 GET 请求)
        with requests.get(download_url, headers=AUTH_HEADER, stream=True) as r:
            r.raise_for_status()
            with open(TEMP_ZIP_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"  - 文件已成功下载到 {TEMP_ZIP_PATH}")

        # 解压文件
        if os.path.exists(TEMP_EXTRACT_DIR):
            shutil.rmtree(TEMP_EXTRACT_DIR)
        os.makedirs(TEMP_EXTRACT_DIR)
        
        print(f"  - 正在解压到 {TEMP_EXTRACT_DIR}...")
        with zipfile.ZipFile(TEMP_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(TEMP_EXTRACT_DIR)
        print("  - 解压完成。")
        return True
    except Exception as e:
        print(f"  - 错误: 下载或解压过程中发生错误: {e}")
        return False

def find_and_move_html(version):
    """查找HTML文件，重命名并移动到目标文件夹"""
    print("步骤 4: 正在查找、重命名并移动HTML文件...")
    found_html = False
    for root, dirs, files in os.walk(TEMP_EXTRACT_DIR):
        for file in files:
            if file.endswith(".html"):
                original_html_path = os.path.join(root, file)
                new_filename = f"{file.replace('.html', '')}{version}.html"
                destination_path = os.path.join(DESTINATION_DIR, new_filename)
                
                print(f"  - 找到HTML文件: {original_html_path}")
                print(f"  - 新文件名: {new_filename}")
                
                # 确保目标目录存在
                os.makedirs(DESTINATION_DIR, exist_ok=True)
                
                # 移动并重命名文件
                shutil.move(original_html_path, destination_path)
                print(f"  - 文件已成功移动到: {destination_path}")
                found_html = True
                break # 假设只有一个HTML文件需要处理
        if found_html:
            break
    
    if not found_html:
        print("  - 错误: 在解压的文件夹中未找到HTML文件。")

def cleanup():
    """清理临时文件和文件夹"""
    print("步骤 5: 清理临时文件...")
    if os.path.exists(TEMP_ZIP_PATH):
        os.remove(TEMP_ZIP_PATH)
        print(f"  - 已删除临时文件: {TEMP_ZIP_PATH}")
    if os.path.exists(TEMP_EXTRACT_DIR):
        shutil.rmtree(TEMP_EXTRACT_DIR)
        print(f"  - 已删除临时目录: {TEMP_EXTRACT_DIR}")
    print("清理完成。")

def main():
    """主执行函数"""
    upload_id = get_first_upload_id()
    if not upload_id:
        return

    version = get_latest_version()
    if not version:
        return

    if download_and_unzip(upload_id):
        find_and_move_html(version)
    
    cleanup()
    print("\n所有操作已完成！")

if __name__ == "__main__":
    main()