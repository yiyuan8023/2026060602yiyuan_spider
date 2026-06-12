# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 20:24:44
- 最近修改：2026-06-10 21:05:00
- 文件用途：负责淘系直播中控台 Cookie 获取、校验、刷新和写入 get_cookie 源表。
- 业务范围：适用于直播 API 调用前的登录态准备；优先复用 cookie 视图中的淘系直播 Cookie，失效后用生意参谋 Cookie 重新派生。
- 依赖入口：使用 Playwright、database.DBManager、cookie_manager.extra_cookie、extra.logger_ 和 TaoXiZhiBoLiveOverviewApi。
- 验收方式：修改后执行 py_compile、导入探针，并用单店铺任务验证 Cookie 复用、派生刷新和 get_cookie 写入。
- 注意事项：只读取 cookie 视图，只写 get_cookie 表；日志不得输出真实 Cookie。
"""

import json
from json import JSONDecodeError

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from cookie_manager.extra_cookie import cookie_str_to_dict, cookiejar_to_cookie_str
from database import DBManager
from date_utils import get_time_ago
from extra.logger_ import logger


ZHIBO_SITE = "淘系_直播中控台"
SYCM_SITE = "生意参谋"
LOGIN_URL = "https://login.taobao.com/havanaone/login/login.htm"
LIVE_OVERVIEW_URL = "https://liveplatform.taobao.com/restful/index/live/overview"
LIVE_SPACE_XPATH = "xpath=//div[@class='live-space-item']"
LOGIN_BUTTON_XPATH = "xpath=//div[@class='fm-btn']/button[@type='submit' and text()='登录']"


class TaoXiZhiBoLoginError(RuntimeError):
    """淘系直播登录态准备失败。"""


def load_browser_cookies(cookie_json):
    """读取可注入浏览器上下文的 Cookie 列表。"""
    try:
        cookie_payload = json.loads(cookie_json)
    except (TypeError, JSONDecodeError) as exc:
        raise TaoXiZhiBoLoginError("生意参谋 Cookie 不是有效 JSON") from exc

    cookies = cookie_payload.get("cookies")
    if not isinstance(cookies, list) or not cookies:
        raise TaoXiZhiBoLoginError("生意参谋 Cookie JSON 缺少 cookies 列表")
    return cookies


def fetch_cookie_row(site, shop_name):
    with DBManager() as db_manager:
        return db_manager.select_cookie(site, shop_name)


def fetch_cookie_header(site, shop_name):
    cookie_row = fetch_cookie_row(site, shop_name)
    return cookie_row[1] if cookie_row else None


def is_taoxi_zhibo_cookie_valid(cookie_header):
    """用直播概览轻量请求校验 Cookie 是否仍可访问直播中控台。"""
    if not cookie_header:
        return False

    from API.API_TaoXi_ZhiBo.API_TaoXi_ZhiBo_LiveOverview import (
        TaoXiZhiBoLiveOverviewApi,
    )

    try:
        stat_day = get_time_ago(1)
        response_data = TaoXiZhiBoLiveOverviewApi(cookie_header).live_overview(
            stat_day,
            stat_day,
        )
        ret = response_data.get("ret") if response_data else []
        return bool(ret and str(ret[0]).startswith("SUCCESS"))
    except Exception as exc:
        logger.warning(f"淘系直播 Cookie 校验失败: {exc}")
        return False


def save_taoxi_zhibo_cookie(shop_name, cookie_header, cookie_items):
    cookie_json = json.dumps(
        {"url": LIVE_OVERVIEW_URL, "cookies": cookie_items},
        ensure_ascii=False,
    )
    cookie_dict = json.dumps(cookie_str_to_dict(cookie_header), ensure_ascii=False)
    with DBManager() as db_manager:
        db_manager.upsert_cookie(
            site=ZHIBO_SITE,
            shop_name=shop_name,
            cookie_str=cookie_header,
            cookie=cookie_json,
            cookie_dict=cookie_dict,
        )
    logger.info(f"{shop_name} 淘系直播 Cookie 已写入 get_cookie")


class TaoXiZhiBoLogin:
    """淘宝直播中控台登录态校验和 Cookie 提取工具。"""

    def __init__(self, shop_name, source_cookie_json, headless=True, timeout_ms=15 * 1000):
        self.shop_name = shop_name
        self.source_cookie_json = source_cookie_json
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.playwright = None
        self.browser = None
        self.context = None
        self.login_page = None
        self.target_page = None

    def open_web(self):
        """加载来源 Cookie 后访问登录页和直播概览页。"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context()
        self.context.add_cookies(load_browser_cookies(self.source_cookie_json))
        self.login_page = self.context.new_page()
        self.target_page = self.context.new_page()
        self.login_page.set_default_timeout(self.timeout_ms)
        self.target_page.set_default_timeout(self.timeout_ms)

        self.login_page.goto(LOGIN_URL, wait_until="domcontentloaded")
        self.target_page.goto(LIVE_OVERVIEW_URL, wait_until="domcontentloaded")
        self.target_page.wait_for_timeout(2 * 1000)

    def login_successfully(self):
        """检测直播空间元素是否存在，存在则视为登录成功。"""
        try:
            locator = self.target_page.locator(LIVE_SPACE_XPATH)
            if locator.count() > 0:
                return True

            login_button = self.target_page.locator(LOGIN_BUTTON_XPATH)
            if login_button.count():
                login_button.click()
                self.target_page.wait_for_timeout(2 * 1000)
                return self.target_page.locator(LIVE_SPACE_XPATH).count() > 0
            return False
        except PlaywrightTimeoutError:
            logger.warning(f"{self.shop_name} 淘系直播登录态检查超时")
            return False
        except Exception as exc:
            logger.warning(f"{self.shop_name} 淘系直播登录态检查失败: {exc}")
            return False

    def get_new_cookies(self):
        """只读取直播概览页面可用 Cookie。"""
        return self.context.cookies(LIVE_OVERVIEW_URL)

    def close_web(self):
        """关闭浏览器和 Playwright 资源。"""
        for resource in (self.context, self.browser):
            if not resource:
                continue
            try:
                resource.close()
            except Exception as exc:
                logger.warning(f"{self.shop_name} 淘系直播登录资源关闭异常: {exc}")

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as exc:
                logger.warning(f"{self.shop_name} Playwright 关闭异常: {exc}")

    def login(self):
        """执行登录态检查并返回直播 Cookie header 和 Cookie 列表。"""
        try:
            self.open_web()
            if not self.login_successfully():
                raise TaoXiZhiBoLoginError(f"{self.shop_name} 淘系直播登录失败")
            cookie_items = self.get_new_cookies()
        except Exception as exc:
            raise TaoXiZhiBoLoginError(f"{self.shop_name} 淘系直播登录流程失败: {exc}") from exc
        finally:
            self.close_web()

        cookie_header = cookiejar_to_cookie_str(cookie_items)
        if not cookie_header:
            raise TaoXiZhiBoLoginError(f"{self.shop_name} 淘系直播登录后未获取到 Cookie")
        return cookie_header, cookie_items


def get_taoxi_zhibo_cookie_header(shop_name, sycm_cookie=None):
    saved_cookie = fetch_cookie_header(ZHIBO_SITE, shop_name)
    if is_taoxi_zhibo_cookie_valid(saved_cookie):
        logger.info(f"{shop_name} 使用已保存的淘系直播 Cookie")
        return saved_cookie

    logger.warning(f"{shop_name} 淘系直播 Cookie 不存在或已失效，准备使用生意参谋 Cookie 重新派生")
    if not sycm_cookie:
        sycm_row = fetch_cookie_row(SYCM_SITE, shop_name)
        sycm_cookie = sycm_row[2] if sycm_row else None
    if not sycm_cookie:
        raise TaoXiZhiBoLoginError(f"{shop_name} 未找到可用于淘系直播派生的生意参谋 Cookie")

    cookie_header, cookie_items = TaoXiZhiBoLogin(shop_name, str(sycm_cookie)).login()
    save_taoxi_zhibo_cookie(shop_name, cookie_header, cookie_items)
    return cookie_header
