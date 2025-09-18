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

    def fetch_trade_summary(self,  date):
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
        res = requests.get(url=url, headers=self.common_headers(api, host))
        req_log(res)
        return res.json()
