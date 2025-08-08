import re
import ujson as json
from .log import logger
from .parseJS4Twee import JSTextExtractor
from .parseJSv2 import JSParserV2
import hashlib

def generate_hash(text):
    # 使用 SHA-256 算法
    hash_object = hashlib.md5(text.encode('utf-8'))
    return hash_object.hexdigest()

import re
import hashlib
# ... 其他导入 ...

def sanitize_key_part(text):
    # 规范化并清理文本，使其适合作为Key的一部分
    text = text.lower()
    # 移除非字母数字字符
    text = re.sub(r'[^a-z0-9]', '_', text)
    # 合并多个下划线并去除首尾下划线
    text = re.sub(r'_+', '_', text).strip('_')
    return text

def generate_fingerprint(text, max_length=40):
    # 1. 提取人类可读文本
    
    # 提取宏参数中的字符串
    macro_strings = []
    macros = re.findall(r'<<.*?>>', text, re.DOTALL)
    for macro in macros:
        # 在宏内部找引用的字符串
        strings = re.findall(r'"(.*?)"|\'(.*?)\'', macro)
        for s1, s2 in strings:
            macro_strings.append(s1 or s2)

    # 提取链接中的文本 [[text|link]], [[link<-text]], [[text->link]] 或 [[text]]
    links = []
    link_matches = re.findall(r'\[\[(.*?)\]\]', text)
    for link in link_matches:
        if '|' in link:
            links.append(link.split('|')[0])
        elif '<-' in link:
            links.append(link.split('<-')[1])
        elif '->' in link:
             links.append(link.split('->')[0])
        else:
            links.append(link)

    # 移除宏、HTML标签和链接结构，保留纯文本部分
    # text_only = re.sub(r'<<.*?>>', ' ', text, flags=re.DOTALL)
    text_only = re.sub(r'(?<![<])<(?![<])[^>]*>|<<(?:switch|case|default|if|elif|else)[^>]*>>', ' ', text, flags=re.DOTALL)
    text_only = re.sub(r'\[\[.*?\]\]', ' ', text_only, flags=re.DOTALL)

    # 合并所有提取到的文本
    all_parts = [text_only.strip()] + links + macro_strings
    all_text = " ".join(filter(None, all_parts))
        
    fingerprint = sanitize_key_part(all_text)

    # 2. 回退策略 1：结构指纹
    if not fingerprint:
        # 提取宏名称 (例如 <<if>> 或 <</if>>)
        macros = re.findall(r'<<\/?([a-zA-Z0-9_]+)', text)
        if macros:
            # 使用前几个独特的宏名称
            unique_macros = sorted(list(set(macros)), key=macros.index) # 保持顺序
            fingerprint = "_".join(unique_macros[:3])

    # 3. 截断
    if len(fingerprint) > max_length:
        fingerprint = fingerprint[:max_length].strip('_')
    
    # 4. 回退策略 2：短哈希
    if not fingerprint:
        # 使用原有的 generate_hash 函数
        return f"hash_{generate_hash(text)[:8]}"
        
    return fingerprint

