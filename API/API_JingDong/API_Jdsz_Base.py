import io
import json
import os
import sys
import time
import zipfile

from requests import Response

import execjs
import requests

from extra.extra_reqlog import req_log
from extra.logger_ import logger
from extra.settings import UA

# 获取当前执行脚本的绝对路径
current_path = os.path.dirname(os.path.abspath(__file__))
js_path = os.path.join(current_path, 'uuid_.js')
js_file = open(js_path, 'r', encoding="utf8")
context = execjs.compile(js_file.read())


class CookieFailError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"CookieFailError: {self.message}"


class JdszBaseAPI:
    # 京东商智 基础模块
    def __init__(self, cookie):
        """
        初始化
        :param cookie:
        """
        self.cookie = cookie
        self.ua = UA
        if not self.test_cookie():
            logger.error("实例初始化失败")
            raise CookieFailError("初始化失败")
        else:
            logger.success("实例初始化成功")

    def fetch_basic_info(self):
        """
        账号基本信息api
        :return:
        """
        host = "https://sz.jd.com"
        api = "/sz/api/personalCenter/getBasicInforData.ajax"
        url = host + api
        res = requests.get(url=url, headers=self.common_headers(api, host))
        req_log(res)
        return res.text

    def common_headers(self, api, host):
        """
        通用的headers
        :param api:
        :param host:
        :return:
        """
        user_mnp_mup = self.fetch_user_mnp_mup(api, host, self.ua)
        logger.info(user_mnp_mup)
        common_headers = {
            "user-agent": self.ua,
            "cookie": self.cookie,
            "User-Mnp": user_mnp_mup["User-Mnp"],
            "User-Mup": str(user_mnp_mup["User-Mup"]),
            "Uuid": user_mnp_mup["Uuid"]
        }
        return common_headers

    def fetch_user_mnp_mup(self, api, host, ua):
        """
        京东商智 headers 参数加密
        """
        user_mup = int(round(time.time() * 1000))  # 生成当前时间的毫秒级时间戳

        uuid = context.call('n', api, host, ua, self.cookie)  # 调用js函数 n 来生成UUID
        aa = api + uuid + str(user_mup) + "372ad2c2b6"  # 生成User-Mnp的参数
        user_mnp = context.call('createHash', aa)  # 调用js函数 createHash 来生成User-Mnp
        return {
            "User-Mnp": user_mnp,
            "User-Mup": user_mup,
            "Uuid": uuid,
        }

    def test_cookie(self):
        """
        测试cookie
        :return:
        """
        res_text = self.fetch_basic_info()
        try:
            res_json = json.loads(res_text)
        except:
            logger.error(f"cookie为空或者已失效")
            return False
        if res_json.get("message") == "成功":
            logger.success(f"账号基本信息:{res_json}")
            return True
        else:
            logger.error(res_json)
            return False

    def read_res_zip(self, res: Response):
        """
        :param res:
        :return:返回zip里面的文件第一个吃的bytes
        """
        with zipfile.ZipFile(io.BytesIO(res.content), 'r') as zip_ref:
            # 获取 ZIP 文件中的所有文件名
            filenames = zip_ref.namelist()
            # 只处理第一个文件
            first_excel_file = filenames[0]
            return zip_ref.open(first_excel_file)

    @staticmethod
    def title_index_to_data(title_index, values):
        """
        将标题索引和对应的值关联起来
        """
        items = []
        for value in values:
            result = {}
            for title, index in title_index.items():
                if index < len(value):
                    result[title] = value[index]
                else:
                    result[title] = None  # 如果索引超出范围，设为None
            items.append( result)
        return items
