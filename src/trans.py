from .consts import *
from .log import logger
import os,shutil,difflib,re
import ujson as json


def trans(version,version_trans):
    # if DIR_PZ_ORIGIN.exists():
    #     shutil.rmtree(DIR_PZ_ORIGIN)
    # os.makedirs(DIR_PZ_ORIGIN, exist_ok=True)
    for root, dirs, files in os.walk(DIR_PZ_ORIGIN/version):
        for d in dirs:
            if not os.path.exists(DIR_TRANS/version/d):
                os.makedirs(DIR_TRANS/version/d)
        for file in files:
            if 'js' in root:continue
            logger.info(f"trans {file}")
            # try:
            with open(f"{root}\\{file}", "r", encoding="utf-8") as fp:
                pzdata = json.loads(fp.read())
            with open(f"{root.replace('pz_origin','fetch')}/{file}", "r", encoding="utf-8") as fp:
                fetchdata = json.loads(fp.read())
            with open(f"{root.replace(version,version_trans)}\\{file}", "r", encoding="utf-8") as fp:
                transdata = json.loads(fp.read())
            with open(f"{root.replace('pz_origin','fetch').replace(version,version_trans)}\\{file}", "r", encoding="utf-8") as fp:
                transFatch = json.loads(fp.read())
            errorKeys = []
            if len(pzdata)!=len(transdata):
                logger.error(f"len not equal {root}\{file} continue")
                for d in fetchdata.keys():
                    dname = d.split("_")[0]
                    if dname in errorKeys:continue
                    fetchcount = 0
                    for d in fetchdata.keys():
                        if d.split("_")[0] == dname:
                            fetchcount += 1
                    transcount = 0
                    for td in transFatch.keys():
                        if td.split("_")[0].split("[")[0][:-1] == dname:
                            transcount += 1
                    if fetchcount!= transcount:
                        if dname not in errorKeys:errorKeys.append(dname)
                print(errorKeys)
            for i in range(len(pzdata)):
                transkey = ""
                passage = pzdata[i]['key'].split("_")[0]
                if passage in errorKeys:
                    logger.error(f"passage {passage} errorKeys continue")
                    continue
                for j in range(len(transdata)):
                    key = transdata[j]['key'].split("_")[-1]
                    passagename = transdata[j]['key'].split("_")[0].split("[")[0][:-1]
                    if 'Widgets' in root:
                        passagename += " [widget]"
                    if pzdata[i]['key'] == f"{passagename}_{key}":
                        transkey = transdata[j]['key']
                        break
                if transkey == "":
                    logger.error(f"no key {pzdata[i]['key']} {passagename}_{key} continue")
                    continue
                trans = transFatch[transkey]['text']
                pzdata[i]['translation'] = trans
                pzdata[i]['stage'] = 1
            with open(root.replace("pz_origin","trans")+"\\"+file,encoding="utf-8",mode="w+") as fp:
                fp.write(json.dumps(pzdata,ensure_ascii=False))
            # continue
            # except:
            #     logger.error(f"no file {root}\{file} continue")
            #     continue
            # pzdata.sort(key=lambda x:x['position'])
            # transdata.sort(key=lambda x:x['position'])
            # for i in range(len(pzdata)):
            #     if pzdata[i]['key'] == transdata[i]['key']:
            #         pzdata[i]['translation'] = transdata[i]['original']
            #         pzdata[i]['stage'] = 1
            with open(root.replace("pz_origin","trans")+"\\"+file,encoding="utf-8",mode="w+") as fp:
                fp.write(json.dumps(pzdata,ensure_ascii=False))

