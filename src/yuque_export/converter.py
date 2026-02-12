# Copyright (c) yuque_export. HTML 转 Markdown 与图片本地化。

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import html2text


# 请求头：语雀 CDN 常校验 Referer/Origin，需模拟来自语雀的请求
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.yuque.com/",
    "Origin": "https://www.yuque.com",
}


def html_to_markdown(html: str) -> str:
    """
    将语雀文档 body HTML 转为 Markdown。

    使用 html2text 保留标题、列表、表格、链接等；图片仍为原始 URL，
    后续由 replace_images_with_local 替换为本地路径。
    """
    if not html or not html.strip():
        return ""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0
    h.ignore_emphasis = False
    return h.handle(html)


def extract_image_urls(html: str) -> List[str]:
    """从 HTML 中提取所有 img 的 src URL（去重、保留顺序）。"""
    soup = BeautifulSoup(html, "html.parser")
    urls: List[str] = []
    seen: set[str] = set()
    for img in soup.find_all("img", src=True):
        src = (img["src"] or "").strip()
        if src and src not in seen and (src.startswith("http://") or src.startswith("https://")):
            seen.add(src)
            urls.append(src)
    return urls


def _url_to_local_basename(url: str, index: int) -> str:
    """根据 URL 和序号生成本地文件名。"""
    path = urlparse(url).path
    name = Path(path).name or "image"
    # 若无扩展名，根据常见类型补全
    if "." not in name:
        name = f"{name}_{index}.png"
    # 非法字符替换
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    if not name.strip():
        name = f"image_{index}.png"
    return name


def download_image(url: str, dest_path: Path, timeout: int = 15) -> bool:
    """下载单张图片到 dest_path，成功返回 True。"""
    try:
        r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        r.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(r.content)
        return True
    except Exception:
        return False


def download_images_to_dir(
    urls: List[str],
    assets_dir: Path,
) -> Dict[str, str]:
    """
    将多张图片下载到 assets_dir，返回映射：原始 URL -> 相对路径（相对于 md 所在目录）。

    相对路径形式为 "assets/xxx.png"，便于在 md 中直接使用。
    """
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    url_to_rel: Dict[str, str] = {}
    for i, url in enumerate(urls):
        base = _url_to_local_basename(url, i)
        # 避免重名：同一 URL 只下一次；不同 URL 同文件名时加序号
        candidate = base
        idx = 0
        while (assets_dir / candidate).exists():
            stem = Path(base).stem
            suf = Path(base).suffix
            idx += 1
            candidate = f"{stem}_{idx}{suf}"
        local_path = assets_dir / candidate
        if download_image(url, local_path):
            url_to_rel[url] = f"assets/{candidate}"
        # 若下载失败，不加入映射，md 中保留原 URL
    return url_to_rel


def replace_images_in_markdown(md: str, url_to_local: Dict[str, str]) -> str:
    """在 Markdown 文本中将图片 URL 替换为本地相对路径。"""
    if not url_to_local:
        return md
    for url, local in url_to_local.items():
        # Markdown 图片语法 ![](url) 或 ![alt](url)，URL 可能被转义
        md = md.replace(url, local)
    return md


def convert_doc(
    html: str,
    assets_dir: Path,
    download_images: bool = True,
) -> Tuple[str, Dict[str, str]]:
    """
    单篇文档完整转换：HTML -> Markdown，图片下载到 assets_dir 并替换链接。

    Returns:
        (markdown_text, url_to_local_rel) 其中 url_to_local_rel 为 原始 URL -> 相对路径。
    """
    md = html_to_markdown(html)
    urls = extract_image_urls(html)
    url_to_rel: Dict[str, str] = {}
    if download_images and urls:
        url_to_rel = download_images_to_dir(urls, assets_dir)
        md = replace_images_in_markdown(md, url_to_rel)
    return md, url_to_rel
