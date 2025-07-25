import datetime
import re
import time
from sys import _getframe

import requests

from logger_ import logger


class ShengCanBaseApi:
    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        self.headers = {"user-agent": self.ua}
        self.token, self.userId, self.session = self.get_sycm_token()
        if not self.session and not self.token and not self.userId:
            raise Exception("cookie失效")

    def req_log(self, res: requests.models.Response):
        """
        针对request请求的response对象的日志，通配
        """
        if res.status_code == 200:
            logger.info(f"在{_getframe(1)}发起了调用,请求成功（status_code:{res.status_code}）")
            return True
        else:
            logger.error(f"在{_getframe(1)}发起了调用,请求失败（status_code:{res.status_code}）")
            return False
    def get_date(self, day=-1, date_format="%Y-%m-%d"):
        """
        获取前几天，后几天，今天日期
        """
        today = datetime.date.today()
        day_ = datetime.timedelta(days=day)
        date_ = today + day_
        return date_.strftime(date_format)
    def get_sycm_token(self):
        s = requests.Session()
        url = 'https://sycm.taobao.com/portal/home.htm'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'cookie': self.cookie,
            'referer': 'https://havanalogin.taobao.com/',
            'Host': 'sycm.taobao.com'
        }
        s.get(url=url, headers=headers)
        res = s.get(url=url, headers=headers)
        token = re.findall("legalityToken=(.*?);", res.text)
        userId = re.findall("mainUserId=(.*?);", res.text)
        if token:
            logger.success(f"SycmAPI初始化成功，token={token[0]},userId={userId[0]}")
            return token[0], userId[0], s
        else:
            logger.error("cookie已过期")
            return None, None, None
    def get_time_13(self):
        """
        获取13位的时间戳
        """
        return int(time.time() * 1000)


