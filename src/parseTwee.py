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
        check_token = lambda s, *keywords: any(keyword in s for keyword in keywords)
        if check_token("<<"+macro_content,"<<if","<<elif","<<else","<<for") and self.peek(2)=="\n":
            if self.tempText.strip()!="" :
                self.extracted_texts_push("text",self.tempText.strip(),self.tempIndex)
                self.tempIndex = 0
                self.tempText = ""
            # if re.search(r'(?<!\[)["\'](.+?)["\'](?!\])',macro_content):
            # self.extracted_texts_push("Macro",f"<<{macro_content}>>",self.index-len(macro_content)-2)
            self.consume(2)  # Consume '>>'
            self.tempText += f"<<{macro_content}>>"
            if self.tempIndex==0:self.tempIndex=zeroIndex
            if DEBUG:logger.info(f"解析到宏: {macro_content}")
        else:
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
            'id': f"{self.passage}_{self.IDindex}",
            'type': type,
            'text': text,
            'position': position,
            'context':context,
            'hash': generate_hash(text) if i==0 else generate_hash(text)+str(i)
        })
        self.IDindex+=1

