#!/usr/bin/env python3
import argparse
import os
import re
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Process include files into flat lists.")

    # 动态支持 -i1/-o1, -i2/-o2 ... 或 -i/-o
    for idx in range(1, 10):
        parser.add_argument(f"-i{idx}", help=f"Input file {idx}")
        parser.add_argument(f"-o{idx}", help=f"Output file {idx}")
    parser.add_argument("-i", help="Single input file")
    parser.add_argument("-o", help="Single output file")

    parser.add_argument("--remove-cn", action="store_true",
                        help="Remove lines containing @cn")
    parser.add_argument("--keep-include", type=str, default="",
                        help="Comma separated list of include files to preserve @cn lines")
    return parser.parse_args()


def clean_line(line: str) -> str:
    """移除注释 (# 及其后)，去掉空白。"""
    line = re.split(r"\s+#", line, 1)[0]  # 去掉 inline 注释
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    return line


def process_file(path, base_dir, seen, remove_cn, keep_includes):
    """递归处理文件，返回行列表。"""
    if path in seen:
        return []  # 避免循环
    seen.add(path)

    result = []
    full_path = os.path.join(base_dir, path)
    if not os.path.exists(full_path):
        print(f"Warning: file not found {full_path}", file=sys.stderr)
        return []

    with open(full_path, encoding="utf-8") as f:
        for raw in f:
            line = clean_line(raw)
            if not line:
                continue

            if line.startswith("include:"):
                include_target = line.split("include:", 1)[1].strip()
                result.extend(process_file(include_target, base_dir, seen,
                                           remove_cn, keep_includes))
            else:
                if remove_cn and "@cn" in line:
                    # 检查是否属于保留的 include
                    # 只有在 keep_includes 白名单里才保留
                    keep = False
                    for inc in keep_includes:
                        if path == inc or path.endswith("/" + inc):
                            keep = True
                            break
                    if not keep:
                        continue
                result.append(line)
    return result


def main():
    args = parse_args()
    keep_includes = [x.strip() for x in args.keep_include.split(",") if x.strip()]

    # 处理输入输出映射
    mappings = []
    if args.i and args.o:
        mappings.append((args.i, args.o))
    for idx in range(1, 10):
        i_val = getattr(args, f"i{idx}")
        o_val = getattr(args, f"o{idx}")
        if i_val and o_val:
            mappings.append((i_val, o_val))

    if not mappings:
        print("No input/output specified", file=sys.stderr)
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(mappings[0][0]))

    # 处理每个输入输出文件
    all_results = {}
    seen = set()
    for infile, outfile in mappings:
        lines = process_file(os.path.basename(infile), base_dir, seen,
                             args.remove_cn, keep_includes)
        all_results[outfile] = lines

    # 写入结果
    for outfile, lines in all_results.items():
        with open(outfile, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    # 删除多余文件（输入目录下的非输入/输出/递归文件）
    keep_files = set()
    for infile, outfile in mappings:
        keep_files.add(os.path.basename(infile))
        keep_files.add(os.path.basename(outfile))
    keep_files.update(seen)  # 保留递归读取过的文件

    for fname in os.listdir(base_dir):
        if fname not in keep_files:
            try:
                os.remove(os.path.join(base_dir, fname))
            except Exception as e:
                print(f"Warning: cannot delete {fname}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
