import ujson as json
from src.parseJSv2 import JSParserV2
import os

def run_test():
    """
    测试 JSParserV3 的功能。
    """
    test_file = 'test_data.js'
    
    print(f"--- 开始测试 {test_file} ---")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 测试文件 {test_file} 未找到。")
        return

    # 初始化解析器
    parser = JSParserV2()
    
    # 解析内容
    extracted_data = parser.parse(content)
    
    if extracted_data is not None:
        print(f"--- 解析完成，共提取 {len(extracted_data)} 条文本 ---")
        
        # 将结果格式化为 JSON 并打印
        # 使用 ujson.dumps 以获得更好的性能和格式
        pretty_json = json.dumps(extracted_data, indent=4, ensure_ascii=False)
        print(pretty_json)
        
        # 将结果写入文件以便更详细地查看
        output_file = 'test_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_json)
        print(f"\n--- 详细结果已保存到 {output_file} ---")
        
    else:
        print("--- 解析失败 ---")

if __name__ == "__main__":
    run_test()
