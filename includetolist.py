#!/usr/bin/env python3
import argparse
import os
import re
import sys

def clean_line(line: str) -> str:
    """清理注释并返回内容。"""
    line = re.split(r"\s+#", line, 1)[0]
    line = line.strip()
    return line if (line and not line.startswith("#")) else ""

def get_filename_from_include(line: str) -> str:
    """
    解析 include 行，提取真实的文件名。
    例如: 'include:deepin @-!cn' -> 'deepin'
    """
    content = line.split("include:", 1)[1].strip()
    file_part = content.split("@")[0].strip()
    return file_part

def process_file(file_name, base_dir, involved_files):
    """递归处理并精准记录依赖文件。"""
    full_path = os.path.join(base_dir, file_name)
    
    if not os.path.exists(full_path):
        print(f"Warning: File NOT found: {full_path}", file=sys.stderr)
        return set()
    
    involved_files.add(file_name)
    
    results = set()
    with open(full_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = clean_line(raw)
            if not line:
                continue
            
            if line.startswith("include:"):
                target_file = get_filename_from_include(line)
                results.update(process_file(target_file, base_dir, involved_files))
            else:
                results.add(line)
    return results

def main():
    parser = argparse.ArgumentParser(description="Process community data with exact include parsing.")
    parser.add_argument("-i", "--input", required=True, help="Input directory")
    parser.add_argument("-o", "--output", help="Output directory")
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input)
    output_dir = os.path.abspath(args.output) if args.output else input_dir

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tasks = [("cn", "cn.txt"), ("geolocation-!cn", "proxy.txt")]
    involved_files = set()
    
    # 新增：用于收集所有任务中带有 @cn 的域名行（使用集合自动去重）
    all_cn_tagged_lines = set()

    for seed_name, output_name in tasks:
        if os.path.exists(os.path.join(input_dir, seed_name)):
            print(f"-> Processing {seed_name}...")
            content = process_file(seed_name, input_dir, involved_files)
            
            # 【修改点 1】：从当前处理的内容中，筛选出包含 @cn 的行，加入到全局集合中
            # 使用更严谨的正则或 split 确保是独立的修饰符，这里采用包含检测：' @cn' 或以 '@cn' 结尾
            for line in content:
                if '@cn' in line:
                    all_cn_tagged_lines.add(line)
            
            with open(os.path.join(output_dir, output_name), "w", encoding="utf-8") as f:
                if content:
                    f.write("\n".join(sorted(list(content))) + "\n")

    # 【修改点 2】：将收集到的 @cn 域名行写入到独立的 @cn.txt 文件中
    cn_file_name = "@cn.txt"
    with open(os.path.join(output_dir, cn_file_name), "w", encoding="utf-8") as f:
        if all_cn_tagged_lines:
            f.write("\n".join(sorted(list(all_cn_tagged_lines))) + "\n")
            print(f"-> Extracted {len(all_cn_tagged_lines)} lines with @cn to {cn_file_name}")

    # 执行清理
    print(f"Cleaning directory: {input_dir}")
    must_keep = involved_files.copy()
    
    # 【修改点 3】：如果输入和输出是同一个目录，把新的 @cn.txt 也加入白名单保护起来
    if input_dir == output_dir:
        must_keep.update({"private", "cn.txt", "proxy.txt", cn_file_name})

    for fname in os.listdir(input_dir):
        fpath = os.path.join(input_dir, fname)
        if os.path.isfile(fpath):
            if fname not in must_keep:
                try:
                    os.remove(fpath)
                    print(f"Removed: {fname}")
                except Exception as e:
                    print(f"Error deleting {fname}: {e}")
            else:
                print(f"Keep: {fname}")

if __name__ == "__main__":
    main()
