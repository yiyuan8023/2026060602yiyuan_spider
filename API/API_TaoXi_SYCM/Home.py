from urllib.parse import urlencode

import requests

from API.API_TaoXi_SYCM.ShengCanBase import ShengCanBaseApi
from extra.extra_reqlog import req_log

from extra.extra_date import get_second_timestamp
from config import UA


class Home(ShengCanBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def fetch_data_overview(self, day):
        """
        首页数据概览
        :return:
        """
        api = "https://sycm.taobao.com/portal/coreIndex/new/overview/v2.json?"
        params = {
            "needCycleCrc": True,
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "_": get_second_timestamp(),
            "token": self.token,
        }
        url = api + urlencode(params)
        print(url)
        res = requests.get(url, headers={"User-Agent": UA, "cookie": self.cookie})
        req_log(res)
        return res.json()
