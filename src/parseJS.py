import re

class JSTextExtractor:
    def __init__(self):
        self.extracted_texts = []

    def parse(self,lines:list):
        file_pos = 0
        self.in_string = False
        self.IDindex = 0
        self.lines = lines
        self.in_comment = False
        for line in lines:
            self._process_line(line, file_pos)
            file_pos += len(line)+1
        return self.extracted_texts

    def _process_line(self, line, line_start_pos):
        string_delimiter = None
        current_string = ""
        position = None
        line_comment = False
        if len(line)>=2 and line[0]==line[1]=="/":
            line_comment = True
        elif len(line)>=2 and line[0]=="/" and line[1]=="*":
            self.in_comment = True
            if len(line)>=2 and line[-2]=="*" and line[-1]=="/":
                self.in_comment = False
        if self.in_comment or line_comment:
            if len(line)>=2 and line[-2]=="*" and line[-1]=="/":
                self.in_comment = False
            return
        for char_pos, char in enumerate(line):
            if not self.in_string:
                if char in ["'", '"', '`']:
                    self.in_string = True
                    string_delimiter = char
                    current_string = char
                    position = line_start_pos + char_pos
            else:
                current_string += char
                if char == string_delimiter and line[char_pos-1] != '\\':
                    self.in_string = False
                    # contextMinLine = max(0,self.lines.index(line))
                    # contextMaxLine = max(len(self.lines),self.lines.index(line)+1)
                    self._add_extracted_text(current_string, position,line)
                    current_string = ""
                    position = None
        if self.in_string and current_string=="`":
            self.extracted_texts.append({
                'id':self.IDindex,
                'text': current_string,
                'position': line_start_pos,
                'context':line if len(line)<=500 else ""
            })
            self.IDindex+=1
        else:
            self.in_string = False

    def _add_extracted_text(self, text, position,context):
        # 使用正则表达式去除字符串定界符
        cleaned_text = re.sub(r'^[\'"`]|[\'"`]$', '', text)
        if cleaned_text:  # 只有在清理后的文本非空时才添加
            self.extracted_texts.append({
                'id':self.IDindex,
                'text': cleaned_text,
                'position': position,
                'context':context if len(context)<=500 else ""
            })
            self.IDindex+=1
        elif text:
            self.extracted_texts.append({
                'id':self.IDindex,
                'text': text[1:],  # 去掉开始定界符
                'position': position,
                'context':context if len(context)<=500 else ""
            })
            self.IDindex+=1
