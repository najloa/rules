#!/usr/bin/env python3
import argparse
import os
import re
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Process include files into flat lists.")

    # 支持 -i1/-o1, -i2/-o2 ...
    for idx in range(1, 10):
        parser.add_argument(f"-i{idx}", help=f"Input file {idx}")
        parser.add_argument(f"-o{idx}", help=f"Output file {idx}")
    parser.add_argument("-i", help="Single input file")
    parser.add_argument("-o", help="Single output file")

    parser.add_argument("--remove-cn", action="store_true",
                        help="Remove lines containing @cn")
    parser.add_argument("--keep-include", type=str, default="",
                        help="Comma separated list of include files to preserve @cn lines")
    parser.add_argument("--cntocn", action="store_true",
                        help="If set, move all @cn lines into -i2/-o2 (or fallback to cn.txt)")
    return parser.parse_args()


def clean_line(line: str) -> str:
    """移除注释 (# 及其后)，去掉空白。"""
    line = re.split(r"\s+#", line, 1)[0]
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    return line


def process_file(path, base_dir, seen, remove_cn, keep_includes, cn_lines, cntocn):
    """递归处理文件，返回普通行，@cn 行根据选项加入 cn_lines。"""
    if path in seen:
        return []
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
                                           remove_cn, keep_includes, cn_lines, cntocn))
            else:
                if remove_cn and "@cn" in line:
                    keep = False
                    for inc in keep_includes:
                        if path == inc or path.endswith("/" + inc):
                            keep = True
                            break
                    if keep:
                        result.append(line)
                    else:
                        if cntocn:
                            cn_lines.append(line)  # 收集到全局 cn_lines
                        # 否则直接丢弃
                else:
                    result.append(line)
    return result


def main():
    args = parse_args()
    keep_includes = [x.strip() for x in args.keep_include.split(",") if x.strip()]

    # 收集输入输出映射
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
    all_results = {}
    cn_lines_global = [] if args.cntocn else None
    seen = set()

    for infile, outfile in mappings:
        cn_lines = cn_lines_global if args.cntocn else []
        lines = process_file(os.path.basename(infile), base_dir, seen,
                             args.remove_cn, keep_includes, cn_lines, args.cntocn)
        all_results[outfile] = lines
        # 如果不是 --cntocn，则每个文件单独写 cn_lines
        if not args.cntocn and cn_lines:
            cn_out = outfile.replace(".txt", "-cn.txt")
            all_results[cn_out] = cn_lines

    # 写入结果
    for outfile, lines in all_results.items():
        with open(outfile, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    # 如果 --cntocn，集中写入到 -i2/-o2 或 cn.txt
    if args.cntocn and cn_lines_global:
        if len(mappings) >= 2:
            _, outfile2 = mappings[1]
            cn_target = outfile2
        else:
            cn_target = os.path.join(base_dir, "cn.txt")
            print(f"Info: --cntocn enabled, writing @cn lines into {cn_target}", file=sys.stderr)

        with open(cn_target, "a", encoding="utf-8") as f:
            f.write("\n".join(cn_lines_global) + "\n")

    # 删除多余文件
    keep_files = set()
    for infile, outfile in mappings:
        keep_files.add(os.path.basename(infile))
        keep_files.add(os.path.basename(outfile))
    keep_files.update(seen)
    if args.cntocn:
        keep_files.add("cn.txt")

    for fname in os.listdir(base_dir):
        if fname not in keep_files:
            try:
                os.remove(os.path.join(base_dir, fname))
            except Exception as e:
                print(f"Warning: cannot delete {fname}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
