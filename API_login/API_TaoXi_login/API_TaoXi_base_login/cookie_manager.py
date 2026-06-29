"""Cookie 管理：加载、验证、刷新、数据库读写、格式转换。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from . import havana
from extra.logger_ import logger


def save_cookies_json(cookies: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON cookies 已保存 -> {path}")


def save_cookies_netscape(cookies: dict, domain: str, path: Path) -> None:
    lines = ["# Netscape HTTP Cookie File\n"]
    ts = int(time.time()) + 86400 * 30
    for name, value in cookies.items():
        lines.append(f".{domain}\tTRUE\t/\tFALSE\t{ts}\t{name}\t{value}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    logger.info(f"Netscape cookies 已保存 -> {path}")


def load_cookies_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and len(data) > 0:
            return data
    except (json.JSONDecodeError, IOError):
        pass
    return None


def cookie_header_to_dict(cookie_header: str | None) -> dict[str, str]:
    if not cookie_header:
        return {}
    cookies = {}
    for item in str(cookie_header).split(";"):
        if "=" not in item:
            continue
        name, value = item.strip().split("=", 1)
        if name:
            cookies[name] = value
    return cookies


def browser_cookie_json_to_dict(cookie_json: str | dict | list | None) -> dict[str, str]:
    if not cookie_json:
        return {}

    if isinstance(cookie_json, str):
        try:
            payload: Any = json.loads(cookie_json)
        except json.JSONDecodeError:
            return {}
    else:
        payload = cookie_json

    if isinstance(payload, list):
        cookie_items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("cookies"), list):
        cookie_items = payload["cookies"]
    elif isinstance(payload, dict):
        return {str(name): str(value) for name, value in payload.items() if value is not None}
    else:
        return {}

    cookies = {}
    for item in cookie_items:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        if name and value is not None:
            cookies[str(name)] = str(value)
    return cookies


def merge_cookie_sources(cookie_str: str | None = None, cookie_json: str | dict | list | None = None) -> dict[str, str]:
    cookies = browser_cookie_json_to_dict(cookie_json)
    cookies.update(cookie_header_to_dict(cookie_str))
    return cookies


def cookie_dict_to_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in cookies.items() if value is not None)


def cookie_dict_to_browser_items(
    cookies: dict[str, str],
    domain: str | None = None,
    max_age_days: int | None = None,
) -> list[dict[str, Any]]:
    if domain is None:
        domain = havana.DEFAULT_COOKIE_DOMAIN
    if max_age_days is None:
        max_age_days = havana.DEFAULT_COOKIE_MAX_AGE_DAYS
    expires = int(time.time()) + 86400 * max_age_days
    return [
        {
            "name": str(name),
            "value": str(value),
            "domain": domain,
            "path": "/",
            "expires": expires,
            "httpOnly": False,
            "secure": False,
            "sameSite": "Lax",
        }
        for name, value in cookies.items()
        if value is not None
    ]


def save_cookies_database(
    shop_name: str,
    cookies: dict[str, str],
    site: str | None = None,
    login_id: str | None = None,
    yingdao_account: str | None = None,
    maintainer_email: str | None = None,
) -> str:
    from database import DBManager

    if site is None:
        site = havana.DEFAULT_COOKIE_SITE

    cookie_header = cookie_dict_to_header(cookies)
    cookie_payload = json.dumps(
        {
            "url": havana.DEFAULT_COOKIE_URL,
            "cookies": cookie_dict_to_browser_items(cookies),
        },
        ensure_ascii=False,
    )
    cookie_dict_text = json.dumps(cookies, ensure_ascii=False)
    with DBManager() as db_manager:
        db_manager.upsert_cookie(
            site=site,
            shop_name=shop_name,
            cookie_str=cookie_header,
            cookie=cookie_payload,
            cookie_dict=cookie_dict_text,
            account=login_id,
            yingdao_account=yingdao_account,
            maintainer_email=maintainer_email,
        )
    logger.info(f"{shop_name} Cookie 已写入 get_cookie，站点={site}")
    return cookie_header


def load_cookies_database(site: str, shop_name: str) -> tuple[str | None, str | None]:
    from database import DBManager

    with DBManager() as db_manager:
        row = db_manager.select_cookie(site, shop_name)
    if not row:
        return None, None
    return row[1], row[2]


def validate_cookies(cookies: dict) -> bool:
    required_keys = {"cookie2"}
    if not required_keys & set(cookies.keys()):
        logger.info("  Cookie 缺少关键字段，需重新登录")
        return False

    logger.info("  验证 Cookie 有效性...")
    try:
        session = requests.Session()
        session.headers.update(havana.BASE_HEADERS)
        session.cookies.update(cookies)
        resp = session.get(havana.VALIDATE_URL, timeout=havana.TIMEOUT, allow_redirects=False)
        if resp.status_code == 200:
            logger.info("  Cookie 有效")
            return True
        if resp.status_code in (301, 302):
            location = resp.headers.get("Location", "")
            if "login" in location.lower():
                logger.info("  Cookie 已过期")
                return False
            logger.info("  Cookie 有效 (非登录重定向)")
            return True
    except Exception as exc:
        logger.warning(f"  验证请求失败: {exc}")
    return False


def validate_and_refresh_cookies(cookies: dict) -> tuple[bool, dict]:
    required_keys = {"unb", "cookie2"}
    if not required_keys & set(cookies.keys()):
        logger.info("  Cookie 缺少关键字段，需重新登录")
        return False, cookies

    logger.info("  用有效 Cookie 访问后台并刷新...")
    try:
        session = requests.Session()
        session.headers.update(havana.BASE_HEADERS)
        session.cookies.update(cookies)
        resp = session.get(havana.VALIDATE_URL, timeout=havana.TIMEOUT, allow_redirects=True)
        if resp.status_code == 200 and "login" not in resp.url.lower():
            refreshed = dict(cookies)
            refreshed.update(session.cookies.get_dict())
            logger.info(f"  Cookie 有效，已刷新（{len(refreshed)} 项）")
            return True, refreshed
        logger.info("  Cookie 已过期")
    except Exception as exc:
        logger.warning(f"  校验/刷新请求失败: {exc}")
    return False, cookies
