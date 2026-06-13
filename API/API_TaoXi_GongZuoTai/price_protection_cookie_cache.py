# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 19:09:00
- 最近修改：2026-06-12 19:09:00
- 文件用途：为千牛价保中心提供运行期 Cookie 预热与本地缓存能力，负责按店铺缓存冷启动 Cookie、打开价保页面补齐会话并生成后续接口可复用的 cached_cookie。
- 业务范围：适用于商家工作台价保中心导出链路，不回写数据库原始 Cookie，仅在本项目 state 目录写入本地缓存。
- 依赖入口：使用标准库 datetime、hashlib、json、pathlib、urllib.parse 和 requests，对外暴露 merge_cookie_texts、load_cached_cookie、warmup_price_center_cookie 等入口。
- 验收方式：修改后执行 py_compile；使用无网样本验证 Cookie 合并、缓存读写和失效判断；真实请求时仅做单店铺价保页预热验证。
- 注意事项：缓存文件属于本地运行态敏感数据，不得提交到仓库；日志不得输出完整 Cookie、完整下载 URL 或敏感票据。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests

from extra.logger_ import logger


MODULE_DIR = Path(__file__).resolve().parent
CACHE_DIR = MODULE_DIR / "state" / "price_protection_cookie_cache"
CACHE_TTL_SECONDS = 30 * 60
BLOCKED_HOSTS = {"login.taobao.com", "error.taobao.com", "err.taobao.com"}


def _now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_url(url):
    parts = urlsplit(url or "")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _safe_text_preview(text, limit=200):
    return " ".join((text or "").split())[:limit]


def _cookie_text_to_dict(cookie_text):
    cookie_dict = {}
    for item in (cookie_text or "").split(";"):
        item = item.strip()
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key:
            cookie_dict[key] = value
    return cookie_dict


def _cookie_jar_to_text(cookie_jar):
    return "; ".join(f"{cookie.name}={cookie.value}" for cookie in cookie_jar)


def merge_cookie_texts(*cookie_texts):
    """按传入顺序合并 Cookie，后出现的同名字段覆盖前者。"""
    cookie_dict = {}
    for cookie_text in cookie_texts:
        for key, value in _cookie_text_to_dict(cookie_text).items():
            cookie_dict[key] = value
    return "; ".join(f"{key}={value}" for key, value in cookie_dict.items())


def build_source_cookie_signature(*cookie_texts):
    merged_cookie = merge_cookie_texts(*cookie_texts)
    if not merged_cookie:
        return ""
    return hashlib.md5(merged_cookie.encode("utf-8")).hexdigest()


def _build_cache_path(shop_name):
    cache_key = shop_name or "default"
    digest = hashlib.md5(cache_key.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{digest}.json"


def load_cached_cookie(shop_name, source_signature, max_age_seconds=CACHE_TTL_SECONDS):
    """读取本地 cached_cookie，源 Cookie 变更或缓存超时则返回 None。"""
    cache_path = _build_cache_path(shop_name)
    if not cache_path.exists():
        return None

    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(f"{shop_name} 价保 Cookie 缓存读取失败: {exc}")
        return None

    cached_cookie = payload.get("cookie")
    if not cached_cookie:
        return None
    if payload.get("source_signature") != source_signature:
        return None

    updated_at = payload.get("updated_at")
    if not updated_at:
        return None

    try:
        updated_datetime = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    if datetime.now() - updated_datetime > timedelta(seconds=max_age_seconds):
        return None
    return cached_cookie


def save_cached_cookie(shop_name, source_signature, cookie_text, source):
    """把价保页预热后的 cached_cookie 保存到本地 state 目录。"""
    if not cookie_text:
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _build_cache_path(shop_name)
    payload = {
        "shop_name": shop_name,
        "source": source,
        "source_signature": source_signature,
        "updated_at": _now_text(),
        "cookie": cookie_text,
    }
    cache_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_login_gate_response(response):
    final_url = (response.url or "").lower()
    host = urlsplit(response.url or "").netloc.lower()
    text = response.text or ""
    if host in BLOCKED_HOSTS:
        return True
    if "logout" in final_url:
        return True
    if "请您登陆之后再访问" in text or "请先登录" in text:
        return True
    if "<title>淘宝网 - 淘！我喜欢</title>" in text and "error.taobao.com" in final_url:
        return True
    return False


def warmup_price_center_cookie(
    shop_name,
    source_cookie,
    extra_cookie,
    price_center_url,
    user_agent,
    force_refresh=False,
    timeout=30,
):
    """用数据库 Cookie 打开价保页，生成仅用于当前任务链路的 cached_cookie。"""
    merged_source_cookie = merge_cookie_texts(source_cookie, extra_cookie)
    source_signature = build_source_cookie_signature(merged_source_cookie)

    if not force_refresh:
        cached_cookie = load_cached_cookie(shop_name, source_signature)
        if cached_cookie:
            logger.info(f"{shop_name} 命中本地价保 Cookie 缓存")
            return cached_cookie

    session = requests.Session()
    session.headers.update({"user-agent": user_agent, "referer": price_center_url})
    session.cookies.update(_cookie_text_to_dict(merged_source_cookie))

    try:
        response = session.get(
            price_center_url,
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        logger.warning(f"{shop_name} 价保页预热失败，继续使用冷启动 Cookie: {exc}")
        return merged_source_cookie

    warmed_cookie = merge_cookie_texts(
        merged_source_cookie,
        _cookie_jar_to_text(session.cookies),
    )
    if is_login_gate_response(response):
        logger.warning(
            f"{shop_name} 价保页预热未通过，url={_safe_url(response.url)}, "
            f"preview={_safe_text_preview(response.text)}"
        )
        return warmed_cookie

    save_cached_cookie(
        shop_name=shop_name,
        source_signature=source_signature,
        cookie_text=warmed_cookie,
        source="price_center_page",
    )
    logger.info(f"{shop_name} 价保页预热成功，已刷新本地 Cookie 缓存")
    return warmed_cookie
