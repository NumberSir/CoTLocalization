import re
import ujson as json
from .log import logger
import hashlib

def generate_hash(text):
    # 使用 SHA-256 算法
    hash_object = hashlib.md5(text.encode('utf-8'))
    return hash_object.hexdigest()

class JSParserV2:
    def __init__(self):
        self.extracted_texts = []
        self.current_line = ""
        self.in_object_block = False

    def parse(self, content):
        logger.info("开始解析文件")
        self.is_BOM = False
        if content.startswith('\ufeff'):
            content = content[1:]  # 跳过BOM
            self.index = 1  # 更新position以反映跳过的字节
            self.is_BOM = True
            logger.info("发现BOM")
        self.content = content
        self.index = 0
        self.position = 0
        self.length = len(content)
        self.tempText = ""
        self.tempIndex = 0
        self.IDindex = 0
        self.in_line_comment = False
        self.in_mutiline_comment = False
        self.object_level = 0
        self.content_lines = content.split("\n")

        while self.index < self.length:
            self.parse_element()
        # if self.tempText.strip()!="" :
        #     self.extracted_texts_push("text",self.tempText.strip(),self.tempIndex)
        #     self.tempIndex = 0
        #     self.tempText = ""

        logger.info("文件解析完成")

    def parse_element(self):
        char = self.content[self.index]
        if self.in_mutiline_comment:
            if char == '*' and self.peek() == '/':
                self.in_mutiline_comment = False
            self.index += 1
            return
        if self.in_line_comment:
            if char == '\n':
                self.in_line_comment = False
            self.index += 1
            return

        # logger.debug(f"正在解析字符: '{char}' {self.index}")
        if char == '/' and self.peek() == '/' and not self.tempText.strip():
            self.in_line_comment = True
        elif char == '/' and self.peek() == '*' and not self.tempText.strip():
            self.in_mutiline_comment = True
        elif char in ["'", '"', '`'] and "=" in [self.peek(-1),self.peek(-2)] and ("function" not in self.tempText) and not self.in_object_block and ("(" not in self.tempText and ")" not in self.tempText):
            self.parse_string()
        elif char == '[' and "=" in [self.peek(-1),self.peek(-2)] and ("function" not in self.tempText) and not self.in_object_block and ("(" not in self.tempText and ")" not in self.tempText):
            self.parse_array()
        elif char == '{':
            if ("function" in self.tempText) or ("(" in self.tempText and ")" in self.tempText and self.object_level==0):
                if "(" in self.tempText and ")" not in self.tempText:
                    self.tempText += char
                    self.index+=1
                else:
                    self.parse_function()
            elif ("Class " in self.tempText) or ("class " in self.tempText):
                self.tempText = ""
                self.index += 1
            else:
                self.parse_object()
        elif self.tempText.strip()=="" and char.strip() and char !="\n" and char !="\r" and not self.in_line_comment and not self.in_mutiline_comment:
            if char=="}" and self.object_level==1:
                self.consume_until("\n")
                self.tempText = ""
                self.object_level = 0
            else:
                self.tempText += char
            self.index+=1
        elif self.tempText.strip() and not self.in_line_comment and not self.in_mutiline_comment:
            if char=="}" and self.object_level==1:
                self.tempText += self.consume_until("\n")
                self.extracted_texts_push("object-rest",self.tempText,self.index-len(self.tempText))
                self.tempText = ""
                self.object_level = 0
            elif char==";" and self.peek()=="\n":
                self.extracted_texts_push("code",self.tempText+char,self.index-len(self.tempText))
                self.tempText = ""
            else:
                self.tempText += char
            self.index+=1
        else:
            self.index+=1
    
    def parse_string(self):
        start_index = self.index
        close_tag = self.content[self.index]
        open = True
        content = ""
        while open:
            content += self.consume_until(close_tag)
            if len(content)>=3 and content[-2] != "\\":
                open = False
            elif len(content)<3:
                open = False
        content += self.consume_until(";")+";"
        self.consume()
        content = self.tempText+content
        start_position = start_index-len(self.tempText)
        if close_tag == "`":
            content = content.split("\n")
            position_now = start_position
            for c in content:
                self.extracted_texts_push("string",c,position_now)
                position_now += len(c)+1
        else:
            self.extracted_texts_push("string",content,start_position)
        self.tempText = ""
    
    def parse_array(self):
        start_index = self.index
        array_level = 1
        content = "["
        open = True
        while open:
            text = self.consume_until("]")+"]"
            self.consume()
            if text[0]=="[":text=text[1:]
            for char in text:
                if char == '[':
                    array_level += 1
                elif array_level > 0 and char == ']':
                    array_level -= 1
            if array_level == 0:
                open = False
            content += text
        if content.count("{")>3 and len(content)>100:
            start_position = start_index+1
            object_in_array_parsr = JSParserV2()
            object_in_array_parsr.parse(content[1:])
            for obj in object_in_array_parsr.extracted_texts:
                self.extracted_texts_push("array-object",obj['text'],start_position+obj['position'],obj['context'])
            self.tempText = ""
            self.consume_until("\n")
            self.consume()
        else:
            content += self.consume_until("\n")
            self.consume()
            if "_cn_name" in self.content[start_index-15:start_index]:
                self.tempText += content
            else:
                self.extracted_texts_push("array",self.tempText+content,start_index-len(self.tempText))
                self.tempText = ""

    def parse_object(self):
        start_index = self.index
        if not self.in_object_block:
            self.in_object_block = True
        self.object_level += 1
        content = "{"
        open = True
        while open:
            text = self.consume_until("}")+"}"
            self.consume()
            if text[0]=="{":text=text[1:]
            if "{" in text or self.object_level>1:
                for char in text:
                    if char == '{':
                        self.object_level += 1
                    elif self.object_level > 0 and char == '}':
                        self.object_level -= 1
                if self.object_level == 1:
                    open = False
            else:
                open = False
                self.object_level=0
            content += text
        if self.object_level>=1 and self.peek()!=",":
            content += self.consume_until(",")+","
            self.consume()
        elif self.object_level==0:
            if "_cn_name" in self.content[start_index-15:start_index]:
                content += self.consume_until(";")+";"
            else:
                content += self.consume_until("\n")
            self.consume()
            self.in_object_block = False
        if "_cn_name" in self.content[start_index-15:start_index]:
            self.tempText += content
        else:
            self.extracted_texts_push("object",self.tempText+content,start_index-len(self.tempText))
            self.tempText = ""

    def parse_function(self):
        start_index = self.index
        level = 1
        content = "{"
        open = True
        while open:
            text = self.consume_until("}")+"}"
            self.consume()
            if text[0]=="{":text=text[1:]
            for char in text:
                if char == '{':
                    level += 1
                elif level > 0 and char == '}':
                    level -= 1
            # print(level,text)
            if level == 0:
                open = False
            content += text
        rest = self.consume_until("\n")
        self.extracted_texts_push("function",self.tempText+content+rest,start_index-len(self.tempText))
        self.tempText = ""

    def consume(self, count=1):
        consumed = self.content[self.index:self.index+count]
        self.index += count
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
            self.index += 1
        return self.content[start:self.index]

    def consume_while(self, condition):
        start = self.index
        while self.index < self.length and condition(self.content[self.index]):
            self.index += 1
        return self.content[start:self.index]

    def extracted_texts_push(self,type,text,position,context=""):
        if not text.strip():return
        text_lines = text.split("\n")
        if not context:
            contextMin = max(0,position-500)
            contextMax = min(len(self.content),position+100)
            context = (self.content[contextMin:contextMax])
        if self.content[position]!=text[0]:
            print(type,[text],position,self.content[position-5:position+5])
            a+1
        i = 0
        for t in self.extracted_texts:
            if t['text'] == text.replace("\\n","\\\\n"):
                i+=1
        self.extracted_texts.append({
            'id': f"{self.IDindex}",
            'type': type,
            'text': text.replace("\\n","\\\\n"),
            'position': position,
            'context':context,
            'hash': generate_hash(text) if i==0 else generate_hash(text)+str(i)
        })
        self.IDindex+=1