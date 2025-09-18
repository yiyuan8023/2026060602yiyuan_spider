import json
import sys
import requests
from API_Pdd_Base import PddBaseApi
from API_Pdd_Analyze import *
from extra.extra_reqlog import req_log
from extra.logger_ import logger
from extra.settings import UA


class PddDataCentre(PddBaseApi):
    """
    pdd商家后台，数据中心模块爬取
    """

    def __init__(self, cookie=None, shop_name=None):
        # 初始化cookie和店铺名称
        super(PddDataCentre, self).__init__()
        self.cookie = cookie
        self.shop_name = shop_name

    @logger.catch
    def service_data__after_sales_data(self, query_data: str):
        # pdd_数据中心_服务数据_售后数据

        api = "https://mms.pinduoduo.com/sydney/api/saleQuality/querySaleQualityDetailInfo"
        payload = json.dumps({
            "queryDate": query_data,
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
    def trade_data__data_overview(self, query_data: str, queryType: int):
        """
        交易数据>>数据总览
        :return:
        """
        # api = "https://mms.pinduoduo.com/sydney/api/mallInfo/queryMallDataPageOverView"
        api = "https://mms.pinduoduo.com/sydney/api/mallTrade/queryMallTradeList"
        payload = json.dumps({
            "queryType": queryType,
            "queryDate": query_data,
            "startDate": query_data,
            "endDate": query_data,
        })
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie,
            "Anti-Content": self.get_anti_content(),
            "Webspiderrule": self.get_web_spider_rule()["web_spider_rule"]
        }

        res_rule_ttf = self.get_web_spider_rule()
        ttf_url = res_rule_ttf["ttf_url"]
        font_dict = self.get_font_mapping(ttf_url)
        res = requests.post(url=api, data=payload, headers=headers)
        req_log(res)
        if res.status_code == 200:
            return res.json(), font_dict
        else:
            return None, None

    @logger.catch
    def flow_data__flow_board(self, begin_date, end_data):
        """
        流量数据>>流量看板>>统计时间
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
    def goods_data__goods_detail(self, startDate, endDate, pageNum=1):
        """
        商品数据>>商品明细
        :return:
        """
        api = "https://mms.pinduoduo.com/sydney/api/goodsDataShow/queryGoodsDetailVOListForMMS"
        payload = json.dumps(
            {"goodsId": "",
             "startDate": startDate,
             "endDate": endDate,
             "queryType": 0,
             "sortCol": 0,
             "sortType": 1,
             "pageNum": pageNum,
             "pageSize": 50,
             "actVs": 1,
             "crawlerInfo": ""
             })
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie,
            "Anti-Content": self.get_anti_content(),
            "Webspiderrule": self.get_web_spider_rule()["web_spider_rule"]
        }
        res_rule_ttf = self.get_web_spider_rule()
        ttf_url = res_rule_ttf["ttf_url"]
        font_dict = self.get_font_mapping(ttf_url)
        res = requests.post(url=api, data=payload, headers=headers)
        req_log(res)
        if res.status_code == 200:
            return res.json(), font_dict
        else:
            return None, None

    # @logger.catch
    def goods_data__goods_general_situation(self, querydate):
        """
        商品数据>>商品概况
        :return:
        """
        api = "https://mms.pinduoduo.com/sydney/api/goodsDataShow/queryGoodsPageOverView"
        payload = json.dumps({
            "queryType": 0,
            "queryDate": querydate,
            "crawlerInfo": ""

        })
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie,
            "Anti-Content": self.get_anti_content(),
            "Webspiderrule": self.get_web_spider_rule()["web_spider_rule"]
        }

        res_rule_ttf = self.get_web_spider_rule()
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
        }

        res = requests.post(url=api, data=payload, headers=headers)
        req_log(res)
        if res.status_code == 200:
            return res.json()
        else:
            return None
