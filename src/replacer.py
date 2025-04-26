import ujson as json
import os,re
import shutil
import emoji

from .consts import *
from .log import logger

class Replacer:
    def __init__(self,version):
        self.version = version
        self.sourcePath = DIR_SOURCE/self.version
        self.fetchPath = DIR_FETCH/self.version
        self.transPath = DIR_TRANS/self.version
        self.translatedPath = DIR_TRANSLATED_SOURCE/self.version
        self.translation_files = {}
        pass
    def replace_file(self):
        if self.translatedPath.exists():
            shutil.rmtree(self.translatedPath)
        os.makedirs(self.translatedPath/"Passages", exist_ok=True)
        for root, dirs, files in os.walk(self.transPath):
            for d in dirs:
                if not os.path.exists(self.translatedPath/d):
                    os.makedirs(self.translatedPath/d)
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
                pzdata.sort(key=lambda x:fetch_data[x['key']]['position'])
                tempd = {}
                for d in pzdata:
                    if 'stage' not in d or d['stage']!=1:
                        if "过时" in d['original']:continue
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
                    # if d['key']=="macros_73":print([file_content[last_idx],file_content[position],translation])
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
                    with open(root.replace('trans','translated_source')+"\\"+file.replace('.json','.twee'),encoding="utf-8",mode="w") as fp:
                        fp.write("".join(target_file_parts))
                elif "js" ==root[-2]+root[-1]:
                    with open(root.replace('trans','translated_source')+"\\"+file.replace('.json','.js'),encoding="utf-8",mode="w") as fp:
                        fp.write("".join(target_file_parts))
                logger.info(f"writed {file} done")

    def convert_to_i18n(self):
        i18n = {"typeB":{"TypeBOutputText":[],"TypeBInputStoryScript":[]}}
        with open(self.fetchPath/"hash_dict.json", "r", encoding="utf-8") as fp:
            hash_dict = json.load(fp)
        for root, dirs, files in os.walk(self.transPath):
            for file in files:
                with open(f"{root}\\{file}", "r", encoding="utf-8") as fp:
                    pzdata = json.load(fp)
                # with open(f"{root.replace('trans','fetch')}\\{file}", "r", encoding="utf-8") as fp:
                #     fetch_data = json.load(fp)
                # logger.info(f"file {file} readed")
                emojiDiffIdx = 0
                lineChangeCount = 0
                nowPassage = ""
                hash_dict_now = {}
                file_trans = {}
                for d in pzdata:
                    key=d['key'].split("_")
                    keynum = key.pop(-1)
                    if "js" not in root:
                        passagename = key[0]
                    else:
                        passagename = "_".join(key)
                    filename = passagename+(".js" if "js" in root else ".twee")
                    if filename not in file_trans:
                        file_trans[filename] = []
                    if '过时' not in d['original']:file_trans[filename].append(d)
                for filename in file_trans:
                    key=file_trans[filename][0]['key'].split("_")
                    keynum = key.pop(-1)
                    if "js" not in root:
                        passagename = key[0]
                    else:
                        passagename = "_".join(key)
                    emojiDiffIdx=0
                    hash_dict_now = hash_dict[passagename+(".js" if "js" in root else ".twee")]
                    id_hash_dict = {}
                    for hash in hash_dict_now:
                        id_hash_dict[hash_dict_now[hash]['id']] = {"hash":hash,"position":hash_dict_now[hash]['position']}
                    file_trans[filename].sort(key=lambda x: id_hash_dict[x['key']]['position'] if x['key'] in id_hash_dict else -1)
                    for d in file_trans[filename]:
                        key=d['key'].split("_")
                        keynum = key.pop(-1)
                        if "js" not in root:
                            passagename = key[0]
                        else:
                            passagename = "_".join(key)

                        if 'stage' not in d or d['stage']!=1:
                            if "过时" in d['original']:continue
                            for char in d['original']:
                                if emoji.is_emoji(char):
                                    emojiDiffIdx += 1
                            continue
                        if d['original']==d['translation']:
                            for char in d['original']:
                                if emoji.is_emoji(char):
                                    emojiDiffIdx += 1
                            continue
                        passageStartpos = 0
                        if d['key'] not in id_hash_dict:
                            logger.warning(f"{d['key']} not exist!")
                            for char in d['original']:
                                if emoji.is_emoji(char):
                                    emojiDiffIdx += 1
                            continue
                        if "js" not in root:
                            # passageStartpos = id_hash_dict[passagename+"_0"]["position"]
                            for fd in hash_dict_now.values():
                                if fd['type']=='passage_name':
                                    passageStartpos = fd['position']+len(passagename)+1
                                    break
                            d['original'] = d['original'].replace("\\n","\n")
                            d['translation'] = d['translation'].replace("\\n","\n")

                            orilist = re.split(r'(?<!\\)\n', d['original'])
                            translist = re.split(r'(?<!\\)\n', d['translation'])
                            if len(orilist)!=len(translist):
                                logger.error(f"{d['key']} \\n error!")
                                i18n['typeB']['TypeBInputStoryScript'].append({"pos":id_hash_dict[d['key']]['position']-passageStartpos+emojiDiffIdx,"pN":passagename.replace(" [widget]",""),"f":d['original'],"t":d['translation']})
                                for char in d['original']:
                                    if emoji.is_emoji(char):
                                        emojiDiffIdx += 1
                                continue
                            linepos = id_hash_dict[d['key']]['position']-passageStartpos
                            for i in range(len(translist)):
                                if orilist[i]==translist[i]:
                                    linepos+=len(orilist[i])+1
                                else:
                                    lineidx=0
                                    for j in range(len(orilist[i])):
                                        if orilist[i][j].strip():
                                            lineidx = j
                                            break
                                    i18n['typeB']['TypeBInputStoryScript'].append({"pos":linepos+lineidx+emojiDiffIdx,"pN":passagename.replace(" [widget]",""),"f":orilist[i].strip(),"t":translist[i].strip()})
                                    linepos+=len(orilist[i])+1
                                for char in orilist[i]:
                                    if emoji.is_emoji(char):
                                        emojiDiffIdx += 1
                        else:
                            d['original'] = d['original'].replace("\\n","\n")
                            d['translation'] = d['translation'].replace('\\\\n',"▲").replace("\\n","\n")
                            
                            orilist = re.split(r'(?<!\\)\n', d['original'])
                            translist = re.split(r'(?<!\\)\n', d['translation'])
                            if len(orilist)!=len(translist):
                                logger.error(f"{d['key']} \\n error!")
                                i18n['typeB']['TypeBOutputText'].append({"pos":passageStartpos+id_hash_dict[d['key']]['position']-passageStartpos+emojiDiffIdx,"f":d['original'],"t":d['translation'].replace("▲","\\n"),"fileName":passagename+".js","js":True})
                                for char in d['original']:
                                    if emoji.is_emoji(char):
                                        emojiDiffIdx += 1
                                continue
                            linepos = id_hash_dict[d['key']]['position']-passageStartpos
                            for i in range(len(translist)):
                                if orilist[i]==translist[i]:
                                    linepos+=len(orilist[i])+1
                                else:
                                    lineidx=0
                                    for j in range(len(orilist[i])):
                                        if orilist[i][j].strip():
                                            lineidx = j
                                            break
                                    i18n['typeB']['TypeBOutputText'].append({"pos":linepos+lineidx+emojiDiffIdx,"f":orilist[i].strip(),"t":translist[i].strip().replace("▲","\\n"),"fileName":passagename+".js","js":True})
                                    linepos+=len(orilist[i])+1
                                for char in orilist[i]:
                                    if emoji.is_emoji(char):
                                        emojiDiffIdx += 1
                            # i18n['typeB']['TypeBOutputText'].append({"pos":passageStartpos+fetch_data[d['key']]['position']+emojiDiffIdx,"f":d['original'],"t":d['translation'],"fileName":passagename+".js","js":True})
                            # for char in fetch_data[d['key']]['text']:
                            #     if emoji.is_emoji(char):
                            #         emojiDiffIdx += 1
        with open(self.translatedPath/"i18n.json",encoding="utf-8",mode="w") as fp:
            fp.write(json.dumps(i18n,ensure_ascii=False))
