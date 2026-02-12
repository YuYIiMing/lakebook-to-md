# Copyright (c) yuque_export. 解析 .lakebook 包与目录结构。

from __future__ import annotations

import json
import os
import re
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, List, Optional

import yaml


def _sanitize_name(name: str) -> str:
    """将标题转为安全文件名/目录名，去除非法字符。"""
    s = re.sub(r'[\\/*?:"<>|]', "_", name)
    return s.strip() or "untitled"


@dataclass
class DocNode:
    """文档节点：对应 toc 中的一篇文档。"""

    title: str
    level: int
    uuid: str
    url: str
    # 输出用的相对路径（不含扩展名），如 "folder/subfolder/doc_title"
    rel_path_stem: str = ""


@dataclass
class DirNode:
    """目录节点：对应 toc 中的目录（TITLE）。"""

    title: str
    level: int
    children: List[Any] = field(default_factory=list)  # DirNode | DocNode


class LakebookParser:
    """
    解析语雀 .lakebook 导出包。

    .lakebook 为 tar 包，解压后根目录下有一个子目录，内有：
    - $meta.json：含 meta.book.tocYml（YAML 字符串）描述目录树
    - {url}.json：每篇文档内容，doc.body 为 HTML
    """

    def __init__(
        self,
        lakebook_path: str,
        *,
        use_unique_suffix: bool = False,
    ) -> None:
        self.lakebook_path = Path(lakebook_path)
        self._use_unique_suffix = use_unique_suffix
        if not self.lakebook_path.exists():
            raise FileNotFoundError(f"lakebook 文件不存在: {lakebook_path}")
        self._extract_dir: Optional[Path] = None
        self._root_dir: Optional[Path] = None  # 解压后知识库根目录（$meta.json 所在）

    def extract(self) -> Path:
        """解压 .lakebook 到临时目录，返回知识库根目录（含 $meta.json 的目录）。"""
        with tarfile.open(self.lakebook_path, "r:*") as tf:
            tmp = tempfile.mkdtemp(prefix="lakebook_")
            tf.extractall(tmp)
        self._extract_dir = Path(tmp)
        items = list(self._extract_dir.iterdir())
        if not items:
            raise ValueError("lakebook 解压后为空")
        self._root_dir = items[0] if items[0].is_dir() else self._extract_dir
        meta_file = self._root_dir / "$meta.json"
        if not meta_file.exists():
            self.cleanup()
            raise ValueError("解压目录中未找到 $meta.json")
        return self._root_dir

    def cleanup(self) -> None:
        """删除解压得到的临时目录。"""
        if self._extract_dir and self._extract_dir.exists():
            import shutil

            shutil.rmtree(self._extract_dir, ignore_errors=True)
        self._extract_dir = None
        self._root_dir = None

    def _load_toc_yml(self) -> List[dict]:
        """从 $meta.json 读取并解析 tocYml，返回 TOC 项列表。"""
        if not self._root_dir:
            raise RuntimeError("请先调用 extract()")
        with open(self._root_dir / "$meta.json", encoding="utf-8") as f:
            meta = json.load(f)
        inner = json.loads(meta["meta"])
        toc_yml_str = inner["book"]["tocYml"]
        data = yaml.safe_load(toc_yml_str)
        if isinstance(data, list):
            return data
        return [data] if data else []

    def build_tree(self) -> List[Any]:
        """
        根据 tocYml 构建目录树（仅根层列表，子节点在 DirNode.children 中）。

        Returns:
            DirNode 与 DocNode 的列表；DOC 对应文档，TITLE 对应目录（递归为 DirNode）。
        """
        items = self._load_toc_yml()
        root: List[Any] = []
        stack: List[tuple[int, DirNode]] = []  # (level, dir_node)

        for item in items:
            kind = (item.get("type") or "").upper()
            if kind == "META":
                continue
            level = int(item.get("level") or 0)
            title = (item.get("title") or "").strip() or "untitled"

            if kind == "TITLE":
                node = DirNode(title=title, level=level)
                # 弹出层级 >= 当前 level 的
                while stack and stack[-1][0] >= level:
                    stack.pop()
                if stack:
                    stack[-1][1].children.append(node)
                else:
                    root.append(node)
                stack.append((level, node))
            elif kind == "DOC":
                doc = DocNode(
                    title=title,
                    level=level,
                    uuid=item.get("uuid") or "",
                    url=item.get("url") or "",
                )
                while stack and stack[-1][0] >= level:
                    stack.pop()
                if stack:
                    stack[-1][1].children.append(doc)
                else:
                    root.append(doc)

        return root

    def _assign_path_stems(
        self,
        nodes: List[Any],
        parent_prefix: str = "",
        used_per_prefix: Optional[dict] = None,
    ) -> None:
        """为每个 DocNode 设置 rel_path_stem；目录名用 parent_prefix 累加。"""
        if used_per_prefix is None:
            used_per_prefix = {}
        for node in nodes:
            if isinstance(node, DirNode):
                dir_name = _sanitize_name(node.title)
                prefix = f"{parent_prefix}{dir_name}/" if parent_prefix else f"{dir_name}/"
                self._assign_path_stems(node.children, prefix, used_per_prefix)
            else:
                assert isinstance(node, DocNode)
                stem = _sanitize_name(node.title)
                if self._use_unique_suffix:
                    unique = (node.uuid or node.url or "")[:8]
                    node.rel_path_stem = (
                        f"{parent_prefix}{stem}_{unique}" if unique else f"{parent_prefix}{stem}"
                    )
                else:
                    used = used_per_prefix.setdefault(parent_prefix, set())
                    base, candidate = stem, stem
                    n = 0
                    while candidate in used:
                        n += 1
                        candidate = f"{base}_{n}"
                    used.add(candidate)
                    node.rel_path_stem = f"{parent_prefix}{candidate}"

    def get_doc_html(self, url: str) -> str:
        """读取单篇文档的 body HTML。"""
        if not self._root_dir:
            raise RuntimeError("请先调用 extract()")
        path = self._root_dir / f"{url}.json"
        if not path.exists():
            return ""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("doc") or {}).get("body") or ""

    def iter_docs(self) -> Iterator[tuple[DocNode, str]]:
        """
        先 build_tree 并 _assign_path_stems，再依次 yield (DocNode, html)。
        """
        root = self.build_tree()
        self._assign_path_stems(root)
        for node, html in self._iter_docs_from_nodes(root):
            yield node, html

    def _iter_docs_from_nodes(
        self, nodes: List[Any]
    ) -> Iterator[tuple[DocNode, str]]:
        for node in nodes:
            if isinstance(node, DirNode):
                yield from self._iter_docs_from_nodes(node.children)
            else:
                assert isinstance(node, DocNode)
                html = self.get_doc_html(node.url)
                yield node, html
