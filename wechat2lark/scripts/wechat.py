"""Fetch a WeChat MP article and parse out title, author, date, and content tree."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class WeChatFetchError(RuntimeError):
    pass


@dataclass
class Article:
    url: str
    title: str
    author: str
    publish_date: Optional[datetime]
    content: Tag
    images: dict[str, Path] = field(default_factory=dict)


def fetch_article(url: str, image_dir: Path) -> Article:
    if "mp.weixin.qq.com" not in urlparse(url).netloc:
        raise WeChatFetchError(f"Not a WeChat MP url: {url}")

    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Referer": "https://mp.weixin.qq.com/"})
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    if "环境异常" in resp.text or "访问过于频繁" in resp.text:
        raise WeChatFetchError(
            "WeChat returned an anti-abuse page. Wait a few minutes and retry, "
            "or switch network."
        )

    soup = BeautifulSoup(resp.text, "html.parser")
    title = _extract_title(soup)
    author = _extract_author(soup)
    publish_date = _extract_date(soup)
    content = soup.select_one("#js_content")
    if content is None:
        raise WeChatFetchError(
            "Could not find #js_content. The article may require login."
        )

    image_dir.mkdir(parents=True, exist_ok=True)
    images = _download_images(content, session, image_dir)

    return Article(
        url=url,
        title=title,
        author=author,
        publish_date=publish_date,
        content=content,
        images=images,
    )


def _extract_title(soup: BeautifulSoup) -> str:
    node = soup.select_one("#activity-name")
    if node and node.get_text(strip=True):
        return node.get_text(strip=True)
    meta = soup.select_one('meta[property="og:title"]')
    if meta and meta.get("content"):
        return meta["content"].strip()
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return "untitled"


def _extract_author(soup: BeautifulSoup) -> str:
    for selector in ("#js_name", ".rich_media_meta_nickname", 'meta[name="author"]'):
        node = soup.select_one(selector)
        if node is None:
            continue
        text = node.get("content") if node.name == "meta" else node.get_text(strip=True)
        if text:
            return text.strip()
    return ""


def _extract_date(soup: BeautifulSoup) -> Optional[datetime]:
    node = soup.select_one("#publish_time")
    if node and node.get_text(strip=True):
        return _parse_date(node.get_text(strip=True))
    match = re.search(r"var\s+ct\s*=\s*\"(\d+)\"", soup.decode())
    if match:
        try:
            return datetime.fromtimestamp(int(match.group(1)))
        except (ValueError, OSError):
            pass
    match = re.search(r"publish_time\s*=\s*\"([\d\-:\s]+)\"", soup.decode())
    if match:
        return _parse_date(match.group(1))
    return None


def _parse_date(text: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return None


def _download_images(content: Tag, session: requests.Session, image_dir: Path) -> dict[str, Path]:
    """Download images referenced in content into image_dir. Mutates <img> tags to point to local files."""
    images: dict[str, Path] = {}
    for img in content.find_all("img"):
        src = img.get("data-src") or img.get("src")
        if not src or src.startswith("data:"):
            continue
        if src in images:
            local = images[src]
        else:
            local = _download_one(src, session, image_dir)
            if local is None:
                continue
            images[src] = local
        img["data-local"] = str(local)
    return images


def _download_one(src: str, session: requests.Session, image_dir: Path) -> Optional[Path]:
    try:
        r = session.get(src, timeout=30)
        r.raise_for_status()
    except requests.RequestException:
        return None
    content = r.content
    if not content:
        return None
    ext = _guess_ext(src, r.headers.get("Content-Type", ""))
    name = hashlib.md5(src.encode()).hexdigest()[:16] + ext
    path = image_dir / name
    path.write_bytes(content)
    return path


def _guess_ext(src: str, content_type: str) -> str:
    ct = content_type.lower()
    if "jpeg" in ct or "jpg" in ct:
        return ".jpg"
    if "png" in ct:
        return ".png"
    if "gif" in ct:
        return ".gif"
    if "webp" in ct:
        return ".webp"
    match = re.search(r"wx_fmt=(\w+)", src)
    if match:
        return "." + match.group(1).lower()
    return ".jpg"
