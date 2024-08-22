import ujson as json
import os
import shutil

from .consts import *
from .log import logger

class Replacer:
    def __init__(self):
        self.translation_files = {}
        pass
    def replace_file(self):
        if DIR_TRANSLATED_SOURCE.exists():
            shutil.rmtree(DIR_TRANSLATED_SOURCE)
        os.makedirs(DIR_TRANSLATED_SOURCE/"Passages", exist_ok=True)
        for root, dirs, files in os.walk(DIR_TRANS):
            for d in dirs:
                if not os.path.exists(DIR_TRANSLATED_SOURCE/d):
                    os.makedirs(DIR_TRANSLATED_SOURCE/d)
            for file in files:
                with open(f"{root}\\{file}", "r", encoding="utf-8") as fp:
                    pzdata = json.load(fp)
                with open(f"{root.replace('trans','fetch')}\\{file}", "r", encoding="utf-8") as fp:
                    fetch_data = json.load(fp)
                if "Passage" in root:
                    with open(f"{root.replace('trans','marge_source')}\\{file.replace('.json','.twee')}","r",encoding="utf-8") as fp:
                        file_content = fp.read()
                elif "Widget" in root:
                    with open(f"{root.replace('trans','source')}\\{file.replace('.json','.twee')}","r",encoding="utf-8") as fp:
                        file_content = fp.read()
                elif "js"==root[-2]+root[-1]:
                    with open(f"{root.replace('trans','source')}\\{file.replace('.json','.js')}","r",encoding="utf-8") as fp:
                        file_content = fp.read()
                else:
                    logger.error(f"no file {root}\{file}!")
                logger.info(f"file {file} readed")
                idx = 1
                delta_index = 0
                target_file_parts = []
                last_idx = 0
                try:
                    pzdata.sort(key=lambda x:fetch_data[x['key']]['position'])
                except:
                    print(pzdata)
                tempd = {}
                for d in pzdata:
                    if 'stage' not in d or d['stage']<1:continue
                    translation = ""
                    if d['key'] not in fetch_data:
                        logger.warning(f"{d['key']} not exist!")
                        continue
                    else:
                        if not fetch_data[d['key']]['text']:continue
                        if fetch_data[d['key']]['text'] in "'\"`":continue
                        position = fetch_data[d['key']]['position']
                        translation = d['translation'] if d['translation'] else fetch_data[d['key']]['text']
                    # if translation.startswith("<br>") and translation!="<br><br>" and translation!="<br>" and "js" not in root:
                    #     if not (file_content[last_idx:position].endswith("<br>")):position+=4
                    #     if "'" not in translation and "\"" not in translation:translation = translation.replace("<br>","<br>\n")
                    #     fetch_data[d['key']]['text'] = fetch_data[d['key']]['text'].replace("<br>","<br>\n")
                    if not translation:translation = fetch_data[d['key']]['text']
                    if "js" not in root:translation = translation.replace("\\n","\n")
                    # if "js" in root and "+" in translation:translation = "\""+translation
                    target_file_parts.append(file_content[last_idx:position])
                    target_file_parts.append(translation)
                    # if position!=fetch_data[d['key']]['position']:position-=4
                    # delta_index += (len(d['range']) - len(translation))
                    last_idx = position+len(fetch_data[d['key']]['text'])
                    if last_idx-1>=len(file_content):print(translation)
                    if file_content[last_idx-1]!=fetch_data[d['key']]['text'][-1]:
                        if file_content[last_idx]==fetch_data[d['key']]['text'][-1]:
                            last_idx += 1
                        elif last_idx+1<len(file_content) and file_content[last_idx+1]==fetch_data[d['key']]['text'][-1]:
                            last_idx = position+len(fetch_data[d['key']]['text'])+1
                    # if idx%1000==0:logger.info(f"replacing {idx+1}/{len(translation_files[zip_filename])}")
                    idx += 1

                target_file_parts.append(file_content[last_idx:])
                if "Passage" in root or "Widgets" in root:
                    with open(root.replace('trans','translated_source')+"\\"+file.replace('.json','.twee'),encoding="utf-8",mode="w+") as fp:
                        fp.write("".join(target_file_parts))
                elif "js" ==root[-2]+root[-1]:
                    with open(root.replace('trans','translated_source')+"\\"+file.replace('.json','.js'),encoding="utf-8",mode="w+") as fp:
                        fp.write("".join(target_file_parts))
                logger.info(f"writed {file} done")

    # def replace_main():
    #     if DIR_OUTPUT.exists():
    #         shutil.rmtree(DIR_OUTPUT)
    #     os.makedirs(DIR_OUTPUT, exist_ok=True)
    #     os.makedirs(DIR_NEWTOKENIZES, exist_ok=True)

    #     translation_files = {}
    #     for file in os.listdir(DIR_TRANS):
    #         with open(DIR_TRANS / file, 'r', encoding='utf-8') as fp:
    #             data = json.load(fp)

    #         translation_files[file] = {}
    #         for translation in data:
    #             translation_files[file][translation['key']] = translation['translation']
    #         logger.info(f"Successfully write in translation file {file}!")

    #     for file in os.listdir(DIR_SOURCE):
    #         filename = file[:-3]  # remove '.js'
    #         if f"{filename}.json" not in translation_files:
    #             logger.warning(f"No translation File name {filename}.json, skip")
    #             continue

    #         with open(DIR_SOURCE / file, 'r', encoding='utf-8') as fp:
    #             content = fp.read()

    #         zip_filename = f"{filename}.json"
    #         js_filename = file
    #         target_js = replace_js_file(zip_filename, js_filename, content, translation_files)

    #         with open(DIR_OUTPUT / file, encoding='utf-8', mode='w') as fp:
    #             fp.write(target_js)
    #         logger.info(f"output rewrite {file} ")

