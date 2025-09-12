#!/usr/bin/env python3
import os
import sys

def expand_file(infile, fout, visited=None):
    """
    递归展开 include: 指令
    - 忽略 # 后面的注释
    - 防止循环 include
    """
    if visited is None:
        visited = set()
    if infile in visited:
        raise ValueError(f"循环 include 检测到: {infile}")
    visited.add(infile)

    with open(infile, "r", encoding="utf-8") as fin:
        for line in fin:
            stripped = line.strip()
            if stripped.startswith("include:"):
                # 去掉注释部分
                content = stripped.split("#", 1)[0].strip()
                fname = content.split(":", 1)[1].strip()
                if not os.path.isfile(fname):
                    raise FileNotFoundError(f"被 include 的文件不存在: {fname}")
                expand_file(fname, fout, visited)
            else:
                fout.write(line)

def main():
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} 输入文件 输出文件")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(output_file, "w", encoding="utf-8") as fout:
        expand_file(input_file, fout)

if __name__ == "__main__":
    main()
