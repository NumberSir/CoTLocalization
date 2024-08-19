from .consts import *
from .log import logger
from .parseTwee import TweeParser
from .parseJS import JSTextExtractor

import ujson as json
import os,shutil,re,numpy

class Fetcher:
    def __init__(self):
        pass
    def _split_by_case(self,name):
        return re.findall('[A-Z][a-z]*', name)
    def marge_source(self):
        if DIR_MARGE_SOURCE.exists():
            shutil.rmtree(DIR_MARGE_SOURCE)
        os.makedirs(DIR_MARGE_SOURCE/"Passages", exist_ok=True)
        # 获取目录中所有文件
        files = [f for f in os.listdir(DIR_SOURCE/"Passages") if os.path.isfile(os.path.join(DIR_SOURCE/"Passages", f))]
        # 按前缀分组
        groups = {}
        for file in files:
            parts = self._split_by_case(file)
            if len(parts) > 1:
                prefix = ''.join(parts[:-1])
                if prefix not in groups:
                    groups[prefix] = []
                groups[prefix].append(file)

        # 在现有分组基础上再次合并
        merged_groups = {}
        for prefix, files in groups.items():
            found_match = False
            for existing_prefix in merged_groups:
                if prefix.startswith(existing_prefix) or existing_prefix.startswith(prefix):
                    merged_groups[existing_prefix].extend(files)
                    found_match = True
                    break
            if not found_match:
                merged_groups[prefix] = files
        groups = merged_groups
        # 合并每组文件
        for prefix, group_files in groups.items():
            merged_content = ""
            for file in group_files:
                with open(os.path.join(DIR_SOURCE/"Passages", file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    merged_content += content + "\n\n"
            # 写入合并后的文件
            with open(os.path.join(DIR_MARGE_SOURCE/"Passages", f"{prefix}.twee"), 'w', encoding='utf-8') as f:
                f.write(merged_content)
    def fetch_source(self):
        if DIR_FETCH.exists():
            shutil.rmtree(DIR_FETCH)
        os.makedirs(DIR_FETCH/"Passages", exist_ok=True)
        for root, dirs, files in os.walk(DIR_MARGE_SOURCE):
            for d in dirs:
                if not os.path.exists(DIR_FETCH/d):
                    os.makedirs(DIR_FETCH/d)
            for file in files:
                logger.info(f"parsing {file}")
                if file.endswith(".twee"):
                    with open(f"{root}\\{file}", "r", encoding="utf-8") as fp:
                        parser = TweeParser()
                        parser.parse(fp.read())
                    parser.extracted_texts.sort(key=lambda x:x['position'])
                    with open(root.replace("marge_source","fetch")+"\\"+file.replace('.twee','.json'),encoding="utf-8",mode="w+") as fp:
                        fp.write(json.dumps(parser.extracted_texts,ensure_ascii=False))
        os.makedirs(DIR_FETCH/"Widgets", exist_ok=True)
        for root, dirs, files in os.walk(DIR_SOURCE/"Widgets"):
            for d in dirs:
                if not os.path.exists(DIR_FETCH/d):
                    os.makedirs(DIR_FETCH/d)
            for file in files:
                logger.info(f"parsing {file}")
                if file.endswith(".twee"):
                    with open(f"{root}\\{file}", "r", encoding="utf-8") as fp:
                        parser = TweeParser()
                        parser.parse(fp.read())
                    parser.extracted_texts.sort(key=lambda x:x['position'])
                    with open(root.replace("source","fetch")+"\\"+file.replace('.twee','.json'),encoding="utf-8",mode="w+") as fp:
                        fp.write(json.dumps(parser.extracted_texts,ensure_ascii=False))
        os.makedirs(DIR_FETCH/"js", exist_ok=True)
        for root, dirs, files in os.walk(DIR_SOURCE/"js"):
            for d in dirs:
                if not os.path.exists(DIR_FETCH/d):
                    os.makedirs(DIR_FETCH/d)
            for file in files:
                logger.info(f"parsing {file}")
                if file.endswith(".js"):
                    with open(f"{root}\\{file}", "r", encoding="utf-8") as fp:
                        parser = JSTextExtractor()
                        parser.parse(fp.read().split("\n"))
                    parser.extracted_texts.sort(key=lambda x:x['position'])
                    with open(root.replace("source","fetch")+"\\"+file.replace('.js','.json'),encoding="utf-8",mode="w+") as fp:
                        fp.write(json.dumps(parser.extracted_texts,ensure_ascii=False))
    def convert_to_pz(self):
        if DIR_PZ_ORIGIN.exists():
            shutil.rmtree(DIR_PZ_ORIGIN)
        os.makedirs(DIR_PZ_ORIGIN, exist_ok=True)
        for root, dirs, files in os.walk(DIR_FETCH):
            for d in dirs:
                if not os.path.exists(DIR_PZ_ORIGIN/d):
                    os.makedirs(DIR_PZ_ORIGIN/d)
            for file in files:
                logger.info(f"convert {file}")
                with open(f"{root}\\{file}", "r", encoding="utf-8") as fp:
                    filedata = json.loads(fp.read())
                pzdata = []
                for d in filedata:
                    pzdata.append({
                        "key":d['id'] if ("Passages" in root) or ("Widgets" in root) else f"{file.replace('.json','')}_{d['id']}",
                        "original":d['text'],
                        "context":d['context']
                    })
                # if "database_names" in file or "worldgen" in file:
                #     pzdata = numpy.array(pzdata)
                #     pzdata = numpy.array_split(pzdata,3)
                #     for i in range(len(pzdata)):
                #         with open(root.replace("fetch","pz_origin")+"\\"+file.replace(".json",f"_{i}.json"),encoding="utf-8",mode="w+") as fp:
                #             fp.write(json.dumps(pzdata[i].tolist(),ensure_ascii=False))
                # else:
                with open(root.replace("fetch","pz_origin")+"\\"+file,encoding="utf-8",mode="w+") as fp:
                    fp.write(json.dumps(pzdata,ensure_ascii=False))