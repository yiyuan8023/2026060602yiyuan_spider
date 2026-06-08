import json
import time
from urllib.parse import urlencode
from tenacity import retry, stop_after_attempt, wait_fixed
import requests
from extra.extra_reqlog import req_log
from config import UA

from API.API_TaoXi_SYCM.ShengCanBase import ShengCanBaseApi
from downloader.core import Downloader


class SelfAnalysis(ShengCanBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    # stop_after_attempt(5)：最多重试 5 次（包括首次尝试）
    # wait_fixed(3)：每次重试之间等待 3 毫秒
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(3))
    def create_report(self, shop_id, start_date, end_date):
        # 【商品-流量来源】创建报表,获取报表id
        url = "https://sycm.taobao.com/lyone/fetchData/createReport.json"
        data = {
            "datasource": "电商后台",
            "channelName": "天猫淘宝",
            "dataPlatform": "生意参谋",
            "shopIds": [shop_id],  # 不同店铺id不同
            # "shopIds": ["20893"],  # 不同店铺id不同
            "dataType": "商品",
            "dataDimension": "流量来源",
            "dateType": "day",
            "isAutoUpdate": "0",
            "indicators": [
                "item_id",
                "item_name",
                "parent_src_name",
                "src_name",
                "src_level",
                "own_principle",
                "ipv_uv_1d_111",
                "ipv_1d_058",
                "crt_ord_byr_cnt_1d_026",
                "pay_ord_byr_cnt_1d_053",
                "ord_rate",
                "pay_ord_amt_1d_058",
                "clt_byr_cnt_1d_113",
                "pay_rate",
                "cart_byr_cnt_1d_018",
                "pay_ord_itm_qty_1d_012",
                "pay_ord_byr_cnt_1d_1049",
                "pay_ord_byr_cnt_1d_1050",
                "pay_ord_byr_cnt_1d_1051",
                "pay_ord_byr_cnt_1d_1052",
                "jp_uv_1d_005",
                "jp_uv_1d_006",
            ],
            "isDataFormat": "Y",
            "reportName": f"spider_{int(time.time()) * 1000}",
            "itemIds": [],
            "customFilters": {
                "pay_ord_amt_1d_059": [
                    "pay_ord_amt_1d_059 = 0",
                    "pay_ord_amt_1d_059 > 0",
                ],
                "ipv_uv_1d_111": ["ipv_uv_1d_111 = 0", "ipv_uv_1d_111 > 0"],
            },
            "dims": {"own_principle": ["all"]},
            "startDate": start_date,
            "endDate": end_date,
            # "id": "4430230"
        }
        headers = {"content-type": "application/json;charset=UTF-8"}

        res = Downloader(
            api=url, method="post", headers=headers, cookie=self.cookie, json_data=data
        ).download_web()
        if req_log(res):
            res_json = res.json()
            # print(res_json)
            return res_json["data"]["id"]
        else:
            return None

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(3))
    def create_report2(self, start_date, end_date):
        url = "https://sycm.taobao.com/lyone/fetchData/createReport.json"
        data = {
            "datasource": "电商后台",
            "channelName": "天猫淘宝",
            "dataPlatform": "生意参谋",
            "shopIds": ["20805"],
            "dataType": "店铺",
            "dataDimension": "流量来源详情",
            "dateType": "day",
            "isAutoUpdate": "0",
            "indicators": [
                "src_name",
                "src_detail",
                "own_principle",
                "uv_1d_030",
                "uv_1d_642",
                "crt_ord_byr_cnt_1d_026",
                "ord_rate",
                "crt_ord_vld_amt_1d_014",
                "pay_ord_byr_cnt_1d_053",
                "pay_rate",
                "pbt_amt",
                "uv_value",
                "pay_ord_amt_1d_059",
                "clt_byr_cnt_1d_108",
                "clt_byr_cnt_1d_113",
                "cart_byr_cnt_1d_018",
                "pay_ord_byr_cnt_1d_1049",
                "pay_ord_byr_cnt_1d_1050",
                "pay_ord_byr_cnt_1d_1051",
                "pay_ord_byr_cnt_1d_1052",
            ],
            "isDataFormat": "Y",
            "reportName": f"spider_v2_{int(time.time()) * 1000}",
            "dims": {
                "src_name": ["关键词推广(原直通车)", "手淘搜索", "关键词推广"],
                "own_principle": ["all", "farthest", "nearest"],
            },
            "startDate": start_date,
            "endDate": end_date,
        }

        res = requests.post(
            url,
            headers={
                "User-Agent": UA,
                "cookie": self.cookie,
                "content-type": "application/json;charset=UTF-8",
            },
            data=json.dumps(data),
        )
        if req_log(res):
            res_json = res.json()
            # print(res_json)
            return res_json["data"]["id"]
        else:
            return None

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(3))
    def fetch_data_download(self, report_id):
        api = "https://sycm.taobao.com/lyone/fetchData/download.json?"
        params = {
            "reportId": report_id,
        }
        url = api + urlencode(params)
        res = requests.get(
            url,
            headers={
                "User-Agent": UA,
                "cookie": self.cookie,
                "refer": f"https://sycm.taobao.com/lyone/auto_analysis/datafetch/report_generation?insertType=sycm&layoutHide=1&useDebug=false&reportId={report_id}&type=create",
            },
        )
        if req_log(res):
            res_json = res.json()
            # print(res_json)
            return True
        else:
            return False

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(3))
    def query_download_url(self, report_id):
        # 获取下载地址链接
        api = "https://sycm.taobao.com/lyone/fetchData/queryDownloadUrl.json?"
        params = {
            "reportId": report_id,
        }
        headers = {
            "refer": f"https://sycm.taobao.com/lyone/auto_analysis/datafetch/report_generation?"
            f"insertType=sycm&layoutHide=1&useDebug=false&reportId={report_id}&type=create"
        }
        res = Downloader(
            api=api, params=params, headers=headers, cookie=self.cookie
        ).download_web()

        if req_log(res):
            res_json = res.json()
            # print(res_json)
            data = res_json["data"]
            status = data["status"]
            if status == "2":
                print("下载任务已提交，请等待数据处理")
                return None
            elif status == "1":
                url = data["url"]
                return url
            else:
                return None
        else:
            return None
