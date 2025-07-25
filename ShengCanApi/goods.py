import io
from urllib.parse import urlencode

import numpy as np
import pandas as pd
import requests


from ShengCanApi.ShengCanBase import ShengCanBaseApi
from logger_ import logger


class Goods(ShengCanBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def good_rank__all_good_day(self, days: int = -1):
        """
        商品排行》》全部商品》》日》》报表
        """
        api = "https://sycm.taobao.com/cc/item/view/excel/top.json?"
        params = {
            "dateRange": f"{self.get_date(days)}|{self.get_date(days)}",
            "dateType": "day",
            "pageSize": 10,
            "page": 1,
            "order": "desc",
            "orderBy": "payAmt",
            "dtUpdateTime": False,
            "dtMaxAge": 0,
            "device": 0,
            "compareType": "cycle",
            "keyword": "",
            "follow": False,
            "cateId": "",
            "cateLevel": "",
            "indexCode": "payAmt, sucRefundAmt, payItmCnt, payByrCnt, payRate, newPayByrCnt, payOldByrCnt, olderPayAmt, juPayAmt, mtdPayAmt, mtdPayItmCnt, ytdPayAmt, itemStatus, itemCartCnt, itemCartByrCnt, itemCltByrCnt, visitCartRate, visitCltRate, itmUv, itmPv, itmStayTime, itmBounceRate, seGuideUv, seGuidePayByrCnt, seGuidePayRate, uvAvgValue, starLevel001, itemUnitPrice1"
        }
        url = api + urlencode(params)
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "cookie": self.cookie})
        self.req_log(res)
        try:
            data = io.BytesIO(res.content)
            df = pd.read_excel(data, skiprows=4, engine='xlrd')
            if df.empty:
                return {}
            else:
                items = df.to_dict('records')
                return items
        except Exception as e:
            logger.warning(f"{e.args}")
            raise e

    def category_360__flow_from(self, dateRange, cateId):
        """
        商品》》品类360》》流量来源
        :param dateRange:
        :return:
        """
        api = "https://sycm.taobao.com/cc/category/flow/source/overview/v3.json?"
        params = {
            "dateRange": dateRange,
            "dateType": "month",
            "pageSize": 10,
            "page": 1,
            "order": "desc",
            "orderBy": "itmUv",
            "belong": "all",
            "cateId": cateId,
            "indexCode": "itmUv, itemCartByrCnt, itemCltByrCnt, payByrCnt",
            "_": self.get_time_13(),
            "token": self.token
        }
        url = api + urlencode(params)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "cookie": self.cookie,
            "referer": f"https://sycm.taobao.com/cc/cate_archives?activeKey=flow&cateId={cateId}&dateRange={dateRange}&dateType=month"
        }
        res = requests.get(url, headers=headers)
        if self.req_log(res):
            return res.json()
        else:
            return None

    def goods_360__title_drainage(self, dateRange, itemId):
        """
        商品》》商品360》》标题与选词引流优化
        :return:
        """
        api = "https://sycm.taobao.com/cc/item/title/v2/word/list.json?"
        params = {
            "dateRange": dateRange,
            "dateType": "day",
            "pageSize": 20,
            "page": 1,
            "order": "desc",
            "orderBy": "uv",
            "itemId": itemId,
            "device": 0,
            "kwType": "se_keyword",
            "indexCode": "uv,payOrderByrCnt,payConveRate",
            "_": self.get_time_13(),
            "token": self.token
        }
        url = api + urlencode(params)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "cookie": self.cookie,
        }
        res = requests.get(url, headers=headers)
        if self.req_log(res):
            return res.json()
        else:
            return None

    def goods_360__title_drainage_excel(self, dateRange, itemId):
        """

        :param dateRange:
        :param itemId:
        :return:
        """
        api = "https://sycm.taobao.com/cc/item/title/word/excel.json?"
        params = {
            "itemId": itemId,
            "device": 0,
            "kwType": "se_keyword",
            "dateType": "day",
            "dateRange": dateRange
        }
        url = api + urlencode(params)
        # print(url)
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "cookie": self.cookie})
        self.req_log(res)
        try:
            data = io.BytesIO(res.content)
            df = pd.read_excel(data, skiprows=5)
            if df.empty:
                return {}
            else:
                items = df.to_dict('records')
                return items
        except Exception as e:
            # logger.error(f"{res.text}")
            return None


    def recommend_analysis_single_excel(self,dateRange):
        """
        商品《《单条效果
        :param dateRange:
        :return:
        """

        api = "https://sycm.taobao.com/s_content/recommend/analysis/single/export.json?"
        params = {
            "contentSource": "all",
            "keyword": "",
            "contentType": "minidetail",
            "dateType": "day",
            "dateRange": dateRange
        }
        url = api + urlencode(params)
        # print(url)
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "cookie": self.cookie})
        self.req_log(res)
        try:
            data = io.BytesIO(res.content)
            df = pd.read_excel(data, skiprows=5)
            df.replace({np.nan: ''}, inplace=True)
            if df.empty:
                return {}
            else:
                items = df.to_dict('records')
                return items
        except Exception as e:
            # logger.error(f"{res.text}")
            return None
