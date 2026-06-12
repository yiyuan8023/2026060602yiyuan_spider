from downloader.core import Downloader
from API.API_TaoXi_SYCM.ShengCanBase import ShengCanBaseApi  # noqa
from extra.logger_ import logger

from date_utils import get_second_timestamp


class Home(ShengCanBaseApi):
    """生意参谋首页概览接口，负责按日期拉取看板摘要数据。"""

    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def fetch_data_overview(self, day):
        """
        首页数据概览
        :return:
        """
        api = "https://sycm.taobao.com/portal/coreIndex/new/overview/v2.json?"  # noqa
        params = {
            "needCycleCrc": True,
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "_": get_second_timestamp(),
            "token": self.token,
        }
        logger.info("请求生意参谋首页数据概览")
        res = Downloader(
            api=api,
            cookie=self.cookie,
            params=params,
            context="生意参谋首页数据概览",
        ).download_web()
        if not res.ok:
            return None
        return res.json()
