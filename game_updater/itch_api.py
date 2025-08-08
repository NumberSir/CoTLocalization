import requests
from . import config

AUTH_HEADER = {
    "Authorization": config.API_KEY
}

def get_latest_upload_info(game_id, password=None):
    """
    获取最新的上传信息，包括upload_id和版本号。
    对于EA版，版本号从build的user_version字段获取。
    对于稳定版，从独立的API获取。
    """
    print("  - 正在请求上传列表...")
    
    url = config.UPLOADS_URL_TEMPLATE.format(game_id=game_id)
    params = {}
    if password:
        params['password'] = password

    try:
        response = requests.get(url, headers=AUTH_HEADER, params=params)
        response.raise_for_status()
        data = response.json()

        if "uploads" not in data or len(data["uploads"]) == 0:
            print("  - 错误: 未找到任何上传记录。")
            return None, None

        # 根据用户之前的修改，我们使用第二个上传记录 (index 1)
        latest_upload = data["uploads"][1]
        upload_id = latest_upload.get("id")
        
        if not upload_id:
            print("  - 错误: 上传记录中缺少 'id'。")
            return None, None
            
        print(f"  - 成功获取 Upload ID: {upload_id}")

        # --- 获取版本号 ---
        version = None
        if game_id == config.EARLY_ACCESS_GAME_ID:
            # EA版: 从build信息中获取版本号
            if "build" in latest_upload and latest_upload["build"].get("user_version"):
                version = latest_upload["build"]["user_version"]
                print(f"  - 成功从Build信息中获取EA版本号: {version}")
            else:
                print("  - 错误: EA版上传记录中未找到 'build.user_version'。")
        else:
            # 稳定版: 调用旧的API获取版本号
            print("  - 正在为稳定版获取最新版本号...")
            version_url = config.LATEST_VERSION_URL_TEMPLATE.format(
                game_id=config.STABLE_GAME_ID, 
                channel_name=config.STABLE_CHANNEL_NAME
            )
            version_response = requests.get(version_url)
            version_response.raise_for_status()
            version_data = version_response.json()
            if "latest" in version_data:
                version = version_data["latest"].lstrip('v')
                print(f"  - 成功获取稳定版版本号: {version}")
            else:
                print("  - 错误: 稳定版版本API未返回'latest'键。")

        return upload_id, version

    except requests.exceptions.RequestException as e:
        print(f"  - 错误: API请求失败: {e}")
        if e.response:
            print(f"  - 响应内容: {e.response.text}")
        return None, None