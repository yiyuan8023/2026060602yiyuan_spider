#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-15 17:24:32
- 最近修改：2026-06-15 17:54:03
- 文件用途：提供淘系登录人工介入入口，自动填写账号密码后等待人工完成滑块、短信或扫码，再保存页面 Cookie。
- 业务范围：适用于 API_login/API_TaoXi_login 的淘宝 Havana 登录页，结果可写入 get_cookie 或保存本地调试文件。
- 依赖入口：DrissionPage、extra.logger_、taobao_login.cookie_dict_to_header、taobao_login_auto 表单辅助函数。
- 验收方式：修改后执行 py_compile；真实运行时先单店铺验证人工过滑块、Cookie 写库和 cookie 读取面。
- 注意事项：API 层不读取 config/local.json；账号密码由 jobs_login 传入；日志不得输出密码和完整 Cookie。
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from extra.logger_ import logger

try:
    from ..API_TaoXi_SYCM_login import DEFAULT_COOKIE_SITE, DEFAULT_COOKIE_URL
    from ..API_TaoXi_base_login import cookie_dict_to_header
except ImportError:
    from API_login.API_TaoXi_login.API_TaoXi_SYCM_login import (
        DEFAULT_COOKIE_SITE, DEFAULT_COOKIE_URL,
    )
    from API_login.API_TaoXi_login.API_TaoXi_base_login import cookie_dict_to_header
# 人工介入复用自动化模块的浏览器填表助手（跨包引用 auto_login）
try:
    from ..auto_login.taobao_login_auto import (
        DEFAULT_OUTPUT_DIR,
        LOGIN_URL,
        SELLER_HOME_URL,
        accept_agreement_dialog,
        fill_login_form,
        safe_file_stem,
        save_cookies_local,
        submit_login_form,
        switch_to_password_login,
    )
except ImportError:
    from API_login.API_TaoXi_login.auto_login.taobao_login_auto import (
        DEFAULT_OUTPUT_DIR,
        LOGIN_URL,
        SELLER_HOME_URL,
        accept_agreement_dialog,
        fill_login_form,
        safe_file_stem,
        save_cookies_local,
        submit_login_form,
        switch_to_password_login,
    )


def page_cookies_to_dict(page: Any) -> dict[str, str]:
    """把 DrissionPage 当前页面 Cookie 转为请求头可用的 dict。"""
    cookies: dict[str, str] = {}
    for cookie in page.cookies():
        name = cookie.get("name")
        value = cookie.get("value")
        if name and value is not None:
            cookies[str(name)] = str(value)
    return cookies


def save_page_cookies_database(
    shop_name: str,
    browser_cookies: list[dict[str, Any]],
    site: str = DEFAULT_COOKIE_SITE,
    login_id: str | None = None,
    cookie_url: str = DEFAULT_COOKIE_URL,
    yingdao_account: str | None = None,
    maintainer_email: str | None = None,
) -> str:
    """把浏览器页面原始 Cookie 列表写入 get_cookie，保留 domain/expires 等页面 Cookie 字段。"""
    from database import DBManager

    cookie_dict = {
        str(cookie.get("name")): str(cookie.get("value"))
        for cookie in browser_cookies
        if cookie.get("name") and cookie.get("value") is not None
    }
    cookie_header = cookie_dict_to_header(cookie_dict)
    cookie_payload = json.dumps(
        {
            "url": cookie_url,
            "cookies": browser_cookies,
        },
        ensure_ascii=False,
    )
    cookie_dict_text = json.dumps(cookie_dict, ensure_ascii=False)
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
    logger.info(f"{shop_name} 页面 Cookie 已写入 get_cookie，站点={site}")
    return cookie_header


def wait_manual_login_success(page: Any, manual_timeout: int, poll_interval: int = 2) -> bool:
    """等待人工完成滑块、短信或扫码，直到页面离开 login URL。"""
    deadline = time.time() + max(int(manual_timeout), 1)
    last_url = ""
    while time.time() < deadline:
        current_url = page.url
        if current_url != last_url:
            logger.info(f"当前登录页面 URL: {current_url}")
            last_url = current_url
        if "login" not in current_url:
            return True
        time.sleep(max(int(poll_interval), 1))
    return False


