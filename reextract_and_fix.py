#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新提取最新版游戏并修正fetch位置信息的流程脚本

功能：
1. 自动确定最新版本号
2. 对最新版游戏进行重新提取
3. 对比提取结果，修正原先fetch的位置信息
4. 生成详细的对比报告
"""

import os
import json
import shutil
import difflib
from pathlib import Path
from datetime import datetime
from src.fetch import Fetcher
from src.consts import DIR_FETCH, DIR_SOURCE, DIR_MARGE_SOURCE
from src.log import logger
import ujson

class ReExtractAndFix:
    """重新提取和修正类"""
    
    def __init__(self):
        self.latest_version = self.get_latest_version()
        self.backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_path = Path(f"reextract_report_{self.backup_suffix}.json")
        self.changes_summary = {
            'version': self.latest_version,
            'timestamp': datetime.now().isoformat(),
            'backup_suffix': self.backup_suffix,
            'files_processed': 0,
            'position_changes': 0,
            'new_entries': 0,
            'removed_entries': 0,
            'detailed_changes': {}
        }
        
    def get_latest_version(self):
        """获取fetch文件夹中的最新版本号"""
        fetch_versions = []
        for item in DIR_FETCH.iterdir():
            if item.is_dir() and item.name.startswith('0.'):
                fetch_versions.append(item.name)
        
        # 按版本号排序，获取最新版本
        fetch_versions.sort(key=lambda x: [int(i) for i in x.replace('a','').replace('b','').replace('c','').replace('d','').replace('e','').replace('f','').split('.')])
        latest = fetch_versions[-1] if fetch_versions else None
        
        if not latest:
            raise ValueError("未找到fetch文件夹中的版本信息")
            
        logger.info(f"检测到最新版本: {latest}")
        return latest
    
    def backup_original_fetch(self):
        """备份原始fetch数据"""
        original_path = DIR_FETCH / self.latest_version
        backup_path = DIR_FETCH / f"{self.latest_version}_backup_{self.backup_suffix}"
        
        if original_path.exists():
            logger.info(f"备份原始fetch数据: {original_path} -> {backup_path}")
            shutil.copytree(original_path, backup_path)
            return backup_path
        else:
            logger.warning(f"原始fetch路径不存在: {original_path}")
            return None
    
    def ensure_marge_source_exists(self):
        """确保marge_source存在，如果不存在则创建"""
        marge_path = DIR_MARGE_SOURCE / self.latest_version
        if not marge_path.exists():
            logger.info(f"创建marge_source: {marge_path}")
            fetcher = Fetcher(self.latest_version)
            fetcher.marge_source()
        else:
            logger.info(f"marge_source已存在: {marge_path}")
        return marge_path
    
    def extract_fresh_data(self):
        """重新提取最新版本数据"""
        logger.info(f"开始重新提取版本 {self.latest_version} 的数据...")
        
        # 确保marge_source存在
        self.ensure_marge_source_exists()
        
        # 创建新的Fetcher实例并执行提取
        fetcher = Fetcher(self.latest_version)
        
        # 重新提取源数据
        fetcher.fetch_source()
        logger.info("fetch_source 完成")
        return fetcher
    
    def compare_fetch_data(self, backup_path):
        """对比新旧fetch数据，生成详细的变化报告"""
        logger.info("开始对比fetch数据变化...")
        
        current_path = DIR_FETCH / self.latest_version
        
        if not backup_path or not backup_path.exists():
            logger.warning("没有备份数据可供对比")
            return
        
        # 遍历所有json文件进行对比
        for root, dirs, files in os.walk(current_path):
            for file in files:
                if not file.endswith('.json') or file == 'hash_dict.json':
                    continue
                    
                current_file = Path(root) / file
                relative_path = current_file.relative_to(current_path)
                backup_file = backup_path / relative_path
                
                if backup_file.exists():
                    self.compare_single_file(current_file, backup_file, str(relative_path))
                else:
                    logger.info(f"新增文件: {relative_path}")
                    self.changes_summary['new_entries'] += 1
                    
                self.changes_summary['files_processed'] += 1
    
    def compare_single_file(self, current_file, backup_file, relative_path):
        """
        安全地对比文件并仅更新位置。
        ID严格保持不变。
        """
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                current_data_by_id = json.load(f)
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data_by_id = json.load(f)

            # 创建新数据的哈希索引以便快速查找
            # {hash: item}
            current_data_by_hash = {item['hash']: item for item in current_data_by_id.values() if 'hash' in item}

            updated_data = {}
            file_changes = {
                'position_updated': [],
                'unmatched_or_text_changed': [],
                'newly_found_text': []
            }
            
            processed_new_hashes = set()

            # 遍历备份数据，这是ID的唯一来源
            for key, backup_item in backup_data_by_id.items():
                backup_hash = backup_item.get('hash')
                
                # 检查stage，如果是9（过时），则直接保留
                if backup_item.get('stage') == 9:
                    updated_data[key] = backup_item
                    continue

                if backup_hash and backup_hash in current_data_by_hash:
                    # 找到了匹配的哈希，说明文本未变
                    new_item = current_data_by_hash[backup_hash]
                    updated_item = backup_item.copy() # 继承旧条目的所有信息

                    # 仅更新位置信息
                    if updated_item.get('position') != new_item.get('position'):
                        file_changes['position_updated'].append({
                            'key': key,
                            'old_position': updated_item.get('position'),
                            'new_position': new_item.get('position')
                        })
                        self.changes_summary['position_changes'] += 1
                        updated_item['position'] = new_item.get('position')
                    
                    updated_data[key] = updated_item
                    processed_new_hashes.add(backup_hash)
                else:
                    # 在新数据中找不到匹配的哈希，保留旧条目并标记
                    file_changes['unmatched_or_text_changed'].append(key)
                    updated_data[key] = backup_item
                    # 可以在这里添加一个状态标记，如果需要的话
                    # updated_data[key]['status'] = 'unmatched'

            # 识别在新提取数据中但未被处理的条目（即新增文本）
            for new_hash, new_item in current_data_by_hash.items():
                if new_hash not in processed_new_hashes:
                    file_changes['newly_found_text'].append({
                        'id': new_item.get('id'),
                        'text': new_item.get('text', '')[:100]
                    })
                    self.changes_summary['new_entries'] += 1
            
            # 如果有变化，则写回文件并记录日志
            if any(file_changes.values()):
                self.changes_summary['detailed_changes'][relative_path] = file_changes
                logger.info(f"文件 {relative_path} 有变化: "
                           f"位置更新={len(file_changes['position_updated'])}, "
                           f"文本变更/丢失={len(file_changes['unmatched_or_text_changed'])}, "
                           f"发现新文本={len(file_changes['newly_found_text'])}")
                
                # **重要**: 将更新后的数据写回当前fetch目录
                with open(current_file, 'w', encoding='utf-8') as f:
                    json.dump(updated_data, f, ensure_ascii=False, indent=2)
            else:
                 # 即使没有变化，也要确保文件内容与备份一致（以防万一）
                if current_data_by_id != backup_data_by_id:
                    shutil.copy2(backup_file, current_file)


        except Exception as e:
            logger.error(f"对比文件 {relative_path} 时出错: {str(e)}")

    def fix_position_issues(self):
        """
        此函数现在被 compare_and_fix_data 取代。
        保留为空或移除，以避免执行不安全的操作。
        """
        logger.info("跳过旧的 fix_position_issues 流程，新的安全更新流程已在对比步骤中完成。")
        pass
    
    def generate_report(self):
        """生成详细的变化报告"""
        logger.info(f"生成变化报告: {self.report_path}")
        
        with open(self.report_path, 'w', encoding='utf-8') as f:
            json.dump(self.changes_summary, f, ensure_ascii=False, indent=2)
        
        # 打印摘要信息
        logger.info("="*60)
        logger.info(f"重新提取和修正完成 - 版本: {self.latest_version}")
        logger.info(f"处理文件数: {self.changes_summary['files_processed']}")
        logger.info(f"位置变化数: {self.changes_summary['position_changes']}")
        logger.info(f"新增条目数: {self.changes_summary['new_entries']}")
        logger.info(f"移除条目数: {self.changes_summary['removed_entries']}")
        logger.info(f"有变化的文件数: {len(self.changes_summary['detailed_changes'])}")
        logger.info(f"详细报告已保存至: {self.report_path}")
        logger.info("="*60)
    
    def run_full_process(self):
        """运行完整的重新提取和修正流程"""
        logger.info("开始运行重新提取和修正流程...")
        
        try:
            # 1. 备份原始数据
            backup_path = self.backup_original_fetch()
            
            # 2. 重新提取数据
            self.extract_fresh_data()
            
            # 3. 对比变化
            if backup_path:
                self.compare_fetch_data(backup_path)
            
            # 4. 生成报告
            self.generate_report()
            
            logger.info("重新提取和修正流程执行完成！")
            
        except Exception as e:
            logger.error(f"流程执行过程中出现错误: {str(e)}")
            raise

def main():
    """主函数"""
    re_extractor = ReExtractAndFix()
    re_extractor.run_full_process()

if __name__ == "__main__":
    main()