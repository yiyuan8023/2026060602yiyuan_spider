import requests

from Api_TaoBaoLianMeng.TaoKeBaseApi import TaoKeBaseApi
from extra.extra_date import get_millisecond_timestamp
from extra.extra_reqlog import req_log
from extra.logger_ import logger

from cookie_manager.extra_cookie import get_cookie_value


class TaoKeMyProductApi(TaoKeBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def tb_tk_my_enrolled_products(self, page_no):
        """
        tb_tk_淘宝联盟_服务商合作_普通招商_我报名的活动_报名的商品
        """
        url = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/mkt.merchants.signup.item.list.json"
        params = {
            "t": get_millisecond_timestamp(),
            "_tb_token_": get_cookie_value(self.cookie, '_tb_token_'),
            "campaignId": "",
            "phaseType": "31",
            "creatorId": "",
            "needResource": "true",
            "orderByClause": "create_time",
            "orderType": "DESC",
            "pageNo": page_no,
            "pageSize": "40"
        }

        # data = json.dumps(data, separators=(',', ':'))
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": self.cookie,
            "user-agent": self.ua,
            "referer": "https://ad.alimama.com/portal/v2/pages/zhaoshang/normal/detail.htm",
            "priority": "u=1, i"

        }

        res = requests.get(url=url, headers=headers, params=params)
        if req_log(res):
            logger.success(f'第{page_no}获取成功！！！')
            return res.json()
        else:
            logger.error(f'第{page_no}获取失败！！！')
            return None

    def tb_tk_cps_settlement_report(self, start_time, end_time):
        """
        tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505
        """
        url = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/shopkeeper.rpt.taskstart.json"
        params = {
            "t": get_millisecond_timestamp(),
            "_tb_token_": get_cookie_value(self.cookie, '_tb_token_'),
            "startTime": f"{start_time} 00:00:00",
            "endTime": f"{end_time} 23:59:59",
            "bizType": 1,
            "status": 3,

        }
        # data = json.dumps(data, separators=(',', ':'))
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": self.cookie,
            "user-agent": self.ua,
            "referer": "https://ad.alimama.com/report/overview/orders.htm",
            "origin": "https://ad.alimama.com",
            'Host': 'ad.alimama.com',  # noqa
        }
        res = requests.get(url=url, headers=headers, params=params)
        if req_log(res):
            logger.success(f'成功！！！创建任务日期:{start_time}')
            return res.json()
        else:
            logger.error(f'失败！！！创建任务日期:{start_time}')
            return None
