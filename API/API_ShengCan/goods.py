from urllib.parse import urlencode
import requests

from extra.downloader import Downloader
from extra.extra_error import handle_request_error
from extra.extra_reqlog import req_log

from API.API_ShengCan.ShengCanBase import ShengCanBaseApi
from extra.logger_ import logger
from extra.settings import UA
from extra.extra_date import get_millisecond_timestamp, get_second_timestamp


class Goods(ShengCanBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def good_rank__all_good_day(self, day):
        # tb_sycm_商品_商品排行_全部商品_202504 # noqa

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
            "indexCode": f"payAmt, sucRefundAmt, payItmCnt, payByrCnt, payRate, newPayByrCnt, "
                         f"payOldByrCnt, olderPayAmt, juPayAmt, mtdPayAmt, mtdPayItmCnt, ytdPayAmt, "
                         f"itemStatus, itemCartCnt, itemCartByrCnt, itemCltByrCnt, visitCartRate, visitCltRate, "
                         f"itmUv, itmPv, itmStayTime, itmBounceRate, seGuideUv, seGuidePayByrCnt, seGuidePayRate, "
                         f"uvAvgValue, starLevel001, itemUnitPrice1"
        }

        try:
            items = Downloader(api=api, cookie=self.cookie, params=params).download_excel(skiprows=4, engine='xlrd')

            return items

        except Exception as e:
            return handle_request_error(e)

    def category_360__flow_from(self, daterange, cate_id):
        """
        tb_sycm_商品_品类360_流量分析_流量来源_202504 
        :param daterange:
        :param cate_id: 品类ID
        :return:接口返回的JSON数据或None
        """  # noqa

        api = "https://sycm.taobao.com/cc/category/flow/source/overview/v3.json?"
        params = {
            "dateRange": daterange,
            "dateType": "month",
            "pageSize": 10,
            "page": 1,
            "order": "desc",
            "orderBy": "itmUv",
            "belong": "all",
            "cateId": cate_id,
            "indexCode": "itmUv, itemCartByrCnt, itemCltByrCnt, payByrCnt",
            "_": get_millisecond_timestamp(),
            "token": self.token
        }

        headers = {
            "referer": f"https://sycm.taobao.com/cc/cate_archives?activeKey=flow&cateId={cate_id}"
                       f"&dateRange={daterange}&dateType=month"
        }

        try:
            res = Downloader(api=api, cookie=self.cookie, params=params, headers=headers).download_web()
            if req_log(res):
                return res.json()
            else:
                logger.warning("请求返回为空或请求日志记录失败")
                return None

        except Exception as e:
            return handle_request_error(e)

    def goods_360__title_drainage(self, daterange, itemid):
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
            "itemId": itemid,
            "device": 0,
            "kwType": "se_keyword",
            "indexCode": "uv,payOrderByrCnt,payConveRate",  # noqa
            "_": get_second_timestamp,
            "token": self.token
        }
        url = api + urlencode(params)
        headers = {
            "User-Agent": UA,
            "cookie": self.cookie,
        }
        res = requests.get(url, headers=headers)
        if req_log(res):
            return res.json()
        else:
            return None

    def goods_360__title_drainage_excel(self, daterange, itemid):
        """
        table_name = "tb_sycm_商品_商品360_标题优化_搜索词_202504"
        :param daterange: 日期区间
        :param itemid: 类目id
        :return:
        """  # noqa

        api = "https://sycm.taobao.com/cc/item/title/word/excel.json?"
        params = {
            "itemId": itemid,
            "device": 0,
            "kwType": "se_keyword",
            "dateType": "day",
            "dateRange": daterange
        }

        try:
            items = Downloader(api=api, cookie=self.cookie, params=params).download_excel(skiprows=5)
            return items
        except Exception as e:
            logger.warning("请求返回为空或请求日志记录失败")
            return handle_request_error(e)

    def recommend_analysis_single_excel(self, day):
        # tb_sycm_内容_渠道效果_推荐_单条效果_微详情视频_全部内容_202507 # noqa

        api = r"https://sycm.taobao.com/s_content/recommend/analysis/single/export.json?"
        params = {
            "contentSource": "all",
            "keyword": "",
            "contentType": "minidetail",  # noqa
            "dateType": "day",
            "dateRange": f"{day}|{day}"
        }
        try:
            items = Downloader(api=api, cookie=self.cookie, params=params).download_excel(skiprows=5)
            return items

        except Exception as e:
            return handle_request_error(e)
