import json

from urllib.parse import urlencode
import requests
from extra.extra_reqlog import req_log
from extra.logger_ import logger
from config import UA


class WxtBaseApi:
    """万相台基础 API，负责校验 Cookie 并创建/查询下载任务。"""

    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua, "cookie": self.cookie}
        self.csrfId, self.loginPointId = self.test_cookie_and_fetch_csrfid()

        if self.csrfId and self.loginPointId:
            logger.success(
                f"WxtBaseApi 初始化成功,csrfId:{self.csrfId},loginPointId:{self.loginPointId}"
            )
        else:
            raise Exception("WxtBaseApi初始化失败")

    def test_cookie_and_fetch_csrfid(self):
        """
        测试cookie是否有效
        获取万相台无界的 csrfId 和 loginPointId
        """
        # checkAccess 同时承担登录态校验和下载任务必要参数提取。
        url = "https://one.alimama.com/member/checkAccess.json"
        headers = {
            "Cookie": self.cookie,
            "Referer": "https://one.alimama.com/index.html",
            "User-Agent": self.ua,
        }
        data = {"bizCode": "universalBP"}

        res = requests.post(url, headers=headers, data=data)

        if req_log(res):
            if res.json().get("info", {}).get("ok"):
                data = res.json().get("data", {})
                csrf_id = data.get("accessInfo", {}).get("csrfId", None)
                login_point_id = data.get("loginPointId", None)
                return csrf_id, login_point_id
            else:
                return False, False
        else:
            logger.error("cookie测试失效")
            return False, False

    def create_download_task(self, data):
        """
        创建下载任务，获取任务id
        :param data:
        :return: task_id
        """
        api = "https://one.alimama.com/report/createDownLoadTask.json?"
        params = {
            "csrfId": self.csrfId,
            # createDownLoadTask 当前使用 onebpSite，查询下载链接时仍走 universalBP。
            "bizCode": "onebpSite",
        }
        url = api + urlencode(params)
        headers = {
            "Cookie": self.cookie,
            "Referer": "https://one.alimama.com/index.html",
            "User-Agent": self.ua,
            "content-type": "application/json",
        }
        res = requests.post(url, data=json.dumps(data), headers=headers)

        if req_log(res):
            if res.json().get("info", {}).get("ok"):
                task_id = res.json().get("data", {}).get("taskId")
                logger.success(f"创建任务成功，taskId：{task_id}")
                return task_id
            else:
                logger.error("创建任务失败")
                return None
        else:
            logger.error("创建任务失败")
            return None

    def get_download_url(self, task_id):
        """
        获取下载链接
        :param task_id:
        :return:
        """
        api = "https://bpcommon.alimama.com/commonapi/report/async/getDownloadUrl.json?"
        params = {
            "csrfId": self.csrfId,
            "bizCode": "universalBP",
            "taskId": task_id,
            "loginPointId": self.loginPointId,
        }
        url = api + urlencode(params)
        headers = {
            "Cookie": self.cookie,
            "Referer": "https://one.alimama.com/",
            "User-Agent": self.ua,
        }
        res = requests.get(url, headers=headers)
        if req_log(res):
            if res.json().get("info", {}).get("ok"):
                download_url = (
                    res.json().get("data", {}).get("result", {}).get("downloadUrl")
                )
                logger.success(f"获取下载链接成功，downloadUrl：{download_url}")
                return download_url
            else:
                logger.error("获取下载链接失败")
                return None
        else:
            logger.error("获取下载链接失败")
            return None
