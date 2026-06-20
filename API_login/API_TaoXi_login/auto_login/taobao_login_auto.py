#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-15 17:04:18
- 最近修改：2026-06-15 17:04:18
- 文件用途：提供淘系登录浏览器自动化独立调试入口，用于协议登录失败时手动验证页面、短信、二维码和滑块链路。
- 业务范围：适用于 API_login/API_TaoXi_login 的淘宝 Havana 登录页；账号密码从 config/local.json 的 taobao_login 配置读取。
- 依赖入口：DrissionPage、slider_helper.handle_nc_slider、sms_helper.get_sms_code、config.local_config、extra.logger_。
- 验收方式：修改后执行 py_compile；真实登录需指定单店铺小范围验证。
- 注意事项：本脚本不写数据库；默认只保存本地 Cookie 文件，日志不得输出密码和完整 Cookie。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


# 本文件位于 API_login/API_TaoXi_login/auto_login/，向上三级才是项目根
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extra.logger_ import logger

try:
    from .slider_helper import handle_nc_slider
except ImportError:
    from slider_helper import handle_nc_slider


LOGIN_URL = "https://login.taobao.com/havanaone/login/login.htm?bizName=taobao"
SELLER_HOME_URL = "https://myseller.taobao.com/seller_admin.htm"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent


def normalize_shop_configs(raw_shops: Any, defaults: dict[str, Any]) -> list[dict[str, Any]]:
    """读取 local.json 的多店铺配置，保持和 jobs_login 的配置形态一致。"""
    if isinstance(raw_shops, dict):
        raw_items = []
        for shop_name, shop_config in raw_shops.items():
            if isinstance(shop_config, dict):
                raw_items.append({"shop_name": shop_name, **shop_config})
            else:
                raw_items.append({"shop_name": shop_name})
    elif isinstance(raw_shops, list):
        raw_items = raw_shops
    else:
        raw_items = []

    shop_configs: list[dict[str, Any]] = []
    for raw_item in raw_items:
        if isinstance(raw_item, str):
            raw_config = {"shop_name": raw_item}
        elif isinstance(raw_item, dict):
            raw_config = raw_item.copy()
        else:
            raise RuntimeError("config/local.json 的 taobao_login.shops 仅支持对象、列表或店铺名字符串")

        if not raw_config.get("shop_name"):
            raise RuntimeError("config/local.json 的 taobao_login.shops 存在缺少 shop_name 的配置")
        shop_configs.append({**defaults, **raw_config})
    return shop_configs


def load_shop_configs() -> list[dict[str, Any]]:
    """从 config/local.json 读取 taobao_login 店铺配置。"""
    from config.local_config import get_local_section

    local_config = get_local_section("taobao_login")
    if not local_config:
        raise RuntimeError("未配置 config/local.json 的 taobao_login，无法执行自动化登录")

    defaults = local_config.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise RuntimeError("config/local.json 的 taobao_login.defaults 必须是对象")

    shop_configs = normalize_shop_configs(local_config.get("shops"), defaults)
    if not shop_configs:
        raise RuntimeError("config/local.json 的 taobao_login.shops 未配置店铺")
    return shop_configs


def choose_shop_config(shop_configs: list[dict[str, Any]], shop_name: str | None) -> dict[str, Any]:
    if shop_name:
        for shop_config in shop_configs:
            if shop_config.get("shop_name") == shop_name:
                return shop_config
        raise RuntimeError(f"未找到店铺配置: {shop_name}")
    return shop_configs[0]


def safe_file_stem(text: str) -> str:
    stem = re.sub(r"[\\/:*?\"<>|\s]+", "_", text.strip())
    return stem or "taobao"


def find_visible(page: Any, selectors: list[str], timeout: int = 3) -> tuple[Any | None, str | None]:
    for selector in selectors:
        try:
            element = page.ele(selector, timeout=timeout)
            if element and element.states.is_displayed:
                return element, selector
        except Exception:
            continue
    return None, None


def click_first_visible(page: Any, selectors: list[str], timeout: int = 2) -> bool:
    element, selector = find_visible(page, selectors, timeout=timeout)
    if not element:
        return False
    try:
        element.click()
    except Exception:
        element.click(by_js=True)
    logger.info(f"已点击页面元素: {selector}")
    return True


def switch_to_password_login(page: Any) -> None:
    click_first_visible(
        page,
        [
            "xpath://span[contains(text(),'密码登录')]",
            "xpath://div[contains(text(),'密码登录')]",
        ],
        timeout=3,
    )


