import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from . import config

def export_story_from_html(html_path):
    """使用Selenium打开HTML，执行JS并下载文件"""
    print("  - 正在使用浏览器执行故事导出脚本...")
    if not os.path.exists(config.STORY_EXPORT_JS_PATH):
        print(f"  - 错误: 导出脚本不存在于: {config.STORY_EXPORT_JS_PATH}")
        return False

    # 配置Chrome以下载文件
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": config.BROWSER_DOWNLOAD_DIR}
    options.add_experimental_option("prefs", prefs)
    
    # 确保目标zip文件不存在
    if os.path.exists(config.FINAL_EXPORT_ZIP_PATH):
        os.remove(config.FINAL_EXPORT_ZIP_PATH)

    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("file://" + html_path)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("  - 页面已成功加载。")

        with open(config.STORY_EXPORT_JS_PATH, 'r', encoding='utf-8') as f:
            js_code = f.read()
        
        print("  - 正在执行导出脚本...")
        driver.execute_script(js_code)
        
        print(f"  - 等待 '{config.FINAL_EXPORT_ZIP_NAME}' 下载完成...")
        start_time = time.time()
        while not os.path.exists(config.FINAL_EXPORT_ZIP_PATH):
            time.sleep(1)
            if time.time() - start_time > config.BROWSER_TIMEOUT:
                print("  - 错误: 等待下载超时。")
                return False
        
        print(f"  - 成功下载文件: {config.FINAL_EXPORT_ZIP_PATH}")
        return True

    except Exception as e:
        print(f"  - 错误: 浏览器自动化过程中发生错误: {e}")
        return False
    finally:
        if driver:
            driver.quit()