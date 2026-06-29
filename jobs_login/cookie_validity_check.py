"""
开发说明：
- 作者：一元
- 创建时间：2026-06-26 16:10:00
- 最近修改：2026-06-26 16:10:00
- 文件用途：排查 Cookie 源库 cookie 表中的登录态是否有效；有效则跳过，失效则发送钉钉通知。
- 业务范围：适用于 cookie 表中可由 Cookie JSON 解析出 URL/domain 的平台登录态巡检；不执行登录、不刷新 Cookie、不写数据库。
- 依赖入口：调用 DBManager.select_cookie_check_rows 读取 cookie 视图，按 Cookie 自带 URL/domain 选择轻量校验方式。
- 验收方式：执行 py_compile 和导入探针；真实运行通过 run_job.py 启动，可用 --site/--shop-name 缩小范围。
- 注意事项：日志和钉钉通知不得输出 Cookie、账号密码、数据库凭据或 Webhook；单条失败只通知和记录，不让脚本报错退出。
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

import requests

from API.API_DingTalk.API_DingTalk_Notify import DingTalkJobNotifier
from API.API_ChiTu.API_Chitu_Base import CHITU_USER_API
from API.API_WPS_Docs import WpsDocsFileApi
from API.API_WeCom_Docs import WeComDocsFileApi
from API_login.API_TaoXi_login.API_TaoXi_base_login.cookie_manager import (
    cookie_dict_to_header,
    merge_cookie_sources,
    validate_cookies,
)
from API_login.API_TaoXi_login.API_TaoXi_base_login.havana import configure_login
from config import get_cookie_database_name
from config.local_config import get_local_section
from database import DBManager
from extra.logger_ import logger


TASK_NAME = "jobs_login/cookie_validity_check.py"
DEFAULT_TIMEOUT = 30
DEFAULT_HTTP_CHECKS = [
    {
        "name": "WPS文档",
        "domains": ("kdocs.cn",),
        "method": "wps_doc",
    },
    {
        "name": "企微文档",
        "domains": ("doc.weixin.qq.com",),
        "method": "wecom_doc",
    },
    {
        "name": "赤兔",
        "domains": ("kf.topchitu.com", "topchitu.com"),
        "validate_url": CHITU_USER_API,
        "method": "chitu",
    },
    {
        "name": "腾讯文档",
        "domains": ("docs.qq.com",),
        "validate_url": "https://docs.qq.com/cgi-bin/online_docs/user_info",
        "invalid_keywords": ("尚未登录", "未登录", '"ret":12100', '"retcode":12100'),
    },
]
TAOXI_DOMAIN_RULES = [
    {
        "name": "DChain",
        "domains": ("web.scm.tmall.com", "scm.tmall.com"),
        "config_section": "dchain_login",
        "validate_url": "https://web.scm.tmall.com/",
    },
    {
        "name": "淘系卖家后台",
        "domains": ("taobao.com", "tmall.com"),
        "config_section": "taobao_login",
        "validate_url": "https://myseller.taobao.com/home.htm",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查 yiyuan_test.cookie 中的 Cookie 是否有效")
    parser.add_argument("--site", help="只检查指定站点标签，例如 生意参谋、DChain、wps文档")
    parser.add_argument("--shop-name", action="append", help="只检查指定店铺/账号，可重复传入")
    parser.add_argument("--no-dingtalk", action="store_true", help="只记录日志，不发送钉钉通知")
    return parser.parse_args()


def build_domain_check_config() -> list[dict[str, Any]]:
    checks = [dict(config) for config in DEFAULT_HTTP_CHECKS]

    for taoxi_config in TAOXI_DOMAIN_RULES:
        check_config = dict(taoxi_config)
        local_section = get_local_section(check_config["config_section"])
        defaults = local_section.get("defaults") or {}
        if not isinstance(defaults, dict):
            defaults = {}
        check_config["validate_url"] = defaults.get("validate_url") or check_config["validate_url"]
        check_config["timeout"] = defaults.get("timeout") or DEFAULT_TIMEOUT
        check_config["method"] = "taoxi"
        checks.append(check_config)

    custom_section = get_local_section("cookie_check")
    custom_domains = custom_section.get("domains") or {}
    if isinstance(custom_domains, dict):
        for domain, raw_config in custom_domains.items():
            if isinstance(raw_config, str):
                checks.append(
                    {
                        "name": domain,
                        "domains": (domain,),
                        "validate_url": raw_config,
                        "timeout": DEFAULT_TIMEOUT,
                        "method": "http",
                    }
                )
            elif isinstance(raw_config, dict) and raw_config.get("validate_url"):
                checks.append(
                    {
                        "name": raw_config.get("name") or domain,
                        "domains": tuple(raw_config.get("domains") or [domain]),
                        "validate_url": raw_config["validate_url"],
                        "timeout": raw_config.get("timeout") or DEFAULT_TIMEOUT,
                        "method": raw_config.get("method") or "http",
                        "invalid_keywords": tuple(raw_config.get("invalid_keywords") or ()),
                    }
                )
    return checks


def build_dingtalk_notifier(disabled: bool = False) -> DingTalkJobNotifier:
    if disabled:
        return DingTalkJobNotifier(enabled=False)
    try:
        return DingTalkJobNotifier.from_config()
    except Exception as exc:
        logger.warning(f"钉钉通知初始化失败，已跳过本次巡检通知：{type(exc).__name__}: {exc}")
        return DingTalkJobNotifier(enabled=False)


def load_cookie_rows(site: str | None = None, shop_names=None):
    with DBManager() as db_manager:
        return db_manager.select_cookie_check_rows(site=site, shop_names=shop_names)


def parse_cookie_payload(cookie_json):
    if not cookie_json:
        return None
    if isinstance(cookie_json, str):
        try:
            return json.loads(cookie_json)
        except json.JSONDecodeError:
            return None
    return cookie_json


def extract_cookie_targets(cookie_json) -> dict[str, Any]:
    payload = parse_cookie_payload(cookie_json)
    urls = []
    domains = []

    if isinstance(payload, dict):
        if payload.get("url"):
            urls.append(str(payload["url"]))
        cookie_items = payload.get("cookies")
        if isinstance(cookie_items, list):
            for item in cookie_items:
                if isinstance(item, dict) and item.get("domain"):
                    domains.append(str(item["domain"]))
        elif not cookie_items:
            domains.extend(_domain_like_cookie_keys(payload))
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                if item.get("url"):
                    urls.append(str(item["url"]))
                if item.get("domain"):
                    domains.append(str(item["domain"]))

    parsed_domains = []
    for url in urls:
        hostname = urlparse(url).hostname
        if hostname:
            parsed_domains.append(hostname)

    all_domains = parsed_domains + domains
    normalized_domains = []
    for domain in all_domains:
        normalized = normalize_domain(domain)
        if normalized and normalized not in normalized_domains:
            normalized_domains.append(normalized)

    return {"urls": urls, "domains": normalized_domains}


def _domain_like_cookie_keys(payload: dict[str, Any]) -> list[str]:
    # 兼容少量直接保存成 {domain: cookie_dict} 的历史结构；普通 cookie 名不会包含点。
    return [key for key in payload if "." in str(key)]


def normalize_domain(domain: str | None) -> str:
    domain = str(domain or "").strip().lower()
    if not domain:
        return ""
    if "://" in domain:
        domain = urlparse(domain).hostname or ""
    return domain.lstrip(".")


def domain_matches(domain: str, rule_domain: str) -> bool:
    domain = normalize_domain(domain)
    rule_domain = normalize_domain(rule_domain)
    return bool(domain and rule_domain and (domain == rule_domain or domain.endswith(f".{rule_domain}")))


def resolve_check_config(targets: dict[str, Any], checks: list[dict[str, Any]], cookies: dict[str, str]):
    for domain in targets["domains"]:
        for check_config in checks:
            if any(domain_matches(domain, rule_domain) for rule_domain in check_config.get("domains", ())):
                resolved = dict(check_config)
                resolved["target_domain"] = domain
                resolved["target_url"] = find_target_url_for_domain(targets.get("urls") or [], domain)
                resolved.setdefault("method", "http")
                resolved.setdefault("timeout", DEFAULT_TIMEOUT)
                return resolved

    if "cookie2" in cookies:
        return {
            "name": "淘系卖家后台",
            "target_domain": "cookie2",
            "method": "taoxi",
            "validate_url": "https://myseller.taobao.com/home.htm",
            "timeout": DEFAULT_TIMEOUT,
        }
    return None


def find_target_url_for_domain(urls: list[str], domain: str) -> str:
    for url in urls:
        hostname = urlparse(str(url)).hostname
        if hostname and domain_matches(hostname, domain):
            return str(url)
    return str(urls[0]) if urls else ""


def validate_http_cookie(cookies: dict[str, str], check_config: dict[str, Any]) -> tuple[bool, str]:
    try:
        session = requests.Session()
        session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "accept": "application/json, text/plain, */*",
                "referer": check_config.get("referer") or check_config["validate_url"],
            }
        )
        session.cookies.update(cookies)
        response = session.get(
            check_config["validate_url"],
            timeout=check_config.get("timeout") or DEFAULT_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        return False, f"校验请求异常：{type(exc).__name__}: {exc}"

    if response.status_code in {301, 302, 401, 403}:
        return False, f"校验接口返回状态码 {response.status_code}"
    if response.status_code >= 400:
        return False, f"校验接口返回状态码 {response.status_code}"

    response_text = (response.text or "")[:1000]
    compact_text = response_text.replace(" ", "")
    for keyword in check_config.get("invalid_keywords") or ():
        if str(keyword).replace(" ", "") in compact_text:
            return False, f"校验响应包含失效特征：{keyword}"
    return True, f"HTTP {response.status_code}"


def validate_wps_doc_cookie(cookies: dict[str, str], check_config: dict[str, Any]) -> tuple[bool, str]:
    document_url = check_config.get("target_url") or ""
    if not document_url:
        return False, "WPS Cookie 缺少可校验文档 URL"
    try:
        cookie_header = cookie_dict_to_header(cookies)
        api = WpsDocsFileApi(cookie_header, referer=document_url)
        file_id = api.resolve_file_id(document_url)
        file_info = api.get_file_info(file_id)
    except Exception as exc:
        return False, f"WPS 文档校验异常：{type(exc).__name__}: {exc}"

    file_name = file_info.get("fname") or file_info.get("name") or file_info.get("file_name") or ""
    return True, f"file_id={file_id}, name={file_name}"


def validate_wecom_doc_cookie(cookies: dict[str, str], check_config: dict[str, Any]) -> tuple[bool, str]:
    document_url = check_config.get("target_url") or ""
    if not document_url:
        return False, "企微文档 Cookie 缺少可校验文档 URL"
    try:
        cookie_header = cookie_dict_to_header(cookies)
        api = WeComDocsFileApi(cookie_header, referer=document_url)
        file_info = api.resolve_document_info(document_url)
    except Exception as exc:
        return False, f"企微文档校验异常：{type(exc).__name__}: {exc}"

    return True, f"pad_id={file_info.get('pad_id')}, title={file_info.get('title')}"


def validate_chitu_cookie(cookies: dict[str, str], check_config: dict[str, Any]) -> tuple[bool, str]:
    try:
        response = requests.get(
            check_config.get("validate_url") or CHITU_USER_API,
            headers={
                "cookie": cookie_dict_to_header(cookies),
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "accept": "application/json, text/plain, */*",
                "referer": "https://kf.topchitu.com/web/homepage/team",
            },
            timeout=check_config.get("timeout") or DEFAULT_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        return False, f"赤兔校验请求异常：{type(exc).__name__}: {exc}"

    if response.status_code != 200:
        return False, f"赤兔用户接口返回状态码 {response.status_code}"
    try:
        response_json = response.json()
    except ValueError:
        preview = " ".join((response.text or "")[:120].split())
        return False, f"赤兔用户接口响应不是 JSON：{preview}"
    if not response_json.get("currentUser"):
        return False, "赤兔用户接口未返回 currentUser"
    return True, "currentUser 已返回"


def validate_taoxi_cookie(cookies: dict[str, str], check_config: dict[str, Any]) -> tuple[bool, str]:
    configure_login(
        validate_url=check_config["validate_url"],
        timeout=check_config.get("timeout") or DEFAULT_TIMEOUT,
    )
    if validate_cookies(cookies):
        return True, check_config["validate_url"]
    return False, "淘系校验未通过"


def validate_cookie_by_config(cookies: dict[str, str], check_config: dict[str, Any]) -> tuple[bool, str]:
    method = check_config.get("method")
    if method == "wps_doc":
        return validate_wps_doc_cookie(cookies, check_config)
    if method == "wecom_doc":
        return validate_wecom_doc_cookie(cookies, check_config)
    if method == "chitu":
        return validate_chitu_cookie(cookies, check_config)
    if method == "taoxi":
        return validate_taoxi_cookie(cookies, check_config)
    return validate_http_cookie(cookies, check_config)


def notify_cookie_invalid(
    notifier: DingTalkJobNotifier,
    *,
    shop_name: str,
    site: str,
    reason: str,
) -> None:
    if not notifier.enabled:
        return

    safe_reason = str(reason).replace("\n", " ")[:800]
    title = f"Cookie失效：{site}/{shop_name}"
    text = (
        f"### {title}\n\n"
        f"- 任务：`{TASK_NAME}`\n"
        f"- Cookie表：`{get_cookie_database_name()}.cookie`\n"
        f"- 站点：{site}\n"
        f"- 店铺/账号：{shop_name}\n"
        f"- 状态：失效\n"
        f"- 摘要：{safe_reason}\n"
    )
    try:
        notifier.send_markdown(title, text)
    except Exception as exc:
        logger.warning(f"{site}/{shop_name} 钉钉失效通知发送失败：{type(exc).__name__}: {exc}")


def log_result_summary(results: list[dict[str, Any]]) -> None:
    site_stats = defaultdict(lambda: {"total": 0, "valid": 0, "invalid": 0})
    for result in results:
        site = result.get("site") or "未知站点"
        status = result.get("status")
        site_stats[site]["total"] += 1
        if status in site_stats[site]:
            site_stats[site][status] += 1

    for site, stats in sorted(site_stats.items()):
        logger.info(
            f"Cookie 巡检统计：站点={site}，总数={stats['total']}，"
            f"有效={stats['valid']}，失效={stats['invalid']}"
        )


def check_one_cookie(row, domain_checks: list[dict[str, Any]]) -> dict[str, Any]:
    shop_name, site, cookie_str, cookie_json = row
    shop_name = str(shop_name or "").strip()
    site = str(site or "").strip()
    row_label = f"{site}/{shop_name}"

    cookies = merge_cookie_sources(cookie_str, cookie_json)
    if not cookies:
        logger.warning(f"{row_label} Cookie 为空或无法解析")
        return {"shop_name": shop_name, "site": site, "status": "invalid", "reason": "Cookie 为空或无法解析"}

    targets = extract_cookie_targets(cookie_json)
    check_config = resolve_check_config(targets, domain_checks, cookies)
    if not check_config:
        reason = "Cookie 不为空，但未解析到可校验的 URL/domain"
        logger.warning(f"{row_label} {reason}")
        return {"shop_name": shop_name, "site": site, "status": "invalid", "reason": reason}

    target_domain = check_config.get("target_domain") or check_config.get("name")
    try:
        ok, detail = validate_cookie_by_config(cookies, check_config)
    except Exception as exc:
        reason = f"校验异常：{type(exc).__name__}: {exc}"
        logger.warning(f"{row_label} {reason}")
        return {"shop_name": shop_name, "site": site, "status": "invalid", "reason": reason}

    if ok:
        logger.info(f"{row_label} Cookie 有效，校验目标={target_domain}，方式={check_config['name']}，跳过")
        return {"shop_name": shop_name, "site": site, "status": "valid", "reason": ""}

    reason = f"{check_config['name']} 校验失败：{detail}"
    logger.warning(f"{row_label} Cookie 已失效，校验目标={target_domain}，{reason}")
    return {"shop_name": shop_name, "site": site, "status": "invalid", "reason": reason}


def main() -> None:
    args = parse_args()
    notifier = build_dingtalk_notifier(disabled=args.no_dingtalk)
    domain_checks = build_domain_check_config()

    try:
        rows = load_cookie_rows(site=args.site, shop_names=args.shop_name)
    except Exception as exc:
        logger.error(f"读取 Cookie 表失败，已结束巡检但不抛出异常：{type(exc).__name__}: {exc}")
        return

    if not rows:
        logger.warning("Cookie 表没有匹配到需要检查的记录")
        return

    results = []
    for row in rows:
        try:
            result = check_one_cookie(row, domain_checks)
        except Exception as exc:
            shop_name = str(row[0] if row else "未知店铺")
            site = str(row[1] if row and len(row) > 1 else "未知站点")
            result = {
                "shop_name": shop_name,
                "site": site,
                "status": "invalid",
                "reason": f"巡检异常：{type(exc).__name__}: {exc}",
            }
            logger.warning(f"{site}/{shop_name} 巡检异常，已按失效处理：{result['reason']}")

        if result["status"] == "invalid":
            notify_cookie_invalid(
                notifier,
                shop_name=result["shop_name"],
                site=result["site"],
                reason=result["reason"],
            )
        results.append(result)

    valid_count = sum(1 for result in results if result["status"] == "valid")
    invalid_count = sum(1 for result in results if result["status"] == "invalid")
    log_result_summary(results)
    logger.info(
        f"Cookie 有效性巡检完成，总数={len(results)}，"
        f"有效={valid_count}，失效={invalid_count}"
    )


if __name__ == "__main__":
    main()