def accept_agreement_dialog(page: Any) -> None:
    click_first_visible(
        page,
        [
            "xpath://button[text()='同意']",
            "xpath://div[text()='同意']",
            "xpath://span[text()='同意']",
            "xpath://a[text()='同意']",
            "css:button.agree-btn",
            "css:.dialog-btn-agree",
            "css:div.btn-agree",
        ],
        timeout=2,
    )


def fill_login_form(page: Any, login_id: str, password: str) -> None:
    account_input, account_selector = find_visible(
        page,
        [
            "css:#fm-login-id",
            "css:input[name='loginId']",
            "css:input[placeholder*='账号']",
            "css:input[placeholder*='手机']",
            "css:input[autocomplete='username']",
        ],
        timeout=5,
    )
    if not account_input:
        raise RuntimeError("未找到账号输入框")
    account_input.clear()
    account_input.input(login_id)
    logger.info(f"已填写账号输入框: {account_selector}")

    password_input, password_selector = find_visible(
        page,
        [
            "css:#fm-login-password",
            "css:input[type='password']",
            "css:input[name='password']",
            "css:input[placeholder*='密码']",
        ],
        timeout=5,
    )
    if not password_input:
        raise RuntimeError("未找到密码输入框")
    password_input.clear()
    password_input.input(password)
    logger.info(f"已填写密码输入框: {password_selector}")


def submit_login_form(page: Any) -> None:
    login_button, selector = find_visible(
        page,
        [
            "css:#login-form button[type='submit']",
            "css:button[type='submit']",
            "css:.btn-login",
            "css:#J_Login",
            "css:.login-btn",
        ],
        timeout=3,
    )
    if login_button:
        try:
            login_button.click()
        except Exception:
            login_button.click(by_js=True)
        logger.info(f"已点击登录按钮: {selector}")
        return

    password_input, _selector = find_visible(page, ["css:input[type='password']"], timeout=2)
    if password_input:
        password_input.input("\n")
        logger.info("未找到登录按钮，已用 Enter 提交")
        return
    raise RuntimeError("未找到登录按钮或密码输入框，无法提交登录")


def wait_leave_login_page(page: Any, seconds: int) -> bool:
    for _ in range(max(int(seconds), 1)):
        if "login" not in page.url:
            return True
        time.sleep(1)
    return False


def handle_sms_if_present(page: Any, wait_seconds: int = 60) -> bool:
    try:
        sms_input = page.ele("css:input[placeholder*='验证码']", timeout=3)
        sms_button = page.ele("css:button[class*='send'], button[class*='code'], a[class*='send']", timeout=2)
        if not (sms_input and sms_button and sms_input.states.is_displayed and sms_button.states.is_displayed):
            return False
    except Exception:
        return False

    logger.info("检测到短信验证码，尝试读取邮箱转发验证码")
    try:
        sms_button.click()
    except Exception:
        pass

    try:
        from ..sms_helper import get_sms_code
    except ImportError:
        from API_login.API_TaoXi_login.sms_helper import get_sms_code

    code = get_sms_code(wait_seconds=wait_seconds, sender_keyword="taobao")
    if not code:
        logger.warning("未获取到短信验证码")
        return False

    sms_input.clear()
    sms_input.input(code)
    logger.info("已填写短信验证码")
    click_first_visible(
        page,
        [
            "css:button[type='submit']",
            "css:.btn-submit",
            "css:button.J_Submit",
            "xpath://button[contains(text(),'确认')]",
            "xpath://button[contains(text(),'登录')]",
            "xpath://button[contains(text(),'验证')]",
        ],
        timeout=3,
    )
    return True


def wait_manual_qr_if_present(page: Any, manual_wait: int) -> None:
    try:
        qr_element = page.ele("css:img[src*='qrcode'], canvas.qrcode-img", timeout=2)
        if qr_element and qr_element.states.is_displayed and qr_element.rect.size[0] > 50:
            logger.warning(f"检测到二维码验证，等待 {manual_wait}s 供人工扫码")
            time.sleep(max(int(manual_wait), 0))
    except Exception:
        pass


