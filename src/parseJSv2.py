import re
import ujson as json
from .log import logger
import hashlib

def generate_hash(text):
    # 使用 SHA-256 算法
    hash_object = hashlib.md5(text.encode('utf-8'))
    return hash_object.hexdigest()

class JSParserV2:
    def __init__(self, in_array = False):
        self.extracted_texts = []
        self.current_line = ""
        self.in_object_block = False
        self.variable_stack = []  # 用于追踪变量名层级
        self.object_key_stack = []  # 用于追踪对象键层级
        self.in_array = in_array
        self.keys_count = {}
        self.object_var_name = ""

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
                self.index += 2
                return
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
            trimmed_text = self.tempText.strip()
            # Heuristic to exclude control flow statements from being misidentified as functions.
            is_control_flow = any(trimmed_text.startswith(kw) for kw in ['if(', 'if (', 'for(', 'for (', 'while(', 'while (', 'switch(', 'switch ('])

            if not is_control_flow and (("function" in self.tempText) or ("(" in self.tempText and ")" in self.tempText and self.object_level==0)):
                if "(" in self.tempText and ")" not in self.tempText:
                    self.tempText += char
                    self.index+=1
                else:
                    self.parse_function()
            elif ((("Class " in self.tempText) or ("class " in self.tempText)) and "\"Class " not in self.tempText and not self.in_object_block):
                print(self.tempText)
                self.tempText = ""
                self.index += 1
            else:
                trimmed_text_before_equal = self.tempText.split("=")[0].strip()
                if not self.in_object_block:self.object_var_name = trimmed_text_before_equal
                self.parse_object()
        elif self.tempText.strip()=="" and char.strip() and char !="\n" and char !="\r" and not self.in_line_comment and not self.in_mutiline_comment:
            if char=="}" and self.object_level==1:
                self.consume_until("\n")
                self.consume()
                self.tempText = ""
                self.object_level = 0
            else:
                self.tempText += char
            self.index+=1
        elif self.tempText.strip() and not self.in_line_comment and not self.in_mutiline_comment:
            if "=" in self.tempText and char == '[':
                # 这是一个启发式规则，用于区分函数参数中的默认数组和真正的数组声明
                # 如果'('的数量多于')'，我们很可能在函数参数列表中
                if self.tempText.count('(') > self.tempText.count(')'):
                    pass  # 不是数组声明，继续累积
                else:
                    self.parse_array()
                    return

            # if char=="}" and self.object_level==1:
            #     self.tempText += self.consume_until("\n")
            #     self.extracted_texts_push("object-rest",self.tempText,self.index-len(self.tempText))
            #     self.tempText = ""
            #     self.object_level = 0
            if char==";" and (self.peek()=="\n" or self.peek()==" ") and not self.in_object_block:
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
        if self.peek(0) == ";":
            content += ";"
            self.consume()
        if content.count("{")>3 and len(content)>100:
            start_position = start_index+1
            object_in_array_parsr = JSParserV2(in_array=True)
            object_in_array_parsr.parse(content[1:])
            for obj in object_in_array_parsr.extracted_texts:
                self.extracted_texts_push("array-object",obj['text'],start_position+obj['position'],obj['context'])
            self.tempText = ""
            self.consume_until("\n")
            self.consume()
        else:
            if "_cn_name" in self.content[start_index-15:start_index]:
                self.tempText += content
            else:
                self.extracted_texts_push("array",self.tempText+content,start_index-len(self.tempText))
                self.tempText = ""

    def parse_object(self):
        start_index = self.index
        if not self.in_array:self.object_level += 1
        content = ""
        empty_object = False
        if self.peek()=="}" and self.peek(2) == ";":
            empty_object = True
        first_pro = self.consume_until(":")
        print(f"==={first_pro}===")
        self.consume()
        should_be_empty = self.consume_until("{").strip()
        self.index = start_index
        content = "{"
        should_extract_details = False
        if (not self.in_object_block and should_be_empty == "" and not self.in_array):
            should_extract_details = True
        print(f"------------\nshoudebeempty{should_be_empty}||", not self.in_object_block, empty_object,"\n------------",(should_extract_details))
        if (should_extract_details) and not empty_object:
            self.in_object_block = True
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
                temp_i = self.index
                temp_content = self.consume_until(",")+","
                if " =" in temp_content:
                    self.index = temp_i
                    content += self.consume_until("}\n")
                    content += "}"
                    self.object_level = 0
                    self.in_object_block = False
                else:
                    content += temp_content
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
        else:
            # (Object.freeze模式的逻辑保持不变)
            logger.warning(f"整体提取(Object.freeze模式) - 使用平衡括号法")
            
            # Find matching brace
            level = 1
            content_start_index = self.index # at '{'
            search_index = self.index + 1
            
            # This simplified brace matching does not account for braces inside strings or comments.
            # However, this is consistent with the rest of the parser's implementation.
            while level > 0 and search_index < self.length:
                char = self.content[search_index]
                if char == '{':
                    level += 1
                elif char == '}':
                    level -= 1
                search_index += 1
            
            # `search_index` is now at the position right after the matching '}'
            content = self.content[content_start_index:search_index]
            self.index = search_index

            # After finding the object, consume the rest of the statement, e.g., ');\n'
            rest = self.consume_until("\n")
            
            full_object_text = self.tempText + content + rest
            
            if not self.in_array:self.object_level -= 1
            if self.object_level == 0:self.in_object_block = False
            temp_i = self.index
            object_rest = self.consume_until("}")
            if object_rest.strip()=="" or object_rest.strip()==",":
                self.object_level = 0
                self.in_object_block = False
                self.consume()
                if self.peek(0)==";":
                    self.consume()
            else:
                self.index = temp_i
            logger.warning(self.tempText+content)
            self.extracted_texts_push("object", full_object_text, start_index - len(self.tempText))
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
            if self.peek(0)=="/" and self.peek(1)=="/":
                while self.peek(0) != "\n" and self.index < self.length:
                    self.index += 1
                continue
            if self.peek(0)=="/" and self.peek(1)=="*":
                self.index += 2
                logger.debug("进入多行注释")
                while self.index < self.length:
                    if self.peek(0) == "*" and self.peek(1) == "/":
                        self.index += 2  # 跳过 */
                        break
                    self.index += 1
                continue
            if self.content[self.index:self.index+len(end)] == end:
                break
            self.index += 1
        return self.content[start:self.index]

    def consume_while(self, condition):
        start = self.index
        while self.index < self.length and condition(self.content[self.index]):
            self.index += 1
        return self.content[start:self.index]
    
    def generate_semantic_key(self, text_type, text, context, position):
        """
        根据词条分析生成语义化的键值 (重构版，不依赖正则表达式解析)
        规则：
        1. 对象键名
        2. 变量赋值
        3. 函数定义
        4. 字符串内容摘要
        """
        logger.debug(f"开始生成语义键 - 类型: {text_type}")

        # --- 内部辅助函数定义开始 ---
        # 为了保持单一函数结构，辅助函数定义在内部

        def _clean_key(key, max_length=50):
            """清理键名，只保留字母、数字和下划线，替换其他字符为下划线。
            (替代原有的 re.sub(r'[^a-zA-Z0-9_]', '_', ...))
            """
            cleaned = []
            for char in key:
                if char.isalnum() or char == '_':
                    cleaned.append(char)
                else:
                    # 避免重复的下划线
                    if not cleaned or cleaned[-1] != '_':
                        cleaned.append('_')
            # 移除首尾可能的下划线并限制长度
            return "".join(cleaned).strip('_')[:max_length]

        def _get_word_before(s, index):
            """从指定索引向前提取一个标识符。"""
            end = index
            # 跳过索引前的空白
            while end > 0 and s[end-1].isspace():
                end -= 1
            start = end
            # 向前查找单词字符、下划线或点号
            while start > 0 and (s[start-1].isalnum() or s[start-1] == '_'):
                start -= 1
            return s[start:end]

        def _get_first_word(s):
            """提取字符串开头的第一个单词（标识符）。"""
            s = s.strip()
            end = 0
            # 简单的标识符定义：字母数字或下划线
            while end < len(s) and (s[end].isalnum() or s[end] == '_'):
                end += 1
            return s[:end]

        def _strip_quotes(s):
            """去除字符串首尾的引号（", ', `）。"""
            s = s.strip()
            if not s or len(s) < 2:
                return s
            if (s.startswith('"') and s.endswith('"')) or \
            (s.startswith("'") and s.endswith("'")) or \
            (s.startswith("`") and s.endswith("`")):
                return s[1:-1]
            return s

        # --- 内部辅助函数定义结束 ---

        # 准备工作：计算上下文
        # 复现原始逻辑: context[:context.find(text[:10]) if text[:10] in context else 0]
        prefix = text[:10]
        if prefix in context:
            context_before_position = context[:context.find(prefix)]
        else:
            # 如果不在上下文中，或者 text 为空，则取空字符串 (context[:0])
            context_before_position = ""

        text_stripped = text.strip()

        # 规则集 1: array-object (数组中的对象)
        # 目标：提取对象中第一个键值对的 "值"
        if text_type == 'array-object':
            try:
                # 1. 去除首尾空白和开头的 '{'
                inner_text = text_stripped
                if inner_text.startswith('{'):
                    inner_text = inner_text[1:].strip()
                
                # 2. 按换行符分割，取第一行
                first_line = inner_text.split('\n')[0].strip()
                
                # 3. 找到第一个冒号，取它后面的部分
                colon_index = first_line.find(':')
                if colon_index != -1:
                    value_part = first_line[colon_index+1:].strip()
                    
                    # 移除可能的尾随逗号 (例如 {"a": "b", ...})
                    if value_part.endswith(','):
                        value_part = value_part[:-1].strip()

                    # 4. 去掉可能存在的引号
                    value_part = _strip_quotes(value_part)
                    
                    # 5. 清理并生成键
                    if value_part:
                        clean_key = _clean_key(value_part)
                        logger.debug(f"根据第一行value找到键: {clean_key}")
                        return f"value_{clean_key}"

            except Exception as e:
                # 保留原有的错误处理
                logger.error(f"新规则解析失败: {e}")

        # 规则集 2: object (对象字面量或类定义)
        if text_type == 'object':
            # --- 主要规则：扫描到第一个不在引号内的逗号 (保持原有的健壮迭代逻辑) ---
            # 这部分原本就不是正则表达式，但它是健壮的，我们保留它
            if text.endswith('"'):
                text_i = len(text) - 1
                while text_i >= 0 and text[text_i] != '"':
                    text_i -= 1
                if text_i != -1:
                    text = text[:text_i+1]
                    text_stripped = _strip_quotes(text.strip())
                    if text_stripped:
                        return f"str_{_clean_key(text_stripped, max_length=100)}"
            if "=" in text:
                before_equal = text.split('=')[0].strip()
                if before_equal:
                    return f"obj_{_clean_key(before_equal,100)}"
            try:
                i = 0
                # 跳过开头的 '{' 和空白
                while i < len(text) and (text[i] == '{' or text[i].isspace()):
                    i += 1
                
                key_start = i
                in_double_quote = False
                in_single_quote = False
                
                while i < len(text) and text[i] != '}':
                    char = text[i]
                    
                    # 简化的引号跟踪（注意：这里和原文一样，不处理转义字符）
                    if char == '"' and not in_single_quote:
                        in_double_quote = not in_double_quote
                    elif char == "'" and not in_double_quote:
                        in_single_quote = not in_single_quote
                    elif char == ',' and not in_double_quote and not in_single_quote:
                        break # 找到第一个顶层逗号
                    
                    i += 1
                
                key_part_full = text[key_start:i].strip()
                
                if key_part_full:
                    # 从 "key": value 中提取 key
                    # 模拟原始逻辑：key_part.split(':')[0].strip()
                    colon_index = key_part_full.find(':')
                    if colon_index != -1:
                        key_name = key_part_full[:colon_index].strip()
                    else:
                        # 可能是 ES6 的简写属性 {prop} 或空对象
                        key_name = key_part_full
                    
                    # 注意：原始逻辑在这里没有去除引号，也没有调用 _clean_key 清理特殊字符，我们保持一致
                    clean_key = _strip_quotes(key_name) 
                    if clean_key:
                        logger.debug(f"通过扫描第一部分找到键: {clean_key}")
                        object_var_name = ""
                        if self.object_var_name:
                            object_var_name = self.object_var_name+"_"
                        return f"obj_{object_var_name}{clean_key}"

            except IndexError:
                pass # 扫描失败，继续使用下面的后备规则

            # --- 后备规则 ---
            # 检查 ES6 类定义: class ClothingGroup { ... }
            # 替代 re.search(r'^class\s+(\w+)', text)
            if text_stripped.startswith('class '):
                remaining = text_stripped[len('class '):].strip()
                class_name = _get_first_word(remaining)
                if class_name:
                    logger.debug(f"找到类定义: {class_name}")
                    return f"class_{class_name}"
            
            # 处理如 setup.AmateurPornTown = {}; 这样的简单对象初始化
            # 替代 re.search(r'setup\.(\w+)\s*=\s*\{', text)
            if text_stripped.startswith('setup.'):
                equal_index = text_stripped.find('=')
                if equal_index != -1:
                    after_equal = text_stripped[equal_index+1:].strip()
                    before_equal = text_stripped[:equal_index].strip()
                    var_name = _strip_quotes(before_equal)
                    logger.debug(f"在对象赋值中找到变量名: {var_name}")
                    return f"var_{var_name}"

        # 规则集 3: string (字符串)
        if text_type == 'string':
            # 3.1 检查是否是对象键名: "key":
            # 替代 re.search(r'["\']([^"\']+)["\']\s*:', text)
            first_char = text_stripped[0] if text_stripped else ''
            if first_char in ('"', "'", "`"):
                # 寻找对应的结束引号
                end_quote_index = text_stripped.find(first_char, 1)
                if end_quote_index != -1:
                    # 检查结束引号后是否紧跟冒号
                    after_quote = text_stripped[end_quote_index+1:].strip()
                    if after_quote.startswith(':'):
                        key_name = text_stripped[1:end_quote_index]
                        # 清理键名 (模拟原有的清理逻辑)
                        clean_key = _clean_key(key_name) 
                        logger.debug(f"找到对象键名: {clean_key}")
                        return f"key_{clean_key}"
            
            # 3.2 检查是否是属性值: prop: "value"
            # 替代 re.search(r'(\w+)\s*:\s*["\'`]([^"\'`]+)', text)
            colon_index = text_stripped.find(':')
            if colon_index != -1:
                prop_name_part = text_stripped[:colon_index].strip()
                prop_value_raw = text_stripped[colon_index+1:].strip()
                
                # 验证属性名是否有效（提取第一个单词）
                prop_name = _get_first_word(prop_name_part)

                if prop_name and prop_value_raw:
                    # 检查值是否被引号包裹并提取内容
                    prop_value = _strip_quotes(prop_value_raw)
                    if prop_value != prop_value_raw: # 确认确实移除了引号，说明是字符串值
                        clean_value = _clean_key(prop_value, max_length=15)
                        logger.debug(f"找到属性值: {prop_name}_{clean_value}")
                        return f"prop_{prop_name}_{clean_value}"

        # 规则集 4: 变量赋值 (通过上下文推断)
        # 替代 re.search(r'(\w+)\s*=\s*$', context_before_position)
        if context_before_position:
            context_stripped = context_before_position.rstrip()
            if context_stripped.endswith('='):
                # 提取等号前的单词
                # 注意：原始正则是 (\w+)，不包含点号，所以我们向前提取一个单词即可
                # 使用 _get_word_before 并取最后一部分可以模拟这个行为
                var_path = _get_word_before(context_stripped, len(context_stripped) - 1)
                if var_path:
                    # 只取最后一部分 (例如 setup.myVar -> myVar)
                    var_name = var_path
                    if var_name:
                        logger.debug(f"找到等号前变量名: {var_name}")
                        return f"var_{var_name}"

        # 规则集 5: 函数定义
        if text_type == 'function':
            # 5.1 Symbol 方法: [Symbol.iterator]() { ... }
            # 替代 re.search(r'^\[Symbol\.(\w+)\]\s*\((?:.|\n)*\)\s*\{', text)
            if text_stripped.startswith('[Symbol.'):
                end_bracket_index = text_stripped.find(']')
                if end_bracket_index != -1:
                    symbol_name = text_stripped[len('[Symbol.'):end_bracket_index]
                    # 验证后续是否为函数结构 (检查括号)
                    remaining = text_stripped[end_bracket_index+1:].strip()
                    if remaining.startswith('('):
                        logger.debug(f"找到Symbol方法: {symbol_name}")
                        # 验证 symbol_name 是否是有效的单词（模拟 \w+）
                        if symbol_name == _get_first_word(symbol_name):
                            return f"func_symbol_{symbol_name}"

            # 5.2 Getter/Setter: get methodName() { ... } 或 set methodName() { ... }
            # 替代 re.search(r'^(get|set)\s+(\w+)\s*\((?:.|\n)*\)\s*\{', text)
            access_type = None
            if text_stripped.startswith('get '):
                access_type = 'get'
                remaining = text_stripped[4:].strip()
            elif text_stripped.startswith('set '):
                access_type = 'set'
                remaining = text_stripped[4:].strip()
            
            if access_type:
                method_name = _get_first_word(remaining)
                if method_name:
                    logger.debug(f"找到{access_type}方法: {method_name}")
                    return f"func_{access_type}_{method_name}"

            # 5.3 函数赋值: setup.A.B = function ...
            # 替代 re.search(r'(\w+(?:\.\w+)*)\s*=\s*function', text)
            # 查找 '='
            equal_index = text_stripped.find('=')
            if equal_index != -1:
                after_equal = text_stripped[equal_index+1:].strip()
                if after_equal.startswith('function'):
                    full_path = text_stripped[:equal_index].strip()
                    if full_path:
                        # 提取最后一个部分作为函数名
                        func_name = full_path.split('.')[-1]
                        if func_name:
                            logger.debug(f"找到函数赋值: {func_name}")
                            return f"func_{func_name}"

            # 5.5 类方法: methodName(params) { ... } (注意：这个规则在原文中排在命名函数之前)
            # 替代 re.search(r'(\w+)\s*\((?:.|\n)*\)\s*(?://[^\n]*\n)?\s*\{', text)
            # 寻找第一个括号
            paren_index = text_stripped.find('(')
            if paren_index != -1:
                # 确保括号在第一个大括号之前（如果存在）
                brace_index = text_stripped.find('{')
                if brace_index == -1 or paren_index < brace_index:
                    # 提取括号前的部分
                    potential_name_part = text_stripped[:paren_index].strip()
                    
                    # 提取最后一个词，以处理可能的 async 等关键字
                    if potential_name_part:
                        potential_name = potential_name_part.split()[-1]
                    else:
                        potential_name = ""
                    
                    # 简单验证是否为有效标识符 (非空且是单词)
                    if potential_name and potential_name == _get_first_word(potential_name):
                        # 排除控制流关键字，增加健壮性
                        if potential_name not in ['if', 'for', 'while', 'switch', 'catch', 'function']:
                            logger.debug(f"找到类方法: {potential_name}")
                            return f"func_{potential_name}"

            # 5.4 命名函数: function functionName()
            # 替代 re.search(r'function\s+(\w+)', text)
            if text_stripped.startswith('function '):
                remaining = text_stripped[len('function '):].strip()
                func_name = _get_first_word(remaining)
                if func_name:
                    logger.debug(f"找到函数名: {func_name}")
                    return f"func_{func_name}"
            
            # 5.6 兜底：从context中搜索简单的变量赋值 (匿名函数)
            # 替代 re.search(r'(\w+)\s*=\s*function', context_before_position)
            # 注意：原文中的这个兜底逻辑有些复杂，它在寻找 context 中是否以 "= function" 结尾。
            # 但通常匿名函数赋值是 context 以 "=" 结尾，而 text 以 "function" 开头。
            
            # 如果 text 是匿名函数定义，我们再次检查规则4的上下文赋值逻辑，并使用 func_ 前缀
            if text_stripped.startswith('function') and context_before_position:
                context_stripped = context_before_position.rstrip()
                if context_stripped.endswith('='):
                    var_path = _get_word_before(context_stripped, len(context_stripped) - 1)
                    if var_path:
                        func_var = var_path
                        if func_var:
                            logger.debug(f"找到匿名函数变量名: {func_var}")
                            return f"func_{func_var}"
            first_line = text_stripped.split('\n')[0].strip()
            return f"func_{_clean_key(first_line)}"

        # 规则集 6: 数组
        if text_type == 'array':
            # 查找赋值操作符
            equal_index = text_stripped.find('=')

            if equal_index != -1:
                before_equal = text_stripped[:equal_index].strip()
                return f"arr_{_clean_key(before_equal)}"

            # 6.3 兜底：尝试从上下文提取数组变量名
            # 替代 re.search(r'(\w+)\s*=\s*\[', context_before_position)
            # 如果当前文本以 '[' 开头，赋值可能在上下文中
            if text_stripped.startswith('[') and context_before_position:
                context_stripped = context_before_position.rstrip()
                if context_stripped.endswith('='):
                    # 提取等号前的单词
                    var_path = _get_word_before(context_stripped, len(context_stripped) - 1)
                    if var_path:
                        array_name = var_path
                        if array_name:
                            logger.debug(f"从上下文找到数组变量名: {array_name}")
                            return f"arr_{array_name}"

        # 规则集 7: 代码块处理
        if text_type == 'code':
            # 尝试提取简单的变量赋值
            # 替代 re.search(r'(\w+)\s*=\s*(\w+)', text)
            equal_index = text_stripped.find('=')
            if equal_index != -1:
                before_equal = text_stripped[:equal_index].strip()
                if before_equal:
                    return f"code_{_clean_key(before_equal)}"
            
            # 如果没有找到赋值，使用文本摘要
            return f"code_{_clean_key(text_stripped, 50)}"

        # 规则集 8: 字符串内容摘要（兜底规则之一）
        if text_type == 'string':
            # 替代 re.search(r'["\'`]([^"\'`]{1,20})', text)
            
            # 尝试提取引号内的内容
            content_preview = _strip_quotes(text_stripped)
            
            # 如果内容和原文相同（说明没有引号），则使用原文
            if content_preview == text_stripped:
                # 如果原文就是被引号包裹的，_strip_quotes 应该已经处理了。
                # 这里的逻辑是为了确保即使没有引号也能生成摘要。
                pass

            clean_content = _clean_key(content_preview, 20)
            
            if clean_content:
                logger.debug(f"找到字符串内容摘要: {clean_content}")
                return f"str_{clean_content}"
            else:
                # 如果清理后为空，使用原始文本的清理版本
                clean_text = _clean_key(text_stripped, 20)
                return f"str_{clean_text if clean_text else 'empty'}"

        # 最终兜底方案：使用位置和类型
        # 移除了原代码中导致错误的 a+1
        logger.debug(f"使用兜底方案: {text_type}_{position},{text}");a+1
        return f"{text_type}_{position}"

    def extracted_texts_push(self,type,text,position,context=""):
        if not text.strip():return
        text_lines = text.split("\n")
        if not context:
            contextMin = max(0,position-500)
            contextMax = min(len(self.content),position+100)
            context = (self.content[contextMin:contextMax])
        if self.content[position]!=text[0]:
            print(type,[text],position,[self.content])
            a+1
        i = 0
        for t in self.extracted_texts:
            if t['text'] == text.replace("\\n","\\\\n"):
                i+=1
        
        # 调试日志：记录当前文本的上下文信息
        logger.debug(f"生成键值 - 类型: {type}, 文本: {text[:50]}..., 位置: {position}")
        
        # 生成基于词条分析的键值
        semantic_key = self.generate_semantic_key(type, text, context, position)
        logger.debug(f"生成的语义键: {semantic_key}")

        if semantic_key in self.keys_count:
            self.keys_count[semantic_key]+=1
            semantic_key+= str(self.keys_count[semantic_key])
        else:
            self.keys_count[semantic_key]=1
        
        self.extracted_texts.append({
            'id': semantic_key,
            'type': type,
            'text': text.replace("\\n","▲"),
            'position': position,
            'context':context,
            'hash': generate_hash(text) if i==0 else generate_hash(text)+str(i)
        })
        self.IDindex+=1