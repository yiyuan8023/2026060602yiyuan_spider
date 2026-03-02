# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-04-29
# Time: 10:48
# Project: jide
# File: ChiTuBaseAPI
import json
from sys import _getframe
from urllib.parse import urlencode
import requests
from fake_useragent import UserAgent
from retrying import retry

from logger_ import logger


class InitException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"InitException: {self.message}"


class ChiTuABasePI(object):
    def __init__(self, cookie=None, shop_name=None, password=None):
        """
        初始
        :param cookie:
        """
        use_cookie = self.test_cookie(cookie)
        if not use_cookie:
            logger.error("ChiTuAPI初始化失败")
        else:
            logger.success("ChiTuAPI初始化成功")
        self.shop_name = shop_name
        self.cookie = cookie
        self.password = password

    def req_log(self, res: requests.Response):
        """
        针对resquest请求对象的log日志，通用方法
        :param res:
        :return:
        """

        if res.status_code == 200:
            logger.success(f"在{_getframe(1)}发起了调用,请求接口成功：200")
            return True
        else:
            logger.error(f"在{_getframe(1)}发起了调用,请求接口失败：{res.status_code}")
            return False

    def ramdom_ua(self):
        """
        获取随机的UA
        :return:
        """
        ua = str(UserAgent().random)
        return ua

    def test_cookie(self, cookie):
        if not cookie:
            logger.error("没有cookie,ChiTuAPI初始化失败")
            return False
        else:
            return self.fetch_user(cookie)

    def fetch_user(self, cookie):
        api = "https://kf.topchitu.com/api/user"
        headers = {"User-Agent": self.ramdom_ua(), "cookie": cookie}
        try:
            res = requests.get(api, headers=headers)
            currentUser = res.json()["currentUser"]
            if currentUser:
                return True
            else:
                logger.error("cookie失效")
                return False
        except Exception as e:
            logger.error("cookie失效")
            return False

    def __str__(self):
        return self.cookie

    def create_export(self, data):
        """
        生成报表，报表中心
        """
        api = "https://kf.topchitu.com/api/export/"
        headers = {
            "User-Agent": self.ramdom_ua(),
            "cookie": self.cookie,
            "content-type": "application/json",
        }
        res = requests.post(url=api, data=json.dumps(data), headers=headers)
        self.req_log(res)
        res_json = res.json()
        taskids = res_json["id"]
        logger.success(f"正在生成报表，taskids={taskids}")
        export_status = False
        try:
            export_status = self.export_task_status(taskids)
        except Exception as e:
            export_status = False
        finally:
            return export_status, taskids

    @retry(stop_max_attempt_number=5, wait_fixed=5000)
    def export_task_status(self, taskIds):
        """
        查看报表状态
        """
        api = "https://kf.topchitu.com/api/export/?"
        params = {"taskIds": taskIds}
        headers = {
            "User-Agent": self.ramdom_ua(),
            "cookie": self.cookie,
        }
        url = api + urlencode(params)
        res = requests.get(url=url, headers=headers)
        self.req_log(res)
        res_json = res.json()
        exportStatus = res_json[0]["exportStatus"]
        logger.success(f"报表(taskids={taskIds}),状态：{exportStatus}")
        if exportStatus == "OK":
            return True
        else:
            raise Exception(f"{exportStatus}")

    def export_download(self, taskIds):
        api = "https://kf.topchitu.com/api/export/download?"
        params = {"taskIds": taskIds, "_version": 21}
        headers = {
            "User-Agent": self.ramdom_ua(),
            "cookie": self.cookie,
        }
        url = api + urlencode(params)
        res = requests.get(url, headers=headers)
        self.req_log(res)
        return res.content

    def verify_password(self):
        """
        密码验证
        """
        api = "https://kf.topchitu.com/api/export-verify/verify-password"
        data = {"password": self.password}
        headers = {
            "User-Agent": self.ramdom_ua(),
            "cookie": self.cookie,
            "content-type": "application/json",
        }
        res = requests.post(url=api, data=json.dumps(data), headers=headers)
        if res.status_code == 200 and not res.text:
            logger.success("密码正确")
            return True
        else:
            logger.error("密码错误")
            return False

    def verify_info(self):
        """
        验证导出状态
        """
        api = "https://kf.topchitu.com/api/export-verify/export-verify-info"
        headers = {
            "User-Agent": self.ramdom_ua(),
            "cookie": self.cookie,
        }
        res = requests.get(api, headers=headers)
        self.req_log(res)
        verify_status = res.json()["exportVerifyStatus"]
        if verify_status:
            return verify_status
        else:
            return self.verify_password()


# a=ChiTuAPI("a")
# print(a.cookie)
