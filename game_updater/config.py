import os

# --- API and Game Config ---
API_KEY = "ZvGKukkx9B9oY6rsEuqeNvBzs6EXTXGm6Jaboc4X"

STABLE_GAME_ID = "2151565"
EARLY_ACCESS_GAME_ID = "2499529"

# Channel name is only used for the stable version's latest check
STABLE_CHANNEL_NAME = "desktop"

# --- Paths and Directories ---
# 使用绝对路径以避免歧义
DESTINATION_DIR = r"D:\Game\CourseOfTemptation_desktop_v0.5.2d"
# 将临时文件放在项目结构中，便于管理
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMP_DIR = os.path.join(BASE_DIR, "temp_update_files")
TEMP_ZIP_PATH = os.path.join(TEMP_DIR, "temp_download.zip")
TEMP_EXTRACT_DIR = os.path.join(TEMP_DIR, "temp_extract")
SOURCE_DIR = os.path.join(BASE_DIR, "source")
FETCH_DIR = os.path.join(BASE_DIR, "fetch")

# --- File Names ---
VERSION_UPDATE_SCRIPT_PATH = os.path.join(BASE_DIR, "versionUpdate.py")
STORY_EXPORT_JS_PATH = os.path.join(DESTINATION_DIR, "story-export.js")
FINAL_EXPORT_ZIP_NAME = "story_export.zip"
# Selenium默认会将文件下载到项目根目录
FINAL_EXPORT_ZIP_PATH = os.path.join(BASE_DIR, FINAL_EXPORT_ZIP_NAME)

# --- API Endpoints ---
# Base URLs, Game ID will be added dynamically
UPLOADS_URL_TEMPLATE = f"https://api.itch.io/games/{{game_id}}/uploads"
DOWNLOAD_URL_TEMPLATE = f"https://api.itch.io/uploads/{{id}}/download"
# This is now only for the stable version
LATEST_VERSION_URL_TEMPLATE = f"https://itch.io/api/1/x/wharf/latest?game_id={{game_id}}&channel_name={{channel_name}}"

# --- Selenium Config ---
BROWSER_DOWNLOAD_DIR = BASE_DIR # Selenium将下载到此目录
BROWSER_TIMEOUT = 60 # 秒