#!/usr/bin/env python3
"""
数据集格式化脚本
将TraningData_8_17目录中的文本文件从空格分隔格式转换为制表符分隔格式
"""

import os
import glob

def format_file(input_file_path, output_file_path):
    """
    格式化单个文件：将空格分隔符改为制表符分隔符
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()
        
        formatted_lines = []
        for line in lines:
            # 去除行尾换行符，分割数值，然后用制表符重新连接
            values = line.strip().split()
            if len(values) == 6:  # 确保每行有6个数值
                formatted_line = '\t'.join(values) + '\n'
                formatted_lines.append(formatted_line)
            else:
                # 如果行格式不正确，保留原样并记录警告
                print(f"警告: 文件 {input_file_path} 中有一行包含 {len(values)} 个数值，期望6个")
                formatted_lines.append(line)
        
        # 写入格式化后的内容
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.writelines(formatted_lines)
        
        print(f"✓ 已格式化: {input_file_path} -> {output_file_path}")
        return True
        
    except Exception as e:
        print(f"✗ 格式化文件 {input_file_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    # 定义目录路径
    base_dir = r"f:\CyberWand\CyberWand_Insta360\Software"
    source_dir = os.path.join(base_dir, "TraningData_7_23")
    backup_dir = os.path.join(base_dir, "TraningData_7_23_backup")
    
    # 检查源目录是否存在
    if not os.path.exists(source_dir):
        print(f"错误: 源目录不存在: {source_dir}")
        return
    
    # 创建备份目录
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"创建备份目录: {backup_dir}")
    
    # 查找所有txt文件
    txt_files = glob.glob(os.path.join(source_dir, "*.txt"))
    
    if not txt_files:
        print("未找到任何txt文件")
        return
    
    print(f"找到 {len(txt_files)} 个txt文件")
    print("开始格式化...")
    
    success_count = 0
    error_count = 0
    
    for txt_file in txt_files:
        filename = os.path.basename(txt_file)
        
        # 备份原文件
        backup_file = os.path.join(backup_dir, filename)
        try:
            import shutil
            shutil.copy2(txt_file, backup_file)
        except Exception as e:
            print(f"警告: 无法备份文件 {txt_file}: {e}")
        
        # 格式化文件（原地修改）
        if format_file(txt_file, txt_file):
            success_count += 1
        else:
            error_count += 1
    
    print("\n格式化完成!")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {error_count} 个文件")
    print(f"备份文件保存在: {backup_dir}")
    print("\n格式说明:")
    print("- 原格式: 空格分隔的6个数值")
    print("- 新格式: 制表符分隔的6个数值")
    print("- 与TraningData_2_9目录格式保持一致")

if __name__ == "__main__":
    main()