# Copyright (c) yuque_export. 命令行入口。

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .writer import run_convert


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将语雀导出的 .lakebook 知识库转换为 Obsidian 可用的 Markdown（保留层级，图片本地化）"
    )
    parser.add_argument(
        "--lakebook",
        "-l",
        type=str,
        required=True,
        help=".lakebook 文件路径",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="输出目录（将在此目录下按层级生成 .md 与 assets/）",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="不下载图片，仅保留图片原始 URL",
    )
    parser.add_argument(
        "--no-frontmatter",
        action="store_true",
        help="不写入 Obsidian 风格 YAML frontmatter（title）",
    )
    parser.add_argument(
        "--unique-suffix",
        action="store_true",
        help="在文件名后加 8 位 uuid 后缀（默认不加，同名文档用 _2、_3 区分）",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args()

    lakebook = Path(args.lakebook)
    if not lakebook.exists():
        print(f"错误：文件不存在 {lakebook}", file=sys.stderr)
        return 1

    try:
        written = run_convert(
            str(lakebook),
            args.output,
            download_images=not args.no_images,
            obsidian_frontmatter=not args.no_frontmatter,
            use_unique_suffix=args.unique_suffix,
        )
        print(f"已转换 {len(written)} 篇文档 -> {args.output}")
        for p in written[:20]:
            print(f"  - {p.relative_to(args.output)}")
        if len(written) > 20:
            print(f"  ... 等共 {len(written)} 个文件")
        return 0
    except Exception as e:
        print(f"转换失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
