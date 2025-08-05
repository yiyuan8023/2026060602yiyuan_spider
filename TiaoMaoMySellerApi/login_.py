# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-07-17
# Time: 11:03
# Project: jide
# File: login_
import json
from playwright.sync_api import sync_playwright

class ZBZKTCookies():
    def __init__(self, username, password):
        self.url = 'https://login.taobao.com/havanaone/login/login.htm?bizName=taobao&sub=true&redirectURL=https%3A%2F%2Fliveplatform.taobao.com%2Frestful%2Findex%2Fhome%2Fdashboard-new'
        self.playwright = sync_playwright().start()
        chromium = self.playwright.chromium  # or "firefox" or "webkit".
        self.browser = chromium.launch(headless=False)
        self.username = username
        self.first_cookie = password

    def open(self):
        self.context = self.browser.new_context()
        # a=
        # print(a)
        # aa=[]
        # for i in a:
        #     if i["domain"]=='.taobao.com':
        #         aa.append(i)
        self.context.add_cookies(json.loads(self.first_cookie)["cookies"])

        self.page2 = self.context.new_page()
        self.page2.goto(self.url)
        self.page2.wait_for_timeout(2 * 1000)
        self.page=self.context.new_page()
        self.page.goto("https://liveplatform.taobao.com/restful/index/live/overview")
        # other actions...
        self.page.wait_for_timeout(2 * 1000)

    def login_successfully(self):
        try:
            locator = self.page.locator(f"xpath=//div[@class='live-space-item']")
            if locator.count()>0:
                return True
            else:
                elements = self.page.query_selector("xpath=//div[@class='fm-btn']/button[@type='submit' and text()='登录']")
                elements.click()
                self.page.wait_for_timeout(2 * 1000)
                locator = self.page.locator(f"xpath=//div[@class='live-space-item']")
                if locator.count() > 0:
                    return True
        except:
            return False

    def get_cookies(self):
        cookies = self.context.cookies()
        return cookies
    def close(self):
        self.browser.close()
        self.playwright.stop()
    def main(self):
        """
        破解入口
        :return:
        """
        try:
            self.open()
            self.login_successfully()
        except Exception as e:
            print(e)
            self.close()
            return {
                'status': 2,
                'content': '登录失败'
            }
        if self.login_successfully():
            cookies = self.get_cookies()
            self.close()
            return {
                'status': 1,
                'content': cookies
            }
        else:
            self.close()
            return {
                'status': 2,
                'content': '登录失败'
            }
