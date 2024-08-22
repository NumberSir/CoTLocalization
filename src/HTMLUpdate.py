import os
from bs4 import BeautifulSoup
import re

from .consts import *
from .log import logger

class HTMLUpdater:
    def __init__(self,html_path):
        self.html_path = DIR_ROOT/html_path
        self.passage_folder = DIR_TRANSLATED_SOURCE/"Passages"
        self.widgets_folder = DIR_TRANSLATED_SOURCE/"Widgets"
        self.js_folder = DIR_TRANSLATED_SOURCE/"js"
        self.soup = None
    def update_main(self,save_path):
        self.read_html()
        self.update_passages()
        self.update_js()
        self.save_html(DIR_ROOT/save_path)

    def read_html(self):
        with open(self.html_path, 'r', encoding='utf-8') as file:
            self.soup = BeautifulSoup(file, 'html.parser')

    def update_passages(self):
        twee_files = self._get_twee_files()
        for twee_file in twee_files:
            self._update_passage_content(twee_file)

    def update_js(self):
        js_content = self._concatenate_js_files()
        script_tag = self.soup.find('script', id='twine-user-script')
        if script_tag:
            script_tag.string = js_content
            logger.info("js file updated")

    def save_html(self, output_path):
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(str(self.soup))

    def _get_twee_files(self):
        twee_files = []
        for folder in [self.passage_folder, self.widgets_folder]:
            twee_files.extend([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.twee')])
        return twee_files

    def _update_passage_content(self, twee_file):
        with open(twee_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 使用正则表达式匹配所有的 passage
        passages = re.findall(r':: (.+?)(?:\s*\[.*?\])?\n([\s\S]+?)(?=\n:: |\Z)', content)
        
        for passage_name, passage_content in passages:
            passage_tag = self.soup.find('tw-passagedata', attrs={'name': passage_name.strip()})
            if passage_tag:
                passage_tag.string = passage_content.strip()
                logger.info(f"Passage {passage_name} updated")
            else:
                logger.error(f"Warning: Passage '{passage_name}' not found in HTML.")

    def _concatenate_js_files(self):
        js_content = ""
        for js_file in os.listdir(self.js_folder):
            if js_file.endswith('.js'):
                with open(os.path.join(self.js_folder, js_file), 'r', encoding='utf-8') as file:
                    js_content += file.read() + "\n\n"
        return js_content

# 使用示例
if __name__ == "__main__":
    updater = HTMLUpdater()

    updater.read_html()
    updater.update_passages()
    updater.update_js()
    updater.save_html(DIR_ROOT/'CoT.html')
