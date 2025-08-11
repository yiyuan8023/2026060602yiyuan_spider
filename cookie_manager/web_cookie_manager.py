import json
from playwright.sync_api import sync_playwright

from extra.database_manager import DatabaseManager


class WebCookieManager:
    def __init__(self, first_url, first_cookie_str, target_url):
        """
            初始化淘宝直播平台登录类
            Args:
                first_url (str): 初始链接
                first_cookie_str (str): 包含初始cookie的JSON字符串
        """

        self.url = first_url  # 登录页面URL，重定向到淘宝直播平台首页
        self.first_cookie = first_cookie_str  # 初始cookie字符串
        self.target_url = target_url

        self.playwright = sync_playwright().start()  # 初始化Playwright并启动浏览器
        chromium = self.playwright.chromium  # or "firefox" or "webkit".   # 使用Chromium浏览器

        # 非无头模式，可视化操作
        self.browser = chromium.launch(headless=False)

        # 浏览器上下文和页面对象（提前初始化）
        self.context = self.browser.new_context()
        self.target_page = self.context.new_page()
        self.first_page = self.context.new_page()

    def open_web(self):
        # 加载初始Cookie,并打开淘宝直播平台页面并

        # 解析并添加初始Cookie
        self.context.add_cookies(json.loads(self.first_cookie)["cookies"])

        # 访问登录页面
        self.first_page.goto(self.url)
        self.first_page.wait_for_timeout(2 * 1000)

        self.target_page.goto(self.target_url)  # 跳转到目标页面（直播概览页面）
        self.target_page.wait_for_timeout(2 * 1000)  # 等待页面加载

    def login_successfully(self):
        """
        检查登录是否成功, 通过检测页面特定元素判断是否已登录
        Returns: bool: 登录成功返回True，否则返回False
        """
        try:
            # 查找直播空间项元素，存在则表示已登录
            locator = self.target_page.locator(f"xpath=//div[@class='live-space-item']")
            if locator.count() > 0:
                return True
            else:
                # 如果未登录，尝试点击登录按钮
                elements = self.target_page.query_selector(
                    "xpath=//div[@class='fm-btn']/button[@type='submit' and text()='登录']")
                if elements:
                    elements.click()
                    self.target_page.wait_for_timeout(2 * 1000)
                    locator = self.target_page.locator(f"xpath=//div[@class='live-space-item']")
                    if locator.count() > 0:
                        return True
            return False
        except Exception as e:
            print(f"检查登录状态时出错: {e}")
            return False

    def get_new_cookies(self):
        """
        获取当前浏览器上下文中的所有Cookie
        Returns:
            list: Cookie列表
        """
        cookies = self.context.cookies()
        return cookies

    def close_web(self):
        # 关闭浏览器和Playwright资源
        self.browser.close()
        self.playwright.stop()

    def main(self):
        """
        主函数：执行登录流程并返回结果
        Returns:
            dict: 包含状态码和内容的字典
                - status: 1表示成功，2表示失败
                - content: 成功时返回Cookie列表，失败时返回错误信息
        """

        try:
            self.open_web()
            self.login_successfully()
        except Exception as e:
            print(f"执行过程中出错: {e}")
            self.close_web()
            result = {
                'status': 2,
                'content': '登录失败'
            }

        if self.login_successfully():
            cookies = self.get_new_cookies()
            self.close_web()
            result = {
                'status': 1,
                'content': cookies
            }

        else:
            self.close_web()
            result = {
                'status': 2,
                'content': '登录失败'
            }
        return result