def capture_manual_login_cookie(
    shop_name: str,
    login_id: str,
    password: str,
    site: str = DEFAULT_COOKIE_SITE,
    save_database: bool = True,
    save_local: bool = False,
    output_dir: Path | str | None = None,
    manual_timeout: int = 300,
    login_url: str = LOGIN_URL,
    post_login_url: str = SELLER_HOME_URL,
    yingdao_account: str | None = None,
    maintainer_email: str | None = None,
) -> dict[str, Any]:
    """
    自动填写账号密码后等待人工完成验证，并保存页面 Cookie。

    这个函数会打开可见浏览器窗口；调用方应只对单店铺小范围使用。
    """
    if not shop_name:
        raise RuntimeError("缺少 shop_name")
    if not login_id or not password:
        raise RuntimeError(f"{shop_name} 缺少 login_id 或 password")

    try:
        from DrissionPage import ChromiumOptions, ChromiumPage
    except ImportError as exc:
        raise RuntimeError("DrissionPage 未安装，无法执行人工介入登录") from exc

    output_path = Path(output_dir).resolve() if output_dir else DEFAULT_OUTPUT_DIR

    options = ChromiumOptions()
    options.auto_port(True)
    options.set_argument("--lang=zh-CN")
    options.set_argument("--disable-blink-features=AutomationControlled")
    options.set_pref("credentials_enable_service", False)
    options.set_pref("profile.password_manager_enabled", False)

    page = ChromiumPage(addr_or_opts=options)
    try:
        logger.info(f"{shop_name} 打开淘宝登录页，自动填写账号密码后等待人工验证")
        page.get(login_url)
        time.sleep(2.5)
        accept_agreement_dialog(page)
        switch_to_password_login(page)
        fill_login_form(page, login_id, password)
        submit_login_form(page)
        time.sleep(2)
        accept_agreement_dialog(page)

        logger.warning(
            f"{shop_name} 请在浏览器中手动完成滑块、短信或扫码验证，"
            f"最长等待 {manual_timeout}s"
        )
        if not wait_manual_login_success(page, manual_timeout=manual_timeout):
            output_path.mkdir(parents=True, exist_ok=True)
            debug_path = output_path / f"manual_debug_{safe_file_stem(shop_name)}.png"
            try:
                page.get_screenshot(str(debug_path))
                logger.warning(f"{shop_name} 人工登录等待超时，已保存截图: {debug_path}")
            except Exception:
                logger.warning(f"{shop_name} 人工登录等待超时，截图保存失败")
            return {
                "shop_name": shop_name,
                "site": site,
                "status": "timeout",
                "cookie_count": 0,
                "saved_to_db": False,
                "saved_local": False,
            }

        if post_login_url and "myseller.taobao.com" not in page.url:
            logger.info(f"{shop_name} 已离开登录页，跳转卖家后台补全 Cookie")
            page.get(post_login_url)
            time.sleep(2)

        browser_cookies = page.cookies()
        cookies = {
            str(cookie.get("name")): str(cookie.get("value"))
            for cookie in browser_cookies
            if cookie.get("name") and cookie.get("value") is not None
        }
        if not cookies:
            return {
                "shop_name": shop_name,
                "site": site,
                "status": "no_cookie",
                "cookie_count": 0,
                "saved_to_db": False,
                "saved_local": False,
            }

        local_paths: dict[str, str] = {}
        if save_local:
            json_path, netscape_path, _cookie_count = save_cookies_local(page, shop_name, output_path)
            local_paths = {"json": str(json_path), "netscape": str(netscape_path)}

        cookie_header_len = 0
        if save_database:
            cookie_header = save_page_cookies_database(
                shop_name=shop_name,
                browser_cookies=browser_cookies,
                site=site,
                login_id=login_id,
                cookie_url=post_login_url or DEFAULT_COOKIE_URL,
                yingdao_account=yingdao_account,
                maintainer_email=maintainer_email,
            )
            cookie_header_len = len(cookie_header)

        logger.info(
            f"{shop_name} 人工介入登录完成，Cookie 数量={len(cookies)}，"
            f"写库={save_database}，本地保存={save_local}"
        )
        return {
            "shop_name": shop_name,
            "site": site,
            "status": "success",
            "cookie_count": len(cookies),
            "cookie_str_len": cookie_header_len,
            "saved_to_db": save_database,
            "saved_local": save_local,
            "local_paths": local_paths,
        }
    finally:
        time.sleep(1)
        try:
            page.quit()
        except Exception:
            pass