def trans_from_pz(pzversion,version):
    for root, dirs, files in os.walk(DIR_TRANS/pzversion):
        # for d in dirs:
        #     if not os.path.exists(DIR_PZ_ORIGIN/d):
        #         os.makedirs(DIR_PZ_ORIGIN/d)
        for file in files:
            # if 'js' not in root:continue
            logger.info(f"trans {file}")
            try:
                with open(f"{root.replace('trans','fetch')}\\{file}", "r", encoding="utf-8") as fp:
                    data = json.loads(fp.read())
                with open(f"{root.replace(pzversion,version).replace('trans','fetch')}\\{file}", "r", encoding="utf-8") as fp:
                    newdata = json.loads(fp.read())
                with open(f"{root}\\{file}", "r", encoding="utf-8") as fp:
                    trans = json.loads(fp.read())
                with open(f"{root.replace(pzversion,version).replace('trans','pz_origin')}\\{file}", "r", encoding="utf-8") as fp:
                    newpzdata = json.loads(fp.read())
            except:
                logger.error(f"no file {root}\{file} continue")
                continue
            transdict = {}
            for i, item in enumerate(trans):
                if item['original'].replace("\\n","\n") not in transdict:
                    transdict[item['original'].replace("\\n","\n") ] = []
                transdict[item['original'].replace("\\n","\n") ].append((i, item))
            for i, item1 in enumerate(newpzdata):
                if item1['original'].replace("\/","/") in transdict:
                    for j,item2 in enumerate(transdict[item1['original']]):
                        item2 = item2[1]
                        if 'context' in item2:
                            if difflib.SequenceMatcher(None,item2['context'].replace("\\n","\n").replace("&lt;","<").replace("&gt;",">"),newpzdata[i]['context'].replace("\/","/")).ratio()>0.75 and item2['original'].replace("\\n","\n")==newpzdata[i]['original'].replace("\/","/"):
                                if item2['translation']!="" and item2['stage']==1:
                                    newpzdata[i]['translation'] = item2['translation'].replace("\\n","\n")
                                    newpzdata[i]['stage']=1
                                break
                        else:
                            if item2['original'].replace("\\n","\n")==newpzdata[i]['original'].replace("\/","/"):
                                if item2['translation']!="" and item2['stage']==1:
                                    newpzdata[i]['translation'] = item2['translation'].replace("\\n","\n")
                                    newpzdata[i]['stage']=1
                                break
            # for i in range(len(newpzdata)):
            #     if i%100==0:logger.info(f"{i}/{len(newpzdata)}")
            #     for j in range(max(0,i-250),min(len(trans),i+250)):
            #         if 'context' in trans[j]:
            #             if "names" in file:print(difflib.SequenceMatcher(None,trans[j]['context'],newpzdata[i]['context']).ratio()>0.75,trans[j]['original']==newpzdata[i]['original'])
            #             if difflib.SequenceMatcher(None,trans[j]['context'],newpzdata[i]['context']).ratio()>0.75 and trans[j]['original']==newpzdata[i]['original']:
            #                 if trans[j]['translation']!="" and trans[j]['stage']==1:
            #                     newpzdata[i]['translation'] = trans[j]['translation']
            #                     newpzdata[i]['stage']=1
            #                 break
            #         else:
            #             if trans[j]['original']==newpzdata[i]['original']:
            #                 if trans[j]['translation']!="" and trans[j]['stage']==1:
            #                     newpzdata[i]['translation'] = trans[j]['translation']
            #                     newpzdata[i]['stage']=1
            #                 break
            with open(root.replace(pzversion,version).replace("trans","pz_origin")+"\\"+file,encoding="utf-8",mode="w+") as fp:
                fp.write(json.dumps(newpzdata,ensure_ascii=False))
def trans_from_trans(pzfile,newfile):
    with open(pzfile, "r", encoding="utf-8") as fp:
        pzdata = json.loads(fp.read())
    with open(newfile, "r", encoding="utf-8") as fp:
        newdata = json.loads(fp.read())
    for i in range(len(pzdata)):
        if pzdata[i]['stage'] == 1:
            newdata[i]['translation'] = pzdata[i]['translation']
            newdata[i]['stage'] = 1
    with open(newfile,encoding="utf-8",mode="w+") as fp:
        fp.write(json.dumps(newdata,ensure_ascii=False))
