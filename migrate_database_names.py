#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本：从trans/0.6.6e/js/database_names.json迁移翻译到pz_origin/0.7.0b/js/database_names.json
最终保存结果到pz_origin/0.7.0b+/js/database_names.json
"""

import json
import os
from typing import List, Dict, Any

def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 不存在")
        return []
    except json.JSONDecodeError as e:
        print(f"错误：解析JSON文件 {file_path} 失败: {e}")
        return []

def save_json_file(data: List[Dict[str, Any]], file_path: str) -> bool:
    """保存JSON文件"""
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"错误：保存文件 {file_path} 失败: {e}")
        return False

def migrate_translations(trans_data: List[Dict[str, Any]], pz_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """迁移翻译数据"""
    # 创建trans数据的字典映射，以original为key
    trans_dict = {}
    for item in trans_data:
        if 'original' in item and 'translation' in item:
            trans_dict[item['original']] = item['translation']
    
    print(f"从trans文件加载了 {len(trans_dict)} 个翻译条目")
    
    # 遍历pz数据，匹配original并添加translation
    migrated_count = 0
    result_data = []
    
    for item in pz_data:
        if 'original' in item:
            new_item = item.copy()  # 复制原始项
            original_text = item['original']
            
            # 如果在trans中找到匹配的original，添加translation
            if original_text in trans_dict:
                new_item['translation'] = trans_dict[original_text]
                migrated_count += 1
                # print(f"迁移: {original_text} -> {trans_dict[original_text]}")
                print(new_item['translation'])
            
            result_data.append(new_item)
        else:
            # 如果没有original字段，直接复制
            result_data.append(item.copy())
    
    print(f"成功迁移了 {migrated_count} 个翻译条目")
    return result_data

def main():
    """主函数"""
    # 文件路径
    trans_file = "trans/0.7.0b+/js/AmateurPornTown.json"
    pz_file = "pz_origin/0.7.0b/js/AmateurPornTown.json"
    output_file = "pz_origin/0.7.0b+/js/AmateurPornTown.json"
    
    print("开始数据迁移...")
    print(f"源翻译文件: {trans_file}")
    print(f"目标原始文件: {pz_file}")
    print(f"输出文件: {output_file}")
    print("-" * 50)
    
    # 加载数据
    print("正在加载trans文件...")
    trans_data = load_json_file(trans_file)
    if not trans_data:
        print("无法加载trans文件，退出")
        return
    
    print("正在加载pz文件...")
    pz_data = load_json_file(pz_file)
    if not pz_data:
        print("无法加载pz文件，退出")
        return
    
    print(f"trans文件包含 {len(trans_data)} 个条目")
    print(f"pz文件包含 {len(pz_data)} 个条目")
    print("-" * 50)
    
    # 执行迁移
    print("开始迁移翻译...")
    result_data = migrate_translations(trans_data, pz_data)
    
    print("-" * 50)
    print("正在保存结果...")
    if save_json_file(result_data, output_file):
        print(f"成功保存到: {output_file}")
        print(f"结果文件包含 {len(result_data)} 个条目")
    else:
        print("保存失败")

if __name__ == "__main__":
    main()