if __name__ == '__main__':
    result = ZBZKTCookies('美心官方旗舰店:一元', '{"url": "https://sycm.taobao.com/portal/home.htm", "cookies": [{"name": "_samesite_flag_", "value": "true", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": null}, {"name": "cookie2", "value": "13fd3bf698a30c68bfd381ecf9c67ebb", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": null}, {"name": "t", "value": "2e04c38d0fd7c848cfba101281a8d4c9", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/10/19 09:07:41"}, {"name": "_tb_token_", "value": "5be3bf1e33f13", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "xlly_s", "value": "1", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/7/24 01:06:44"}, {"name": "unb", "value": "2208167046031", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": null}, {"name": "sn", "value": "%E5%B0%8F%E5%90%89%E6%97%97%E8%88%B0%E5%BA%97%3Axj", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "cancelledSubSites", "value": "empty", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "_euacm_ac_l_uid_", "value": "2208167046031", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/7/22 01:07:57"}, {"name": "2208167046031_euacm_ac_c_uid_", "value": "2670540851", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/7/22 01:07:57"}, {"name": "2208167046031_euacm_ac_rs_uid_", "value": "2670540851", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/7/22 01:07:57"}, {"name": "_portal_version_", "value": "new", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/7/22 01:07:57"}, {"name": "cc_gray", "value": "1", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/7/28 01:07:57"}, {"name": "XSRF-TOKEN", "value": "395e7bdf-8bd4-4838-9513-049d4c1dd7dc", "domain": "sycm.taobao.com", "path": "/", "secure": false, "httpOnly": true, "expirationDate": null}, {"name": "_euacm_ac_rs_sid_", "value": "null", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2025/7/22 01:08:08"}, {"name": "x_one_bi_token", "value": "one-bi-ffb5af5263254d48aba8eaa492cdf718-2670540851-2208167046031", "domain": ".sycm.taobao.com", "path": "/", "secure": false, "httpOnly": true, "expirationDate": "2026/7/21 01:07:59"}, {"name": "3PcFlag", "value": "1753060056001", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/7/31 09:07:35"}, {"name": "x5sec", "value": "7b2274223a313735333036303036312c22733b32223a2233656132663864353462636236363232222c22617365727665723b33223a22307c434e756c39734d47454c476e677533362f2f2f2f2f774561447a49794d4467784e6a63774e4459774d7a45374d544330684f6e5142673d3d227d", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/7/21 01:37:39"}, {"name": "sgcookie", "value": "E100a2lVJn3ItcKqDKzQqHTppuZijj%2Fvubici5I9niXZxYK64OwpDKSD7QcDDfTL9e9VKNOPo82TseNjUfN7rWXgocAnDihenwksXewVCqMFG%2B%2FJEo15QS9RpfTtjvS3raGs", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": "2026/7/21 09:07:41"}, {"name": "uc1", "value": "cookie21=UIHiLt3xSalX&cookie14=UoYbyGyaVY0qpA%3D%3D", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "csg", "value": "cd150c98", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": null}, {"name": "skt", "value": "422577e684fdd8c1", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": true, "expirationDate": null}, {"name": "_cc_", "value": "W5iHLLyFfA%3D%3D", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2026/7/21 09:07:41"}, {"name": "_m_h5_tk", "value": "b90d3fa6e77db8db89c35eb5187361ff_1753069427966", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/7/21 02:37:47"}, {"name": "_m_h5_tk_enc", "value": "bcda55a9dc7889ae9cf6feb2ba9489fd", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2025/7/21 02:37:47"}, {"name": "cna", "value": "o4AEIarrWT4CAXjHRMKP6Vla", "domain": ".taobao.com", "path": "/", "secure": true, "httpOnly": false, "expirationDate": "2026/8/25 01:07:57"}, {"name": "tfstk", "value": "gJIxHQXqQ7VDj3IvEtzoIzEELFylbzXqwsWIjCAm5_CRCtIDoOOMX1CO6IY_gnjOwO5yIc4Vs_HON_QD5GAGXxSR9cm0grWsXhx_tWq3xtJ2bhNn6Sk6PIJNFCwklqtMZWx_tWqorYT4ih1goenl2TOyBmi6l1gWPpRWCqt11QTWdpcXf116VL9HdVO65E97VQJ6fC16f8BWadK61v0L6QMXscQAT8hlircSADsJHEdKjQntXRvvkB6XwWNC2kLvOtO-jSv_gJO9aMNuyT75lsvP6kFJmwXhbesjN-vfJOjp-UGoy1-vB9-PAW0MrNBffUQzAfpV5tjO5T2K8p75gi79vAZfendvRK88AcCB5pBe4MNnSUbOhGTRzWgHOgW5-NC0acOcJT1J-gcoxnbhKG8CcjIzMMjdmqGH9d0be83Z7E9zb_3whEhGVRvJt-Et7V8zULd3ey3Z7E9yeB2YMVuwz85..", "domain": ".taobao.com", "path": "/", "secure": false, "httpOnly": false, "expirationDate": "2026/1/17 01:06:54"}, {"name": "JSESSIONID", "value": "6A5F4D52D79C0C1BE1873BFB193FEA2E", "domain": "sycm.taobao.com", "path": "/", "secure": false, "httpOnly": true, "expirationDate": null}]}')
    a=result.main()
    # cookiejar_to_cookie_str()
    print(a)