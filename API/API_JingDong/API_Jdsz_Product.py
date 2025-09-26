import json
from urllib.parse import urlencode
import requests

from API.API_JingDong.API_Jdsz_Base import JdszBaseAPI
from extra.extra_reqlog import req_log


class JdSzProductAPI(JdszBaseAPI):
    # 京东商智》》商品
    def __init__(self, cookie):
        # 初始化cookie和店铺名称
        super().__init__(cookie)

    def fetch_product_analysis__category_analysis(self, date):
        # jd_jdsz_商品_类目分析_行业类目

        host = "https://szgateway.jd.com"
        api = f"/szpaas/szajax/category/getOfflineCategorySummary.ajax"  # noqa
        params = {
            "dateType": "day",
            "date": date,
            "startDate": date,
            "endDate": date,
            "categoryType": "1"
        }
        url = host + api + "?" + urlencode(params)
        headers = self.common_headers(api, host)
        headers["referer"] = "https://sz.jd.com/szweb/sz/view/productAnalysis/categoryAnalysis.html"
        res = requests.get(url=url, headers=headers)
        req_log(res)
        return res.json()

    def fetch_product_analysis__product_detail(self, date, type="0"):
        """
        jd_jdsz_商品_商品明细》spu&sku
        type=0：spu
        type=1：sku
        :return:
        """
        host = "https://sz.jd.com"
        api = "/sz/api/productDetail/getProductList.ajax"
        params = {
            "date": date,
            "startDate": date,
            "endDate": date,
            "type": type,
            "compareType": "hb",
            "categoryType": "0",
            "second": "999999",
            "third": "",
            "channel": "99"
        }
        url = host + api + "?" + urlencode(params)
        headers = self.common_headers(api, host)
        res = requests.get(url=url, headers=headers)
        req_log(res)
        return res.json()

    def fetch_trade_summary(self, date):
        # jd_jdsz_交易_交易概况_全部渠道

        host = "https://sz.jd.com"
        api = "/sz/api/trade/getSummaryData.ajax"
        params = {
            "channel": "99",
            "cmpType": "0",
            "date": date,
            "endDate": date,
            "startDate": date
        }
        url = host + api + "?" + urlencode(params)
        headers = self.common_headers(api, host)
        res = requests.get(url=url, headers=headers)
        req_log(res)
        return res.json()

    def fetch_service_analysis__after_sale_service(self, date):
        """
        jd_jdsz_服务_服务分析_售后服务单量
        服务分析》》服务分析》》售后服务单量&服务核心指标
        :return:
        """
        host = "https://sz.jd.com"
        api = "/sz/api/serviceAnalysis/getSummaryData.ajax"
        params = {
            "date": date,
            "endDate": date,
            "startDate": date
        }
        url = host + api + "?" + urlencode(params)
        headers = self.common_headers(api, host)
        res = requests.get(url=url, headers=headers)
        req_log(res)
        # print(res.json())
        return res.json()

    def fetch_fans_summary__data_summary(self, date):
        """
        jd_jdsz_客户_关注店铺用户概况_数据概览
        :return:
        """
        host = "https://sz.jd.com"
        api = "/sz/api/cust/fansSummary/detail.ajax"
        params = {
            "date": date,
            "startDate": date,
            "endDate": date
        }
        url = host + api + "?" + urlencode(params)
        headers = self.common_headers(api, host)
        res = requests.get(url=url, headers=headers)
        req_log(res)
        # print(res.json())
        return res.json()

    def szpaas_lowcode_szajax_query_memberoverview(self, date):
        """
        jd_jdsz_客户_品牌会员_会员概况_开卡会员_202509
        :return:
        """
        host = "https://szgateway.jd.com"
        api = "/szpaas/lowcode/szajax/query/memberOverview.ajax" # NOQA
        user_mnp_mup = self.fetch_user_mnp_mup(api, host, self.ua)
        params = {
            "User-mup": str(user_mnp_mup["User-Mup"]),
            "User-mnp": user_mnp_mup["User-Mnp"],
            "uuid": user_mnp_mup["Uuid"]
        }

        payload = json.dumps({
            "filterList": [
                {
                    "propertyName": "dt",
                    "values": [date],
                    "op": ">=",
                    "type": "string"
                },
                {
                    "propertyName": "dt",
                    "values": [date],
                    "op": "<=",
                    "type": "string"
                },
                {
                    "propertyName": "time_interval",
                    "values": ["BY_DAY"],
                    "op": "=",
                    "type": "string"
                }
            ],
            "dimList": ["dt","time_interval"],
            "metricList": [
                "jdr_sch_user_authentication_member_shop_cnt_shopversion_brandmem@date_end&brandmem_card",
                "jdr_sch_user_authentication_member_shop_cnt_shopversion_brandmem_increase@brandmem_card",
                "jdr_sch_user_open_member_shop_cnt_shopversion_brandmem@brandmem_card",
                "jdr_sch_user_invalid_member_shop_cnt_shopversion_brandmem@brandmem_card",
                "jdr_sch_user_authentication_member_shop_cnt_shopversion_brandmem_client@brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz@brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_dis_qtty_shopversion_brandmem_sz@brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_amt_shopversion_brandmem_sz@brandmem_card",
                "jdr_sch_mkt_brow_shop_cnt_shopversion_brandmem_sz@brandmem_card&browse_brand",
                "jdr_sch_mkt_brow_shop_qtty_shopversion_brandmem_sz@brandmem_card&browse_brand",
                "jdr_sch_mkt_brow_sku_qtty_shopversion_brandmem_sz@brandmem_card&browse_brand",
                "jdr_sch_user_follow_sku_sku_qtty_shopversion_brandmem@brandmem_card&follow_brand",
                "jdr_sch_mkt_brow_shop_cnt_shopversion_brandmem_sz@brandmem_card&add_cart",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_ld30_rebuy_brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_brandmem_card_ld30",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_rebuy_90d_brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_brandmem_card_90d"
            ],
            "groupList": [],
            "attributeList": [],
            "commonParam": {
                "platformId": 0,
                "userErp": "",
                "period": 0,
                "startTime": 0,
                "endTime": 0,
                "indexFreq": "OFFLINE",
                "description": "开卡会员数据概览指标数据集-指标服务1",
                "annotation": "基础",
                "page": -1,
                "pageSize": 100,
                "resAppKey": "lowcode2772",
                "traceId": params["uuid"],
                "date": date,
                "startDate": date,
                "endDate": date,
                "dateType": "day"
            }
        })
        headers = {
            'User-Agent': self.ua,
            'Referer': 'https://sz.jd.com/szweb/sz/view/brandMember/memberOverview.html',
            'Cookie': self.cookie,
            'Content-Type': 'application/json'
        }

        url = host + api + "?" + urlencode(params)
        res = requests.post(url=url, headers=headers, data=payload)
        req_log(res)
        return res.json()

