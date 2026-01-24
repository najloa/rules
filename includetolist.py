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
    """递归处理文件并去重。"""
    full_path = os.path.join(base_dir, file_name)
    if not os.path.exists(full_path):
        print(f"Warning: file not found {full_path}", file=sys.stderr)
        return set()
    
    seen_files.add(file_name)
    
    results = set()
    with open(full_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = clean_line(raw)
            if not line:
                continue
            
            if line.startswith("include:"):
                target = line.split("include:", 1)[1].strip()
                results.update(process_file(target, base_dir, seen_files))
            else:
                results.add(line)
    return results

def main():
    parser = argparse.ArgumentParser(description="Process community data with custom output path.")
    parser.add_argument("-i", "--input", required=True, help="Working directory containing source files")
    parser.add_argument("-o", "--output", help="Output directory for cn.txt and proxy.txt (defaults to input dir)")
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input)
    # 如果没指定 -o，则输出到 -i 目录
    output_dir = os.path.abspath(args.output) if args.output else input_dir

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory {input_dir} does not exist")
        sys.exit(1)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. 定义任务
    tasks = [
        ("geolocation-cn", "cn.txt"),
        ("geolocation-!cn", "proxy.txt")
    ]
    
    involved_files = set()  # 记录所有被引用的原始碎片文件名
    keep_in_output = {"cn.txt", "proxy.txt"} # 记录输出目录中需要保护的文件

    # 2. 递归处理
    for seed_name, output_name in tasks:
        seed_path = os.path.join(input_dir, seed_name)
        if not os.path.exists(seed_path):
            print(f"Error: Seed file {seed_name} not found in {input_dir}")
            continue

        print(f"Processing {seed_name}...")
        final_content = process_file(seed_name, input_dir, involved_files)
        
        output_path = os.path.join(output_dir, output_name)
        with open(output_path, "w", encoding="utf-8") as f:
            if final_content:
                f.write("\n".join(sorted(list(final_content))) + "\n")
        print(f"Generated: {output_path}")

    # 3. 清理输入目录
    # 逻辑：只保留 involved_files 里的文件。
    # 特殊情况：如果输入和输出是同一个目录，还要额外保留生成的 txt。
    print(f"Cleaning up input directory: {input_dir}...")
    
    # 确定在输入目录下绝对不能删的文件名
    must_keep = involved_files.copy()
    if input_dir == output_dir:
        must_keep.update(keep_in_output)

    for fname in os.listdir(input_dir):
        fpath = os.path.join(input_dir, fname)
        if os.path.isfile(fpath):
            if fname not in must_keep:
                try:
                    os.remove(fpath)
                    print(f"Removed: {fname}")
                except Exception as e:
                    print(f"Failed to delete {fname}: {e}")

    print("Success.")

if __name__ == "__main__":
    main()
