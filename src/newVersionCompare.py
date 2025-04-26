import os
import filecmp
import difflib

from .consts import *
from .log import logger

def compare_directories(dir1, dir2):
    """
    比较两个目录下的所有子文件夹和文件
    """
    # 使用filecmp.dircmp比较目录
    comparison = filecmp.dircmp(dir1, dir2)
    
    # 打印不同的文件
    print("不同的文件:")
    for name in comparison.diff_files:
        print(f"- {name}")
        compare_files(os.path.join(dir1, name), os.path.join(dir2, name))
    
    # 递归比较子目录
    for subdir in comparison.common_dirs:
        compare_directories(os.path.join(dir1, subdir), os.path.join(dir2, subdir))

def compare_files(file1, file2):
    """
    比较两个文件，逐行对比并输出差异
    """
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()
    
    # 使用difflib比较行
    differ = difflib.Differ()
    diff = list(differ.compare(lines1, lines2))
    
    print(f"文件 '{file1}' 和 '{file2}' 的差异:")
    for line in diff:
        if line.startswith('  '):  # 相同的行
            continue
        elif line.startswith('- '):  # 在file1中但不在file2中的行
            print(f"- {line[2:].strip()}")
        elif line.startswith('+ '):  # 在file2中但不在file1中的行
            print(f"+ {line[2:].strip()}")

# 使用示例
dir1 = DIR_SOURCE/VERSION
dir2 = DIR_SOURCE/VERSION2
compare_directories(dir1, dir2)
