import io
from urllib.parse import urlencode

import numpy as np
import pandas as pd
import requests

from downloader import Downloader
from extra_time import convert_to_timestamp

from ShengCanApi.ShengCanBase import ShengCanBaseApi
from logger_ import logger
from settings import UA
from extra_date import get_millisecond_timestamp


class Goods(ShengCanBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def good_rank__all_good_day(self, day):
        """
        商品排行》》全部商品》》日》》报表
        """
        api = "https://sycm.taobao.com/cc/item/view/excel/top.json?"
        params = {
            # "dateRange": f"{get_date(days)}|{get_date(days)}",
            "dateRange": f"{day}|{day}",
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
            "User-Agent": UA,
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

    def category_360__flow_from(self, daterange, cateid):

        """
        tb_sycm_商品_品类360_流量分析_流量来源_202504
        :param daterange:
        :param cateid: 品类ID
        :return:接口返回的JSON数据或None
        """
        api = "https://sycm.taobao.com/cc/category/flow/source/overview/v3.json?"
        params = {
            "dateRange": daterange,
            "dateType": "month",
            "pageSize": 10,
            "page": 1,
            "order": "desc",
            "orderBy": "itmUv",
            "belong": "all",
            "cateId": cateid,
            "indexCode": "itmUv, itemCartByrCnt, itemCltByrCnt, payByrCnt",
            "_": get_millisecond_timestamp(),
            "token": self.token
        }

        headers = {
            "referer": f"https://sycm.taobao.com/cc/cate_archives?activeKey=flow&cateId={cateid}&dateRange={daterange}&dateType=month"
        }

        res = Downloader(self.cookie).download_web(api, params,headers=headers)
        if self.req_log(res):
            return res.json()
        else:
            return None

    def goods_360__title_drainage(self, daterange, itemId):
        """
        商品》》商品360》》标题与选词引流优化
        :return:
        """
        api = "https://sycm.taobao.com/cc/item/title/v2/word/list.json?"
        params = {
            "dateRange": daterange,
            "dateType": "day",
            "pageSize": 20,
            "page": 1,
            "order": "desc",
            "orderBy": "uv",
            "itemId": itemId,
            "device": 0,
            "kwType": "se_keyword",
            "indexCode": "uv,payOrderByrCnt,payConveRate",
            "_": convert_to_timestamp,
            "token": self.token
        }
        url = api + urlencode(params)
        headers = {
            "User-Agent": UA,
            "cookie": self.cookie,
        }
        res = requests.get(url, headers=headers)
        if self.req_log(res):
            return res.json()
        else:
            return None

    def goods_360__title_drainage_excel(self, daterange, itemId):
        """
        table_name = "tb_sycm_商品_商品360_标题优化_搜索词_202504"
        :param daterange:
        :param itemId:
        :return:
        """
        api = "https://sycm.taobao.com/cc/item/title/word/excel.json?"
        params = {
            "itemId": itemId,
            "device": 0,
            "kwType": "se_keyword",
            "dateType": "day",
            "dateRange": daterange
        }

        try:
            data = Downloader(self.cookie).download_excel(api, params)
            df = pd.read_excel(data, skiprows=5)
            if df.empty:
                return {}
            else:
                items = df.to_dict('records')
                return items
        except Exception as e:
            # logger.error(f"{res.text}")
            return None

    def recommend_analysis_single_excel(self, day):
        """
        tb_sycm_内容_渠道效果_推荐_单条效果_微详情视频_全部内容_202507

        """
        api = "https://sycm.taobao.com/s_content/recommend/analysis/single/export.json?"
        params = {
            "contentSource": "all",
            "keyword": "",
            "contentType": "minidetail",
            "dateType": "day",
            "dateRange": f"{day}|{day}"
        }
        try:
            data = Downloader(self.cookie).download_excel(api, params)
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
