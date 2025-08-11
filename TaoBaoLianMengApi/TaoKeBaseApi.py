# File: TaoKeBaseApi


from urllib.parse import urlencode
import pandas as pd
import requests

from extra.downloader import Downloader
from cookie_manager.extra_cookie import get_cookie_value
from extra.logger_ import logger
from extra.settings import UA
from extra.extra_date import get_millisecond_timestamp
from extra.extra_reqlog import req_log


class TaoKeBaseApi(object):
    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua, "cookie": self.cookie}

    def task_status_list(self):
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

    @staticmethod
    def _process_task_status(result):
        """
        处理任务状态列表，分类已完成和未完成的任务
        :param result: 任务状态列表
        :return: (finish_task, un_finish_task)
        """
        finish_task = {}  # {文件名: 任务ID}
        un_finish_task = []  # [任务ID, 文件名, ...]

        for task in result:
            if task.get('process') == "100" and task.get('status') == 1:
                finish_task[task["fileName"]] = task["id"]
            elif task.get('errorMessage') == "超时停止调度":
                un_finish_task.append(task["id"])
                un_finish_task.append(task["fileName"])
        return finish_task, un_finish_task

    def get_task_status_list(self):
        """
           获取淘宝联盟任务状态列表
        """
        # 调用API获取任务状态列表
        task_status_list_res = self.task_status_list()
        logger.info(task_status_list_res)

        if not task_status_list_res:
            return {}, []

        # 检查返回结果中的错误码，判断cookie是否过期
        if task_status_list_res.get("code") == 601:
            raise "cookie过期"

        result = task_status_list_res.get('data', {}).get('result', [])
        finish_task, un_finish_task = self._process_task_status(result)

        logger.info(finish_task)
        return finish_task, un_finish_task

    def fetch_report_shop_data(self, id_list):
        """
        获取淘宝联盟报表文件下载链接
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
