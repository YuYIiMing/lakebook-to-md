# Copyright (c) yuque_export. 按层级写出 Markdown 文件与资源目录。

from __future__ import annotations

from pathlib import Path

from .converter import convert_doc
from .parser import DocNode, LakebookParser


def ensure_title_in_md(md: str, title: str) -> str:
    """若 md 不以 # 开头，则在开头插入一级标题。"""
    md = md.strip()
    if not md:
        return f"# {title}\n"
    if not md.startswith("#"):
        return f"# {title}\n\n{md}"
    return md


def write_doc(
    node: DocNode,
    html: str,
    output_root: Path,
    download_images: bool = True,
    obsidian_frontmatter: bool = True,
) -> Path:
    """
    将单篇文档转换为 Markdown 并写入到 output_root / node.rel_path_stem.md；
    图片保存到同目录下 assets/。

    Returns:
        写入的 md 文件路径。
    """
    output_root = Path(output_root)
    stem = node.rel_path_stem
    md_path = output_root / f"{stem}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = md_path.parent / "assets"

    md, _ = convert_doc(html, assets_dir, download_images=download_images)
    md = ensure_title_in_md(md, node.title)

    if obsidian_frontmatter:
        front = "---\ntitle: {}\n---\n\n".format(
            node.title.replace("|", "\\|").replace("\n", " ")
        )
        md = front + md

    md_path.write_text(md, encoding="utf-8")
    return md_path


def run_convert(
    lakebook_path: str,
    output_dir: str,
    *,
    download_images: bool = True,
    obsidian_frontmatter: bool = True,
    use_unique_suffix: bool = False,
) -> list[Path]:
    """
    主流程：解压 lakebook -> 解析目录 -> 逐篇转 md 并写文件。

    Args:
        use_unique_suffix: 若 True，文件名加 uuid 后缀（如 _aefApMTk）；若 False，仅用标题，同名用 _2、_3 区分。

    Returns:
        所有写入的 .md 文件路径列表。
    """
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    parser = LakebookParser(lakebook_path, use_unique_suffix=use_unique_suffix)
    written: list[Path] = []
    try:
        parser.extract()
        for node, html in parser.iter_docs():
            path = write_doc(
                node,
                html,
                output_root,
                download_images=download_images,
                obsidian_frontmatter=obsidian_frontmatter,
            )
            written.append(path)
    finally:
        parser.cleanup()

    return written