def save_cookies_local(page: Any, shop_name: str, output_dir: Path) -> tuple[Path, Path, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cookies_list = page.cookies()
    cookie_count = len(cookies_list)
    file_stem = safe_file_stem(shop_name)
    json_path = output_dir / f"taobao_cookies_{file_stem}.json"
    netscape_path = output_dir / f"taobao_cookies_{file_stem}.txt"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(cookies_list, file, ensure_ascii=False, indent=2)

    expires = int(time.time()) + 86400 * 30
    lines = ["# Netscape HTTP Cookie File\n"]
    for cookie in cookies_list:
        domain = cookie.get("domain", ".taobao.com")
        if not domain.startswith("."):
            domain = f".{domain}"
        name = cookie.get("name", "")
        value = cookie.get("value", "")
        path = cookie.get("path", "/") or "/"
        secure = "TRUE" if cookie.get("secure") else "FALSE"
        lines.append(f"{domain}\tTRUE\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

    with netscape_path.open("w", encoding="utf-8") as file:
        file.writelines(lines)

    return json_path, netscape_path, cookie_count


def run_auto_login(shop_config: dict[str, Any], output_dir: Path, save_local: bool, manual_wait: int) -> str:
    try:
        from DrissionPage import ChromiumOptions, ChromiumPage
    except ImportError as exc:
        raise RuntimeError("DrissionPage 未安装，无法执行自动化登录") from exc

    shop_name = str(shop_config.get("shop_name") or "").strip()
    login_id = str(shop_config.get("login_id") or "").strip()
    password = str(shop_config.get("password") or "")
    if not shop_name:
        raise RuntimeError("店铺配置缺少 shop_name")
    if not login_id or not password:
        raise RuntimeError(f"{shop_name} 缺少 login_id 或 password")

    timeout = int(shop_config.get("timeout") or 30)
    slider_retry = int(shop_config.get("slider_retry") or 4)

    options = ChromiumOptions()
    options.auto_port(True)
    options.set_argument("--lang=zh-CN")
    options.set_argument("--disable-blink-features=AutomationControlled")
    options.set_pref("credentials_enable_service", False)
    options.set_pref("profile.password_manager_enabled", False)

    page = ChromiumPage(addr_or_opts=options)
    try:
        logger.info(f"{shop_name} 开始浏览器自动化登录调试")
        page.get(LOGIN_URL)
        time.sleep(2.5)
        logger.info(f"当前 URL: {page.url}")

        accept_agreement_dialog(page)
        switch_to_password_login(page)
        fill_login_form(page, login_id, password)
        submit_login_form(page)
        time.sleep(3)

        accept_agreement_dialog(page)
        if "login" in page.url:
            handle_nc_slider(page, max_retry=slider_retry, logger=logger)
            time.sleep(2)

        if "login" in page.url:
            handle_sms_if_present(page, wait_seconds=60)
            time.sleep(2)

        if "login" in page.url:
            wait_manual_qr_if_present(page, manual_wait=manual_wait)

        success = wait_leave_login_page(page, timeout)
        if not success:
            output_dir.mkdir(parents=True, exist_ok=True)
            debug_path = output_dir / f"debug_{safe_file_stem(shop_name)}.png"
            try:
                page.get_screenshot(str(debug_path))
                logger.warning(f"{shop_name} 登录未确认，已保存截图: {debug_path}")
            except Exception:
                logger.warning(f"{shop_name} 登录未确认，截图保存失败")
            return "unknown"

        if "myseller.taobao.com" not in page.url:
            page.get(SELLER_HOME_URL)
            time.sleep(2)

        if save_local:
            json_path, netscape_path, cookie_count = save_cookies_local(page, shop_name, output_dir)
            logger.info(f"{shop_name} Cookie 已本地保存，数量={cookie_count}")
            logger.info(f"JSON 文件: {json_path}")
            logger.info(f"Netscape 文件: {netscape_path}")

        logger.info(f"{shop_name} 浏览器自动化登录成功")
        return "success"
    finally:
        time.sleep(1)
        try:
            page.quit()
        except Exception:
            pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="淘宝 Havana 登录浏览器自动化独立调试脚本")
    parser.add_argument("--shop-name", help="指定 config/local.json 中 taobao_login.shops 的店铺名")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="本地 Cookie/截图输出目录")
    parser.add_argument("--no-save-local", action="store_true", help="只验证登录，不保存本地 Cookie 文件")
    parser.add_argument("--manual-wait", type=int, default=60, help="二维码或人工验证等待秒数")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    shop_configs = load_shop_configs()
    shop_config = choose_shop_config(shop_configs, args.shop_name)
    output_dir = Path(args.output_dir).resolve()
    status = run_auto_login(
        shop_config=shop_config,
        output_dir=output_dir,
        save_local=not args.no_save_local,
        manual_wait=args.manual_wait,
    )
    logger.info(f"自动化登录调试结束，状态={status}")


if __name__ == "__main__":
    main()
