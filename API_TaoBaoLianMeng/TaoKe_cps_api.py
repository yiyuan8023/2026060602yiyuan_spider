"""
注：
步骤：生成任务-获取任务列表-在任务列表中寻找目标ID

1、cps订单，可以指定区间下载，只需要获取下载的开始日期和结束日期即可
2、创建任务后，会生成任务列表，需要从任务列表中找到对于的任务id，根据ID再获取报表
3、创建任务重，如果历史已经创建，会生成直白，直接从任务列表中获取即可
TODO:原打算先删除全部任务，然后再创建，但是在测试过程中，无法通过，所以放弃

"""
from urllib.parse import urlencode

import pandas as pd
import requests

from Api_TaoBaoLianMeng.TaoKeBaseApi import TaoKeBaseApi
from extra.downloader import Downloader
from extra.extra_date import get_millisecond_timestamp
from extra.extra_reqlog import req_log
from extra.logger_ import logger

from cookie_manager.extra_cookie import get_cookie_value


class TaoKeCpsApi(TaoKeBaseApi):
    def __init__(self, cookie, start_time, end_time, name_suffix):
        super().__init__(cookie)
        self.cookie = cookie
        self.name_suffix = name_suffix
        self.start_time = start_time
        self.end_time = end_time

    def tb_tk_cps_settlement_report(self):
        """
        tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505
        创建任务
        """
        url = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/shopkeeper.rpt.taskstart.json"
        params = {
            "t": get_millisecond_timestamp(),
            "_tb_token_": get_cookie_value(self.cookie, '_tb_token_'),
            "startTime": f"{self.start_time} 00:00:00",
            "endTime": f"{self.end_time} 23:59:59",
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
            logger.success(f'成功！！！创建任务日期:{self.start_time}_{self.end_time}')
            return res.json()
        else:
            logger.error(f'失败！！！创建任务日期:{self.start_time}_{self.end_time}')
            return None

    def cps_task_status_list(self):
        """
        获取淘宝联盟任务状态列表JSON数据
        该函数用于查询当前账号下所有报表任务的执行状态，包括任务ID、文件名、
        处理进度、状态等信息。主要用于检查报表任务是否已完成，以便进行后续下载操作。
        Returns: dict or None: 返回API响应的JSON数据
        """
        api = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/shopkeeper.rpt.process.list.json?"
        t = get_millisecond_timestamp()
        params = {
            "t": t,
            "_tb_token_": get_cookie_value(self.cookie, '_tb_token_'),
            "pageNo": 1,
            "pageSize": 10,
            "bizType": 1,
            # "status": 3,
            # "timeer": t
        }

        headers = {
            "cookie": self.cookie,
            "user-agent": self.ua,
            "referer": "https://ad.alimama.com/report/overview/orders.htm",
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }

        url = api + urlencode(params)
        res = requests.get(url, headers=headers)
        if req_log(res):
            return res.json()
        else:
            return None

    def fetch_cps_file_link(self, id_list):
        """
        获取【tb_tk_淘宝联盟_商品分析】文件下载链接
        :param id_list:
        :return:
        """
        api = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/shopkeeper.rpt.filelink.json?"
        params = {
            "t": get_millisecond_timestamp(),
            "_tb_token_": get_cookie_value(self.cookie, '_tb_token_'),
            "idList": id_list,
            "bizType": 1
        }
        headers = {
            "cookie": self.cookie,
            "user-agent": self.ua,
            "referer": "https://ad.alimama.com/report/overview/orders.htm",
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        url = api + urlencode(params)
        res = requests.get(url, headers=headers)
        if req_log(res):
            file_link = res.json().get("data", {}).get("urlList", [{}])[0].get("url")
            logger.info(file_link)
            # items = Downloader(api=file_link, cookie=None, params=None, headers=None).download_csv()
            data = Downloader(api=file_link).download_csv()
            df = pd.read_csv(data)
            df_filled = df.fillna("")
            if df_filled.empty:
                return {}
            else:
                items = df_filled.to_dict('records')
                return items
        else:
            return None
