# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-04-16
# Time: 17:07
# Project: jide
# File: Home
import io
import time
from urllib.parse import urlencode

import requests

from ShengCanApi.ShengCanBase import ShengCanBaseApi


class Home(ShengCanBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie
    def fetch_data_overview(self,days=-1):
        """
        首页数据概览
        :return:
        """
        api = "https://sycm.taobao.com/portal/coreIndex/new/overview/v2.json?"
        params = {
            "needCycleCrc": True,
            "dateType": "day",
            "dateRange": f"{self.get_date(days)}|{self.get_date(days)}",
            "_": self.get_time_13(),
            "token":self.token
        }
        url = api + urlencode(params)
        print(url)
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "cookie": self.cookie})
        self.req_log(res)
        return res.json()