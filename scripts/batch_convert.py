#!/usr/bin/env python3
"""
将 yuque 目录下所有 .lakebook 文件转换为 Markdown，输出到 out 目录。
每个 .lakebook 对应 out/<知识库名>/ 子目录。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from yuque_export.writer import run_convert


def main() -> int:
    yuque_dir = ROOT / "yuque"
    out_dir = ROOT / "out"

    if not yuque_dir.exists():
        print(f"目录不存在: {yuque_dir}")
        return 1

    lakebooks = list(yuque_dir.rglob("*.lakebook"))
    if not lakebooks:
        print(f"在 {yuque_dir} 下未找到任何 .lakebook 文件，请将知识库导出文件放入该目录后重试。")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)

    for i, path in enumerate(lakebooks, 1):
        # 用文件名（去掉 .lakebook）作为输出子目录名
        name = path.stem
        target = out_dir / name
        print(f"[{i}/{len(lakebooks)}] 转换: {path.name} -> {target}")
        try:
            written = run_convert(
                str(path),
                str(target),
                download_images=True,
                obsidian_frontmatter=True,
            )
            print(f"  已写入 {len(written)} 篇文档")
        except Exception as e:
            print(f"  失败: {e}", file=sys.stderr)
            return 1

    print(f"\n全部完成，输出目录: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
