"""
开发说明：
- 作者：一元
- 创建时间：2025-04-29 10:48:00
- 最近修改：2026-06-10 17:30:00
- 文件用途：负责赤兔 Cookie 获取、校验、刷新和写入 get_cookie 源表。
- 业务范围：适用于赤兔 API 调用前的登录态准备；优先复用 cookie 视图中的淘系-赤兔 Cookie，失效后用生意参谋 Cookie 重新授权。
- 依赖入口：使用 Playwright、requests、database.DBManager、cookie_manager.extra_cookie、extra.logger_。
- 验收方式：修改后执行 py_compile、导入探针，并用单店铺任务验证 Cookie 复用、授权刷新和 get_cookie 写入。
- 注意事项：只读取 cookie 视图，只写 get_cookie 表；日志不得输出真实 Cookie。
"""

import json
from json import JSONDecodeError

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from cookie_manager.extra_cookie import (
    cookie_str_to_dict,
    cookiejar_to_cookie_str,
    get_ramdom_ua,
)
from API.API_ChiTu.API_Chitu_Base import ChituAPIError
from database import DBManager
from extra.logger_ import logger


CHITU_SITE = "淘系-赤兔"
SYCM_SITE = "生意参谋"
CHITU_HOME_URL = "https://kf.topchitu.com/"
CHITU_USER_API = "https://kf.topchitu.com/api/user"
PROFESSION_LOGIN_XPATH = "xpath=//div[@class='professionLogin']/div"
AUTHORIZE_LOGIN_XPATH = (
    "xpath=//*[text()='检测到您已登录淘宝，可以直接进行授权']/..//*[text()='授权并登录']"
)
SUBMIT_LOGIN_XPATH = "xpath=//button[@id='sub']"


class ChituLoginError(ChituAPIError):
    """赤兔授权登录失败。"""


def load_browser_cookies(cookie_json):
    try:
        cookie_payload = json.loads(cookie_json)
    except (TypeError, JSONDecodeError) as exc:
        raise ChituLoginError("生意参谋 Cookie 不是有效 JSON") from exc

    cookies = cookie_payload.get("cookies")
    if not isinstance(cookies, list) or not cookies:
        raise ChituLoginError("生意参谋 Cookie JSON 缺少 cookies 列表")
    return cookies


def fetch_cookie_row(site, shop_name):
    with DBManager() as db_manager:
        return db_manager.select_cookie(site, shop_name)


def fetch_cookie_header(site, shop_name):
    cookie_row = fetch_cookie_row(site, shop_name)
    return cookie_row[1] if cookie_row else None


def is_chitu_cookie_valid(cookie_header):
    if not cookie_header:
        return False

    headers = {"User-Agent": get_ramdom_ua(), "cookie": cookie_header}
    try:
        response = requests.get(CHITU_USER_API, headers=headers, timeout=15)
        if response.status_code != 200:
            return False
        return bool(response.json().get("currentUser"))
    except Exception as exc:
        logger.warning(f"赤兔 Cookie 校验失败: {exc}")
        return False


def save_chitu_cookie(shop_name, cookie_header, cookie_items):
    cookie_json = json.dumps({"cookies": cookie_items}, ensure_ascii=False)
    cookie_dict = json.dumps(cookie_str_to_dict(cookie_header), ensure_ascii=False)
    with DBManager() as db_manager:
        db_manager.upsert_cookie(
            site=CHITU_SITE,
            shop_name=shop_name,
            cookie_str=cookie_header,
            cookie=cookie_json,
            cookie_dict=cookie_dict,
        )
    logger.info(f"{shop_name} 赤兔 Cookie 已写入 get_cookie")


class ChituCookieAuth:
    def __init__(self, shop_name, sycm_cookie, headless=True, timeout_ms=15 * 1000):
        self.shop_name = shop_name
        self.sycm_cookie = sycm_cookie
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.authorize_locator = None

    def open(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context()
        self.context.add_cookies(load_browser_cookies(self.sycm_cookie))
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        self.page.goto(CHITU_HOME_URL, wait_until="domcontentloaded")
        self.page.locator(PROFESSION_LOGIN_XPATH).click()
        self.authorize_locator = self.page.locator(AUTHORIZE_LOGIN_XPATH)

    def authorize(self):
        if not self.authorize_locator:
            raise ChituLoginError(f"{self.shop_name} 未初始化赤兔授权入口")

        try:
            self.authorize_locator.wait_for(state="visible", timeout=self.timeout_ms)
        except PlaywrightTimeoutError as exc:
            raise ChituLoginError(f"{self.shop_name} 未检测到淘宝授权入口") from exc

        submit_button = self.page.locator(SUBMIT_LOGIN_XPATH)
        if submit_button.count():
            submit_button.click()
        else:
            self.authorize_locator.click()

        try:
            self.page.wait_for_load_state("networkidle", timeout=5 * 1000)
        except PlaywrightTimeoutError:
            logger.warning(f"{self.shop_name} 赤兔授权后网络等待超时，继续读取 Cookie")
        self.page.wait_for_timeout(2 * 1000)

    def get_chitu_cookies(self):
        return self.context.cookies(CHITU_HOME_URL)

    def close(self):
        for resource in (self.context, self.browser):
            if not resource:
                continue
            try:
                resource.close()
            except Exception as exc:
                logger.warning(f"{self.shop_name} 赤兔登录资源关闭异常: {exc}")

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as exc:
                logger.warning(f"{self.shop_name} Playwright 关闭异常: {exc}")

    def login(self):
        try:
            self.open()
            self.authorize()
            cookie_items = self.get_chitu_cookies()
        except Exception as exc:
            raise ChituLoginError(f"{self.shop_name} 赤兔授权登录失败: {exc}") from exc
        finally:
            self.close()

        cookie_header = cookiejar_to_cookie_str(cookie_items)
        if not cookie_header:
            raise ChituLoginError(f"{self.shop_name} 赤兔授权后未获取到 Cookie")
        return cookie_header, cookie_items


def get_chitu_cookie_header(shop_name, sycm_cookie=None):
    saved_cookie = fetch_cookie_header(CHITU_SITE, shop_name)
    if is_chitu_cookie_valid(saved_cookie):
        logger.info(f"{shop_name} 使用已保存的赤兔 Cookie")
        return saved_cookie

    logger.warning(f"{shop_name} 赤兔 Cookie 不存在或已失效，准备使用生意参谋 Cookie 重新授权")
    if not sycm_cookie:
        sycm_row = fetch_cookie_row(SYCM_SITE, shop_name)
        sycm_cookie = sycm_row[2] if sycm_row else None
    if not sycm_cookie:
        raise ChituLoginError(f"{shop_name} 未找到可用于赤兔授权的生意参谋 Cookie")

    cookie_header, cookie_items = ChituCookieAuth(shop_name, str(sycm_cookie)).login()
    save_chitu_cookie(shop_name, cookie_header, cookie_items)
    return cookie_header
