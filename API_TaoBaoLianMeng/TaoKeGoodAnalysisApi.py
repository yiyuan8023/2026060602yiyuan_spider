"""
注：

步骤：获取任务列表-检查不在列表中的任务-重新生成任务-获取下载链接-下载文件-存入数据库

1、cps订单，可以指定区间下载，只需要获取下载的开始日期和结束日期即可
2、创建任务后，会生成任务列表，需要从任务列表中找到对于的任务id，根据ID再获取报表
3、创建任务重，如果历史已经创建，会生成直白，直接从任务列表中获取即可
TODO:原打算先删除全部任务，然后再创建，但是在测试过程中，无法通过，所以放弃

"""

from urllib.parse import urlencode

import pandas as pd
import requests

from Api_TaoBaoLianMeng.TaoKeBaseApi import TaoKeBaseApi
from extra.extra_date import get_millisecond_timestamp
from extra.extra_reqlog import req_log
from extra.logger_ import logger
from extra.downloader import Downloader

from cookie_manager.extra_cookie import get_cookie_value


class TaoKeGoodAnalysisApi(TaoKeBaseApi):
    def __init__(self, cookie, name_suffix):
        super().__init__(cookie)
        self.cookie = cookie
        self.name_suffix = name_suffix

    def tb_tk_goods_analysis(self, start_time, end_time):

        #  tb_tk_淘宝联盟_商品分析
        #  发送请求，创建任务

        url = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/shopkeeper.rpt.taskstart.json"
        params = {
            "t": get_millisecond_timestamp(),
            "_tb_token_": get_cookie_value(self.cookie, '_tb_token_'),
            "startTime": f"{start_time} 00:00:00",
            "endTime": f"{end_time} 23:59:59",
            "bizType": 126,
            "ext": '{"level3Dim":null,"orderMetric":"alipayAmt","orderType":"desc"}'
        }
        # data = json.dumps(data, separators=(',', ':'))
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": self.cookie,
            "user-agent": self.ua,
            "referer": "https://ad.alimama.com/portal/v2/report/item/list.htm",
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

    def create_goods_analysis_task(self, start_time, end_time, finish_task):
        """
            创建【tb_tk_淘宝联盟_商品分析】任务
            检查该时间段的报表是否已经存在且已完成，如果存在则直接返回任务ID；如果不存在则调用API
        创建新的报表任务。
        """
        logger.info(f"\n{'-' * 120}\n在创建 {start_time} 00:00:00~{end_time} 23:59:59-商品分析 报告")
        file_name = f"{start_time} 00:00:00~{end_time} 23:59:59-商品分析"
        if file_name in finish_task.keys():
            logger.info(f"报告已存在，且完成{file_name}")
            return finish_task[file_name]

        else:
            res_json = self.tb_tk_goods_analysis(start_time, end_time)
            # print(res_json)
            if res_json and res_json.get('data'):
                id_list = res_json.get('data').get('idList')
                logger.info(f"任务已创建，{id_list}")
            else:
                logger.info("任务已经存在")

    def goods_task_status_list(self):
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
            "pageSize": 40,
            "bizType": 126,
            "timeer": t
        }

        headers = {
            "cookie": self.cookie,
            "user-agent": self.ua,
            "referer": "https://ad.alimama.com/portal/v2/report/item/list.htm",
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }

        url = api + urlencode(params)
        res = requests.get(url, headers=headers)
        if req_log(res):
            return res.json()
        else:
            return None

    def get_finish_id(self, start_time, end_time):

        task_status_list_res = self.goods_task_status_list()  # 任务状态列表json数据包
        _finish_task, _un_finish_task = self.get_task_status_list(
            task_status_list_res=task_status_list_res)  # 解析数据包, 获取任务状态id
        file_name = f"{start_time} 00:00:00~{end_time} 23:59:59-{self.name_suffix}"
        if file_name in _finish_task.keys():
            return _finish_task[file_name]

        else:
            res_json = self.tb_tk_goods_analysis(start_time, end_time)
            if res_json and res_json.get('data'):
                id_list = res_json.get('data').get('idList')
                logger.info(f"任务已创建，{id_list}")
                return None
            else:
                logger.info("任务已经存在")
                return None

    def fetch_goods_file_link(self, id_list):
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
            "bizType": 126
        }
        headers = {
            "cookie": self.cookie,
            "user-agent": self.ua,
            "referer": "https://ad.alimama.com/portal/v2/report/item/list.htm",
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
