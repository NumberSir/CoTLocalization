from .consts import *
from .log import logger
import os,shutil,difflib,re
import ujson as json


def trans():
    # if DIR_PZ_ORIGIN.exists():
    #     shutil.rmtree(DIR_PZ_ORIGIN)
    # os.makedirs(DIR_PZ_ORIGIN, exist_ok=True)
    for root, dirs, files in os.walk(DIR_PZ_ORIGIN):
        # for d in dirs:
        #     if not os.path.exists(DIR_PZ_ORIGIN/d):
        #         os.makedirs(DIR_PZ_ORIGIN/d)
        for file in files:
            # if 'js' not in root:continue
            logger.info(f"trans {file}")
            try:
                with open(f"{root.replace('pz_origin','oldfetch')}\\{file}", "r", encoding="utf-8") as fp:
                    olddata = json.loads(fp.read())
                with open(f"{root.replace('pz_origin','fetch')}\\{file}", "r", encoding="utf-8") as fp:
                    newdata = json.loads(fp.read())
                with open(f"{root}\\{file}", "r", encoding="utf-8") as fp:
                    pzdata = json.loads(fp.read())
            except:
                logger.error(f"no file {root}\{file} continue")
                continue
            if re.search(r'[一-龟]',json.dumps(olddata,ensure_ascii=False)):
                for i in range(len(pzdata)):
                    try:
                        old = olddata[pzdata[i]['key']]
                    except:
                        old = newdata[pzdata[i]['key']]
                    new = newdata[pzdata[i]['key']]
                    if old['id'] == new['id'] and old['text']!=new['text'] and re.search(r'[一-龟]',old['text']):
                        pzdata[i]['translation'] = old['text']
                        pzdata[i]['stage'] = 1
            with open(root.replace("pz_origin","trans")+"\\"+file,encoding="utf-8",mode="w+") as fp:
                fp.write(json.dumps(pzdata,ensure_ascii=False))