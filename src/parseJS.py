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
        self.in_muti = False
        for line in lines:
            self._process_line(line, file_pos)
            file_pos += len(line)+1
        return self.extracted_texts

    def _process_line(self, line, line_start_pos):
        string_delimiter = None
        current_string = ""
        position = None
        line_comment = False
        line_idx=0
        for i in range(len(line)):
            if line[i].strip():
                line_idx=i
                break
        if len(line)>line_idx+1 and line[i]==line[line_idx+1]=="/":
            line_comment = True
        elif len(line)>line_idx+1 and line[line_idx]=="/" and line[line_idx+1]=="*":
            self.in_comment = True
            if len(line)>=2 and line[-2]=="*" and line[-1]=="/":
                self.in_comment = False
        if self.in_comment or line_comment:
            if len(line)>=2 and line[-2]=="*" and line[-1]=="/":
                self.in_comment = False
            return
        contextMinLine = max(0,self.lines.index(line)-1)
        contextMaxLine = max(len(self.lines),self.lines.index(line)+1)
        for char_pos, char in enumerate(line):
            if (not self.in_string):
                if char in ["'", '"', '`']:
                    self.in_string = True
                    if char=="`":
                        if not self.in_muti:self.in_muti = True
                    string_delimiter = char
                    current_string = char
                    position = line_start_pos + char_pos+1
            else:
                current_string += char
                if char == string_delimiter and line[char_pos-1] != '\\':
                    self.in_string = False
                    context = "\n".join(self.lines[contextMinLine:contextMaxLine])
                    if len(context)>=500:
                        context = line if len(line)<500 else ""
                    if char_pos+1<len(line) and (line[char_pos+1]!=":" or " " in current_string or re.search(r'[一-龟]',current_string)):
                        self._add_extracted_text(current_string, position,context)
                    current_string = ""
                    position = None
                elif char == "`" and self.in_muti and not self.in_string:
                    self.in_muti = False
                    context = "\n".join(self.lines[contextMinLine:contextMaxLine])
                    if len(context)>=500:
                        context = line if len(line)<500 else ""
                    self._add_extracted_text(line, position,context)
            if self.in_string and "+" in line:
                for i in range(len(line)):
                    if line[i].strip():
                        line_idx = i
                        break
                self.in_string = False
                context = "\n".join(self.lines[contextMinLine:contextMaxLine])
                if len(context)>=500:
                    context = line if len(line)<500 else ""
                self.extracted_texts.append({
                    'id':self.IDindex,
                    'text': line.strip(),
                    'position': line_start_pos+line_idx,
                    'context':context
                })
                self.IDindex+=1
                current_string = ""
                position = None
                break
        if self.in_muti:
            self.extracted_texts.append({
                'id':self.IDindex,
                'text': line if not current_string else current_string,
                'position': line_start_pos if not position else position-1,
                'context':"\n".join(self.lines[contextMinLine:contextMaxLine]) if len("\n".join(self.lines[contextMinLine:contextMaxLine]))<=1000 else line
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
                'context':context
            })
            self.IDindex+=1
        elif text:
            self.extracted_texts.append({
                'id':self.IDindex,
                'text': text[1:],  # 去掉开始定界符
                'position': position,
                'context':context
            })
            self.IDindex+=1
