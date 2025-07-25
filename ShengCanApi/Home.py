
from urllib.parse import urlencode

import requests

from ShengCanApi.ShengCanBase import ShengCanBaseApi

from extra_time import get_date, convert_to_timestamp
from settings import UA


class Home(ShengCanBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def fetch_data_overview(self, days=-1):
        """
        首页数据概览
        :return:
        """
        api = "https://sycm.taobao.com/portal/coreIndex/new/overview/v2.json?"
        params = {
            "needCycleCrc": True,
            "dateType": "day",
            "dateRange": f"{get_date(days)}|{get_date(days)}",
            "_": convert_to_timestamp(),
            "token": self.token
        }
        url = api + urlencode(params)
        print(url)
        res = requests.get(url, headers={
            "User-Agent": UA,
            "cookie": self.cookie})
        self.req_log(res)
        return res.json()
