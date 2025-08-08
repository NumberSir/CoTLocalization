#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量数据迁移脚本：从trans/0.6.6e/js/目录迁移所有数据库翻译文件到pz_origin/0.7.0b/js/
最终将结果保存在pz_origin/0.7.0b+/js/目录
"""

import json
import os
import glob
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

def migrate_translations(trans_data: List[Dict[str, Any]], pz_data: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], int]:
    """迁移翻译数据"""
    # 创建trans数据的字典映射，以original为key
    trans_dict = {}
    for item in trans_data:
        if 'original' in item and 'translation' in item:
            trans_dict[item['original']] = item['translation']
    
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
            
            result_data.append(new_item)
        else:
            # 如果没有original字段，直接复制
            result_data.append(item.copy())
    
    return result_data, migrated_count

def get_json_files(directory: str) -> List[str]:
    """获取目录中的所有JSON文件"""
    pattern = os.path.join(directory, "*.json")
    return glob.glob(pattern)

def process_single_file(trans_file: str, pz_file: str, output_file: str) -> bool:
    """处理单个文件的迁移"""
    print(f"\n处理文件: {os.path.basename(trans_file)}")
    print(f"  源翻译文件: {trans_file}")
    print(f"  目标原始文件: {pz_file}")
    print(f"  输出文件: {output_file}")
    
    # 检查源文件是否存在
    if not os.path.exists(trans_file):
        print(f"  警告：源翻译文件不存在，跳过")
        return False
    
    if not os.path.exists(pz_file):
        print(f"  警告：目标原始文件不存在，跳过")
        return False
    
    # 加载数据
    trans_data = load_json_file(trans_file)
    pz_data = load_json_file(pz_file)
    
    if not trans_data and not pz_data:
        print(f"  警告：两个文件都无法加载，跳过")
        return False
    
    print(f"  trans文件包含 {len(trans_data)} 个条目")
    print(f"  pz文件包含 {len(pz_data)} 个条目")
    
    # 执行迁移
    result_data, migrated_count = migrate_translations(trans_data, pz_data)
    
    print(f"  成功迁移了 {migrated_count} 个翻译条目")
    
    # 保存结果
    if save_json_file(result_data, output_file):
        print(f"  ✓ 成功保存到: {output_file}")
        print(f"  结果文件包含 {len(result_data)} 个条目")
        return True
    else:
        print(f"  ✗ 保存失败")
        return False

def main():
    """主函数"""
    # 目录路径
    trans_dir = "trans/0.6.6e/Widgets"
    pz_dir = "pz_origin/0.7.0b/Widgets"
    output_dir = "pz_origin/0.7.0b+/Widgets"
    
    print("开始批量数据迁移...")
    print(f"源翻译目录: {trans_dir}")
    print(f"目标原始目录: {pz_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 70)
    
    # 获取trans目录中的所有JSON文件
    trans_files = get_json_files(trans_dir)
    
    if not trans_files:
        print("错误：在trans目录中没有找到JSON文件")
        return
    
    print(f"找到 {len(trans_files)} 个翻译文件")
    
    # 统计变量
    total_files = 0
    successful_files = 0
    total_migrated = 0
    
    # 处理每个文件
    for trans_file in trans_files:
        filename = os.path.basename(trans_file)
        pz_file = os.path.join(pz_dir, filename)
        output_file = os.path.join(output_dir, filename)
        
        total_files += 1
        
        if process_single_file(trans_file, pz_file, output_file):
            successful_files += 1
    
    # 打印总结
    print("\n" + "=" * 70)
    print("迁移完成！")
    print(f"总文件数: {total_files}")
    print(f"成功处理: {successful_files}")
    print(f"失败: {total_files - successful_files}")
    
    if successful_files > 0:
        print(f"\n所有结果已保存到: {output_dir}")
        
        # 列出输出目录中的文件
        output_files = get_json_files(output_dir)
        print(f"输出目录包含 {len(output_files)} 个文件:")
        for output_file in sorted(output_files):
            print(f"  - {os.path.basename(output_file)}")

if __name__ == "__main__":
    main()