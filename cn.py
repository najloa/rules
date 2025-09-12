#!/usr/bin/env python3
import os

def expand_file(infile, fout, visited=None):
    """
    递归展开 include: 指令
    infile: 输入文件名
    fout: 已经打开的输出文件对象
    visited: 防止循环 include
    """
    if visited is None:
        visited = set()
    if infile in visited:
        raise ValueError(f"循环 include 检测到: {infile}")
    visited.add(infile)

    with open(infile, "r") as fin:
        for line in fin:
            stripped = line.strip()
            if stripped.startswith("include:"):
                fname = stripped.split(":", 1)[1].strip()
                if not os.path.isfile(fname):
                    raise FileNotFoundError(f"被 include 的文件不存在: {fname}")
                expand_file(fname, fout, visited)
            else:
                fout.write(line)

def main():
    input_file = "cn"   # 输入文件
    output_file = "cnlist.txt"  # 输出文件
    with open(output_file, "w") as fout:
        expand_file(input_file, fout)

if __name__ == "__main__":
    main()
