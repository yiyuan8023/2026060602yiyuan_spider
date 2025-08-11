import json
from playwright.sync_api import sync_playwright


class ZBZKTCookies:

    def __init__(self, shop_name, first_cookie_str):
        """
            初始化淘宝直播平台登录类
            Args:
                shop_name (str): 用户名
                first_cookie_str (str): 包含初始cookie的JSON字符串
        """  # noqa
        # 登录页面URL，重定向到淘宝直播平台首页
        # self.url = (f'https://login.taobao.com/havanaone/login/login.htm?bizName=taobao&sub=true&redirectURL=https%3A%2F%2Fliveplatform.taobao.com%2Frestful%2Findex%2Fhome%2Fdashboard-new')  # noqa
        self.url = (f'https://login.taobao.com/havanaone/login/login.htm')  # noqa

        # 初始化Playwright并启动浏览器
        self.playwright = sync_playwright().start()
        # 使用Chromium浏览器
        chromium = self.playwright.chromium  # or "firefox" or "webkit".
        # 非无头模式，可视化操作
        self.browser = chromium.launch(headless=False)
        self.username = shop_name
        # 初始cookie字符串
        self.first_cookie = first_cookie_str

        # 浏览器上下文和页面对象（提前初始化）
        self.context = self.browser.new_context()
        self.page2 = self.context.new_page()
        self.page = self.context.new_page()

    def open_web(self):
        # 打开淘宝直播平台页面并加载初始Cookie

        # 解析并添加初始Cookie
        self.context.add_cookies(json.loads(self.first_cookie)["cookies"])

        # 访问登录页面
        self.page2.goto(self.url)
        self.page2.wait_for_timeout(2 * 1000)

        # 跳转到直播概览页面
        self.page.goto("https://liveplatform.taobao.com/restful/index/live/overview")
        # 等待页面加载
        self.page.wait_for_timeout(2 * 1000)

    def login_successfully(self):
        """
        检查登录是否成功, 通过检测页面特定元素判断是否已登录
        Returns: bool: 登录成功返回True，否则返回False
        """
        try:
            # 查找直播空间项元素，存在则表示已登录
            locator = self.page.locator(f"xpath=//div[@class='live-space-item']")
            if locator.count() > 0:
                return True
            else:
                # 如果未登录，尝试点击登录按钮
                elements = self.page.query_selector(
                    "xpath=//div[@class='fm-btn']/button[@type='submit' and text()='登录']")
                if elements:
                    elements.click()
                    self.page.wait_for_timeout(2 * 1000)
                    locator = self.page.locator(f"xpath=//div[@class='live-space-item']")
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
            return {
                'status': 2,
                'content': '登录失败'
            }
        if self.login_successfully():
            cookies = self.get_new_cookies()
            self.close_web()
            return {
                'status': 1,
                'content': cookies
            }
        else:
            self.close_web()
            return {
                'status': 2,
                'content': '登录失败'
            }


if __name__ == '__main__':
    result = ZBZKTCookies('林内官方旗舰店:一元',
                          '{"url": "https://sycm.taobao.com/portal/home.htm", "cookies": [{"name": "_samesite_flag_", "value": "true", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": null}, {"name": "cookie2", "value": "14f791849aa07d80ce1e679a4a6b3869", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": null}, {"name": "t", "value": "9d7ee9075efdd7adedd556d191cc5e02", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/11/6 06:24:53"}, {"name": "_tb_token_", "value": "77abeeeb5f3b", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "3PcFlag", "value": "1754605463949", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/8/18 06:24:24"}, {"name": "xlly_s", "value": "1", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/8/10 22:24:33"}, {"name": "unb", "value": "2212151220659", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": null}, {"name": "sn", "value": "%E6%9E%97%E5%86%85%E4%BC%81%E4%B8%9A%E5%BA%97%3A%E4%B8%80%E5%85%83", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "uc1", "value": "cookie14=UoYbz91WHE8Jrw%3D%3D&cookie21=URm48syIZx9a", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "csg", "value": "c6776ab2", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "_cc_", "value": "Vq8l%2BKCLiw%3D%3D", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2026/8/8 06:24:53"}, {"name": "cancelledSubSites", "value": "empty", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "skt", "value": "b8b6d4f35ae8c5be", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": null}, {"name": "sgcookie", "value": "E100Hf4niNiA19N%2FWjHZ4lzzAAht0sJn3RDMasase7HgISDQVx2ga4sulV14n%2F5GLFaVDYFmXRmYK87FHKUV70jYi29VTqQyCW4gyAiIDJ8pj8wJ9XDmAWlnlxe81m0t52bg", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": "2026/8/8 06:24:53"}, {"name": "_m_h5_tk", "value": "7e82df725c794cb37b34d500aa466679_1754614134944", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/8/7 23:54:54"}, {"name": "_m_h5_tk_enc", "value": "0d6dbf5a140bc3a4a6b79845920f4ab5", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/8/7 23:54:54"}, {"name": "_euacm_ac_l_uid_", "value": "2212151220659", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/8/8 22:25:23"}, {"name": "2212151220659_euacm_ac_c_uid_", "value": "3830928885", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/8/8 22:25:23"}, {"name": "2212151220659_euacm_ac_rs_uid_", "value": "3830928885", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/8/8 22:25:23"}, {"name": "_portal_version_", "value": "new", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/8/8 22:25:23"}, {"name": "cc_gray", "value": "1", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/8/14 22:25:23"}, {"name": "XSRF-TOKEN", "value": "f5be6f5b-d1b7-4759-bb38-76f2d30ba2db", "domain": "sycm.taobao.com", "path": "/", "secure": false, "httpOnly": true, "expirationDate": null}, {"name": "cna", "value": "mBUcIQMSGCACAXrgmQJLJ0Pk", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2026/9/11 22:25:25"}, {"name": "_euacm_ac_rs_sid_", "value": "null", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/8/8 22:25:27"}, {"name": "x_one_bi_token", "value": "one-bi-ebbe29d1f35947aaaddfbccaf03efd27-3830928885-2212151220659", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": true, "expirationDate": "2026/8/7 22:25:25"}, {"name": "JSESSIONID", "value": "8CAB607544131C89151B80C55546AD63", "domain": "sycm.taobao.com", "path": "/", "secure": false, "httpOnly": true, "expirationDate": null}, {"name": "tfstk", "value": "gcfmHJcWftJf0PEJe_ObhWCrrZy-4IO6AGh9XCKaU3-SMqEfkTYNXga_lIQwjGjJVhKvBhdgS3S2DKUf7VYN2IJ1HhKvjCb1xzEL9WQflCOLvkFKHEXehCta6CyJa7yOCTrL9WQ43EOOzkC9r0Vp2FRwun-2zzY95c8NbKPza3T67m8Zgz4kVElqufkVz08X-C-NbCzlz3Tw_ESw_f5m_HfNN_rgFWiM_hANZEvDYZ2I_ffo9KxFu3caY_Y0fH72qfl9xu8-SabYmX_JGsIHJiFriMbVLGWFPlcH09QCJhJqJXpRUi1kETnq3eADmp52h2a9GdWlZIC4fv_RrnJHwTe7Dddcm9tB38Z5jaxAbsvrmuKOpaC2EMr-ZG9G3iYyTgRqUvJy9fTzW_ksCK8WrHd1g1cPWQtLsz4od-92PEELrzDsCK8WrHUurvi63UTYv", "domain": ".taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2026/2/3 22:25:25"}]}')

    a = result.main()
    # cookiejar_to_cookie_str()
    print(a)
