import json
import sys
import requests

from API.API_Pdd.API_Pdd_Base import PddBaseApi

from extra.extra_reqlog import req_log
from extra.logger_ import logger
from extra.settings import UA


class PddDataCentre(PddBaseApi):
    # pdd商家后台，数据中心模块爬取

    def __init__(self, cookie=None, shop_name=None):
        # 初始化cookie和店铺名称
        super(PddDataCentre, self).__init__()
        self.cookie = cookie
        self.shop_name = shop_name

    @logger.catch
    def pdd_service__after_sales_data(self, date: str):
        # pdd_数据中心_服务数据_售后数据

        api = "https://mms.pinduoduo.com/sydney/api/saleQuality/querySaleQualityDetailInfo"
        payload = json.dumps({
            "queryDate": date,
            "crawlerInfo": ""
        })
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie
        }

        res = requests.post(url=api, data=payload, headers=headers)
        req_log(res)
        if res.status_code == 200:
            return res.json()
        else:
            return None

    @logger.catch
    def pdd_trade_data__data_overview(self, start_date: str, end_date: str):
        # pdd_数据中心_交易数据_数据总览
        res_rule_ttf = self.get_web_spider_rule()
        api = "https://mms.pinduoduo.com/sydney/api/mallTrade/queryMallTradeList"
        payload = json.dumps({
            "queryType": 7,  # 7 代表的是自定义日期
            "queryDate": end_date,
            "startDate": start_date,
            "endDate": end_date,
        })
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie,
            "Anti-Content": self.get_anti_content(),
            "Webspiderrule": res_rule_ttf["web_spider_rule"]  # noqa 字体
        }


        ttf_url = res_rule_ttf["ttf_url"]
        font_dict = self.get_font_mapping(ttf_url)
        res = requests.post(url=api, data=payload, headers=headers)
        req_log(res)
        if res.status_code == 200:
            return res.json(), font_dict
        else:
            return None, None

    @logger.catch
    def pdd_flow_data__flow_board(self, begin_date, end_data):
        """
        pdd_数据中心_流量数据_流量看板_数据总览_202509
       :return:
       """
        api = "https://mms.pinduoduo.com/sydney/api/mallFlow/queryMallFlowOverView"
        payload = json.dumps({
            "beginDate": begin_date,
            "crawlerInfo": "",
            "endDate": end_data
        })

        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie
        }

        res = requests.post(url=api, data=payload, headers=headers)
        req_log(res)
        if res.status_code == 200:
            return res.json()
        else:
            return None

    # @logger.catch
    def goods_data__goods_detail(self, start_date, end_date, page_num=1):

        # pdd_数据中心_商品数据_商品明细_商品明细效果
        res_rule_ttf = self.get_web_spider_rule()
        api = "https://mms.pinduoduo.com/sydney/api/goodsDataShow/queryGoodsDetailVOListForMMS"
        payload = json.dumps(
            {"goodsId": "",
             "startDate": start_date,
             "endDate": end_date,
             "queryType": 0,
             "sortCol": 0,
             "sortType": 1,
             "pageNum": page_num,
             "pageSize": 50,
             "actVs": 1,
             "crawlerInfo": ""
             })
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie,
            "Anti-Content": self.get_anti_content(),
            "Webspiderrule": res_rule_ttf["web_spider_rule"] # noqa 字体
        }

        ttf_url = res_rule_ttf["ttf_url"]
        font_dict = self.get_font_mapping(ttf_url)
        res = requests.post(url=api, data=payload, headers=headers)
        req_log(res)
        if res.status_code == 200:
            return res.json(), font_dict
        else:
            return None, None

    @logger.catch
    def goods_data__goods_general_situation(self, start_date: str, end_date: str):
        # pdd_数据中心_商品数据_商品概况
        res_rule_ttf = self.get_web_spider_rule()
        api = "https://mms.pinduoduo.com/sydney/api/goodsDataShow/queryGoodsPagePlnOstListByDate"
        payload = json.dumps({
            "queryType": 7,  # 7 代表的是自定义日期
            "queryDate": end_date,
            "startDate": start_date,
            "endDate": end_date,
        })
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie,
            "Anti-Content": self.get_anti_content(),
            "Webspiderrule": res_rule_ttf["web_spider_rule"]
        }

        ttf_url = res_rule_ttf["ttf_url"]
        font_dict = self.get_font_mapping(ttf_url)
        res = requests.post(url=api, data=payload, headers=headers)
        req_log(res)
        if res.status_code == 200:
            return res.json(), font_dict
        else:
            return None

    def goods_data__goods_general_situation_realtime(self):
        """
        商品数据>>商品概况 实时数据
        :return:
        """
        api = "https://mms.pinduoduo.com/sydney/api/goodsDataShow/queryGoodsPageOverviewForMms"
        payload = json.dumps({})
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie,
            "Anti-Content": self.get_anti_content(),
            # "cache-control": "max-age=0"
        }

        res = requests.post(url=api, data=payload, headers=headers)
        req_log(res)
        if res.status_code == 200:
            return res.json()
        else:
            return None