DEBUG = False
class TweeParser:
    def __init__(self):
        self.tokens = {
            'PASSAGE_START': r'::',
            'LINK': r'\[\[',
            'LINK_END': r'\]\]',
            'MACRO_START': r'<<',
            'MACRO_END': r'>>',
            'VARIABLE': r'\$',
            'NEWLINE': r'\n',
            'HTML_TAG_START': r'<',
            'HTML_TAG_END': r'>',
            'JS_START': r'<<script>>',
            'JS_END': r'<</script>>'
        }
        self.extracted_texts = []
        self.current_line = 1
        self.current_column = 0
        self.in_js_block = False
        self.passage_keys_count = {}

    def parse(self, content):
        logger.info("开始解析文件")
        self.content = content
        self.index = 0
        self.position = 0
        self.length = len(content)
        self.tempText = ""
        self.tempIndex = 0
        self.IDindex = 0
        self.passage = ""

        while self.index < self.length:
            self.parse_element()
        if self.tempText.strip()!="" :
            self.extracted_texts_push("text",self.tempText.strip(),self.tempIndex)
            self.tempIndex = 0
            self.tempText = ""

        logger.info("文件解析完成")

    def parse_element(self):
        if self.in_js_block:
            self.parse_js_content()
            return

        char = self.content[self.index]

        if DEBUG:logger.debug(f"正在解析字符: '{char}' {self.index}")
        if char == ':' and self.peek() == ':':
            self.parse_passage()
        elif char == '[' and self.peek() == '[':
            self.parse_link()
        elif self.content[self.index:].startswith('<<script>>'):
            self.parse_js_block_start()
        elif char == '<' and self.peek() == '<':
            self.parse_macro()
        elif char == '<':
            self.parse_html_tag()
        # elif char == '$':
        #     self.parse_variable()
        # elif char == '\n':
        #     self.current_line += 1
        #     self.current_column = 0
        #     self.index += 1
        elif char.strip() and char !="\n" and char !="\r":
            self.parse_text("")
        elif char=="\n" and self.peek() == "\n":
            if self.tempText.strip()!="":
                self.extracted_texts_push("text",self.tempText.strip(),self.tempIndex)
                self.tempIndex = 0
                self.tempText = ""
            self.index+=2
        elif self.tempText.strip():
            self.tempText += char
            self.index+=1
        else:
            self.index+=1

    def parse_passage(self):
        if DEBUG:logger.debug(f"开始解析段落 at 行 {self.current_line}, 列 {self.current_column}")
        self.consume(3)  # Consume ':: '
        passage_name = self.consume_until('\n')
        if passage_name!=self.passage:
            self.passage = passage_name
            self.IDindex = 0
            self.passage_keys_count = {}
        self.extracted_texts_push("passage_name",passage_name,self.index-len(passage_name))
        # logger.info(f"解析到段落名: {passage_name}")

    def parse_link(self):
        if DEBUG:logger.debug(f"开始解析链接 at 行 {self.current_line}, 列 {self.current_column}")
        self.consume(2)  # Consume '[['
        link_text = self.consume_until(']]')
        self.extracted_texts_push("link",f"[[{link_text}]]",self.index - len(link_text)-2)
        self.consume(2)  # Consume ']]'
        # logger.info(f"解析到链接: {link_text}")

    def parse_macro(self):
        if DEBUG:logger.debug(f"开始解析宏 at 行 {self.current_line}, 列 {self.current_column}")
        zeroIndex = self.index
        self.consume(2)  # Consume '<<'
        macro_content = self.consume_until('>>')

        content = macro_content.strip()
        # 处理闭合标签（如 <</if>>），移除斜杠后再次去除首尾空格
        _content = content[1:].strip() if content.startswith('/') else content
        command = ""
        if _content:
            # 分割内容，获取第一个单词作为命令名称
            parts = _content.split()
            if parts:
                command = parts[0].lower()

        # 定义需要跳过的 if 相关命令列表 (Twee也常使用 elseif)
        # if_related_commands = ["if", "else", "elif", "elseif"]
        # is_if_related = command in if_related_commands
        is_if_related = False

        check_token = lambda s, *keywords: any(keyword in s for keyword in keywords)
        if check_token("<<"+macro_content,"<<if","<<elif","<<else","<<for") and self.peek(2)=="\n":
            if self.tempText.strip()!="" :
                self.extracted_texts_push("text",self.tempText.strip(),self.tempIndex)
                self.tempIndex = 0
                self.tempText = ""
            # if re.search(r'(?<!\[)["\'](.+?)["\'](?!\])',macro_content):
            # self.extracted_texts_push("Macro",f"<<{macro_content}>>",self.index-len(macro_content)-2)
            self.consume(2)  # Consume '>>'
            if not is_if_related:
                self.tempText += f"<<{macro_content}>>"
                if self.tempIndex==0:self.tempIndex=zeroIndex
                if DEBUG:logger.info(f"解析到宏: {macro_content}")
        else:
            if is_if_related:
                self.consume(2) # Consume '>>'
                if DEBUG:logger.info(f"解析并跳过内联IF宏: {macro_content}")
            else:
                # 原始逻辑：其他内联宏（如 <<link>>, <<bathroom>>）视为文本的一部分
                self.index = zeroIndex
                self.parse_text("macro")

    def parse_html_tag(self):
        # logger.debug(f"开始解析HTML标签 at 行 {self.current_line}, 列 {self.current_column}")
        zeroIndex=self.index
        self.consume(1)
        tag_content = self.consume_until('>')
        if "=" in tag_content:
            self.index = zeroIndex
            self.consume(1)
            tag_content = self.consume_until('=')
            tag_content+="="
            if self.peek()=="'":
                self.consume(2)
                tag_content += "'"+self.consume_until('\'')
            elif self.peek()=="\"":
                self.consume(2)
                tag_content += "\""+self.consume_until('"')
            else:
                self.consume(1)
            
            tag_content += self.consume_until('>')
            # self.extracted_texts_push("HTML",f"{tag_content}>",zeroIndex)
        self.consume(1)  # Consume '>'
        if self.tempText.strip()!="" and (tag_content=="br" and self.peek()=="b" and self.peek(2)=="r" and self.peek(3)==">"):
            self.extracted_texts_push("text",self.tempText.strip(),self.tempIndex)
            self.tempIndex = 0
            self.tempText = ""
            if (tag_content=="br" and self.peek()=="b" and self.peek(2)=="r" and self.peek(3)==">"):
                self.index += 4
        else:
            self.tempText += f"<{tag_content}>"
            if self.tempIndex==0:self.tempIndex=zeroIndex
        # logger.info(f"跳过HTML标签: <{tag_content}>")

    def parse_variable(self):
        # logger.debug(f"开始解析变量 at 行 {self.current_line}, 列 {self.current_column}")
        self.consume(1)  # Consume '$'
        variable_name = self.consume_while(lambda c: c.isalnum() or c == '_')
        # logger.info(f"解析到变量: ${variable_name}")

    def parse_text(self,type):
        if type=="macro":
            self.consume(2)
        zeroIndex = self.index
        text = self.consume_until("\n\n")
        if "<" in text:
            self.index = zeroIndex
            text = self.consume_while(lambda c: c not in '<' and not (c==':' and self.peek()==":"))
        if type=="macro":
            self.tempText += "<<"+text
            if self.tempIndex==0:self.tempIndex=zeroIndex-2
        elif text.strip():
            self.tempText += text
            if self.tempIndex==0:self.tempIndex=zeroIndex
        # elif text.strip():
        #     self.extracted_texts.append({
        #         'type': 'text',
        #         'text': text,
        #         'position': self.index-len(text)
        #     })
        #     if DEBUG:logger.debug(f"解析到文本: {text[:20]}... at 行 {self.current_line}, 列 {self.current_column - len(text)}")

    def parse_js_block_start(self):
        if self.tempText.strip()!="" :
            self.tempText += f"<<script>>"
            self.extracted_texts_push("text",self.tempText.strip(),self.tempIndex)
            self.tempIndex = 0
            self.tempText = ""
        if DEBUG:logger.debug(f"开始解析JavaScript代码块 at 行 {self.current_line}, 列 {self.current_column}")
        self.consume(12)  # Consume '<<script>>'
        self.in_js_block = True
        if DEBUG:logger.info("进入JavaScript代码块")

    def parse_js_content(self):
        js_content = self.consume_until('<</script>>')
        parser = JSParserV2()
        parser.parse(js_content)
        for p in parser.extracted_texts:
            self.extracted_texts_push("js_code",p['text'],p['position']+self.index-len(js_content),p["context"])
        if self.content[self.index:].startswith('<</script>>'):
            self.consume(12)  # Consume '</script>'
            self.in_js_block = False
        #     logger.info("退出JavaScript代码块")
        if DEBUG:logger.info(f"解析到JavaScript代码: {js_content[:30]}...")

    def consume(self, count=1):
        consumed = self.content[self.index:self.index+count]
        self.index += count
        self.current_column += count
        return consumed

    def peek(self,count=1):
        if self.index + count < self.length:
            return self.content[self.index + count]
        return None

    def consume_until(self, end):
        start = self.index
        while self.index < self.length:
            if self.content[self.index:self.index+len(end)] == end:
                break
            if self.content[self.index] == '\n':
                self.current_line += 1
                self.current_column = 0
            else:
                self.current_column += 1
            self.index += 1
        return self.content[start:self.index]

    def consume_while(self, condition):
        start = self.index
        while self.index < self.length and condition(self.content[self.index]):
            self.current_column += 1
            self.index += 1
        return self.content[start:self.index]
    def extracted_texts_push(self,type,text,position,context=""):
        if not text.strip():return
        # --- 新的稳定 Key 生成逻辑 ---
        # 确保Passage名称也被规范化
        passage_prefix = self.passage if self.passage else "Global"
        if type == "passage_name":
            fingerprint = "title"
        else:
            # 使用我们定义的函数生成指纹
            fingerprint = generate_fingerprint(text)
        base_key = f"{passage_prefix}_{fingerprint}"
        # 冲突解决
        if base_key in self.passage_keys_count:
            base_key = f"{passage_prefix}_{generate_fingerprint(text,80)}"
            if base_key not in self.passage_keys_count:
                self.passage_keys_count[base_key] = 1
                unique_id = base_key
            else:
                self.passage_keys_count[base_key] += 1
                count = self.passage_keys_count[base_key]
                # 添加后缀，例如 _2, _3
                unique_id = f"{base_key}_{count}"
        else:
            self.passage_keys_count[base_key] = 1
            unique_id = base_key

        contextStat = max(0,len(self.extracted_texts)-3)
        if not context:
            for i in range(contextStat,len(self.extracted_texts)):
                context += self.extracted_texts[i]['text']
        if self.content[position]!=text[0]:
            print(type,text,position,self.content[position-5:position+5])
            a+1
        i=0
        for t in self.extracted_texts:
            if t['text'] == text:
                i+=1
        self.extracted_texts.append({
            'id': unique_id,
            'type': type,
            'text': text,
            'position': position,
            'context':context,
            'hash': generate_hash(text) if i==0 else generate_hash(text)+str(i)
        })
        self.IDindex+=1

