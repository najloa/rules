#!/usr/bin/env python3
import os
import sys
import argparse

def expand_file(infile, fout, visited=None, remove_cn=False, keep_include=None, from_include=None):
    if visited is None:
        visited = set()
    if infile in visited:
        print(f"[警告] 跳过循环 include: {infile}")
        return
    visited.add(infile)

    with open(infile, "r", encoding="utf-8") as fin:
        for line in fin:
            stripped = line.strip()

            # 判断是否删除 @cn 行
            if remove_cn and "@cn" in stripped:
                # 如果当前文件是某个 include 进来的，就保留
                if from_include in (keep_include or []):
                    pass
                else:
                    continue

            if stripped.startswith("include:"):
                content = stripped.split("#", 1)[0].strip()
                fname = content.split(":", 1)[1].strip()
                if not os.path.isfile(fname):
                    print(f"[警告] 被 include 的文件不存在: {fname}")
                    continue
                expand_file(fname, fout, visited, remove_cn, keep_include, from_include=fname)
            else:
                fout.write(line)

def main():
    parser = argparse.ArgumentParser(description="展开 include: 文件并支持过滤 @cn 行")
    parser.add_argument("input", help="输入文件")
    parser.add_argument("output", help="输出文件")
    parser.add_argument("--remove-cn", action="store_true", help="删除包含 @cn 的行")
    parser.add_argument("--keep-include", nargs="*", help="保留这些 include 文件中的 @cn 行（空格分隔）")
    args = parser.parse_args()

    with open(args.output, "w", encoding="utf-8") as fout:
        expand_file(args.input, fout,
                    remove_cn=args.remove_cn,
                    keep_include=args.keep_include)

if __name__ == "__main__":
    main()
