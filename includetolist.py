#!/usr/bin/env python3
import argparse
import os
import re
import sys

def clean_line(line: str) -> str:
    """移除注释，去掉两端空白。"""
    line = re.split(r"\s+#", line, 1)[0]
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    return line

def process_file(file_name, base_dir, seen_files):
    """
    递归处理文件并去重。
    """
    full_path = os.path.join(base_dir, file_name)
    if not os.path.exists(full_path):
        print(f"Warning: file not found {full_path}", file=sys.stderr)
        return set()
    
    seen_files.add(file_name)
    
    results = set() # 使用集合自动去重
    with open(full_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = clean_line(raw)
            if not line:
                continue
            
            if line.startswith("include:"):
                target = line.split("include:", 1)[1].strip()
                # 递归并将结果合并到当前集合
                results.update(process_file(target, base_dir, seen_files))
            else:
                results.add(line)
    return results

def main():
    parser = argparse.ArgumentParser(description="Process community data and clean workspace.")
    parser.add_argument("-i", "--input", required=True, help="Working directory")
    args = parser.parse_args()

    work_dir = os.path.abspath(args.input)
    if not os.path.isdir(work_dir):
        print(f"Error: {work_dir} is not a directory")
        sys.exit(1)

    # 1. 核心定义
    tasks = [
        ("geolocation-cn", "cn.txt"),
        ("geolocation-!cn", "proxy.txt")
    ]
    
    # 记录所有需要保留的文件名
    keep_filenames = {"cn.txt", "proxy.txt"}
    # 记录递归中涉及到的所有原始碎片文件
    involved_files = set()

    # 2. 递归处理任务
    for seed_name, output_name in tasks:
        if not os.path.exists(os.path.join(work_dir, seed_name)):
            print(f"Error: Seed file {seed_name} not found in {work_dir}")
            continue

        print(f"Processing {seed_name}...")
        # 递归并获取去重后的内容
        final_content = process_file(seed_name, work_dir, involved_files)
        
        # 写入扁平化后的文件
        output_path = os.path.join(work_dir, output_name)
        with open(output_path, "w", encoding="utf-8") as f:
            if final_content:
                # 排序可以让输出更整洁
                f.write("\n".join(sorted(list(final_content))) + "\n")

    # 3. 确定最终保留名单
    # 保留：两个生成的 txt + 两个原始种子文件 + 递归中 include 的所有文件
    keep_filenames.update(involved_files)

    # 4. 执行删除
    print("Cleaning up directory...")
    current_files = os.listdir(work_dir)
    for fname in current_files:
        fpath = os.path.join(work_dir, fname)
        
        # 只处理文件（跳过子目录，除非你有特殊需求）
        if os.path.isfile(fpath):
            if fname not in keep_filenames:
                try:
                    os.remove(fpath)
                except Exception as e:
                    print(f"Failed to delete {fname}: {e}")
            else:
                print(f"Keep: {fname}")

    print("Process completed successfully.")

if __name__ == "__main__":
    main()
