
import json

from urllib.parse import urlencode
import requests
from extra.extra_reqlog import req_log
from extra.logger_ import logger
from extra.settings import UA


class WxtBaseApi:
    # 万相台 API
    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua, "cookie": self.cookie}
        self.csrfId, self.loginPointId = self.test_cookie_and_fetch_csrfid()

        if self.csrfId and self.loginPointId:
            logger.success(f"WxtBaseApi 初始化成功,csrfId:{self.csrfId},loginPointId:{self.loginPointId}")
        else:
            raise Exception("WxtBaseApi初始化失败")

    def test_cookie_and_fetch_csrfid(self):
        """
        测试cookie是否有效
        获取万相台无界的 csrfId 和 loginPointId
        """
        # 测试cookie,正常会包括在 checkAccess 接口返回的 json 中
        url = "https://one.alimama.com/member/checkAccess.json"
        headers = {
            "Cookie": self.cookie,
            "Referer": "https://one.alimama.com/index.html",
            "User-Agent": self.ua
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
            "bizCode": "universalBP"
        }
        url = api + urlencode(params)
        headers = {
            "Cookie": self.cookie,
            "Referer": "https://one.alimama.com/index.html",
            "User-Agent": self.ua,
            "content-type": "application/json"
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
            "loginPointId": self.loginPointId

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
                download_url = res.json().get("data", {}).get("result", {}).get("downloadUrl")
                logger.success(f"获取下载链接成功，downloadUrl：{download_url}")
                return download_url
            else:
                logger.error("获取下载链接失败")
                return None
        else:
            logger.error("获取下载链接失败")
            return None

# a=WanXiangTaiBaseApi(cookie="_tb_token_=fc5577ef-1880-4913-b430-b84051957104; dnk=; t=32ec1ebd82648c8b1e2da2161a97f0e5; lgc=; wk_cookie2=1b76aa0113fd20e5edc5b5c1c9ae2156; _tb_token_=7f38b57b85873; wk_unb=UoH%2B4NPsNoWZlw%3D%3D; cookie2=1b041044b1464d5e4c44c1c41d437adf; _nk_=; cna=pMeKICScZn4CAXPN5Bx3qtJt; xlly_s=1; uc1=cookie14=UoYajlVWuI%2BpNQ%3D%3D&cookie21=U%2BGCWk%2F7oPIg; lid=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; unb=2212373938588; sgcookie=E100KTwaqr52TLSYEI%2BJTIHZV9aC1RJ4WKRIXoKiHrRaMqFF898u3xLKdELI9TJEkPOG03hMs0bJ0pxz2trJsJl2lq5PxNY96hQ%2BqGQK8t%2Fs1ztNVfBU8G4jhU49jKP5gNWw; cancelledSubSites=empty; csg=4fde637f; sn=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; tfstk=gQuZqxi-arDCU70wnW4V4RH4soatxPv5iqwbijc01R2g5j_qYxMn1ltt1roEnvE_IcGbgZlTdx_j1xwU8Jcjf-a_cSDECbm_fFUbmxkIpZG_5j1tvYGl5VtTlZzTkrvWFUT56fUYoPKLcdCT-SF4iEwgoJ4TGSsQ7CYS6fCh_tASxU14BMBxi-D0jkb3aJXGSrD0xJV8KNVcSSXHTSe3oSV0neX315WGIGDmtBPYK-40jfy4VoJzGlAbw-5reO5LM8cgLZblw5qMXxIfmiDT_lrE3JRw_2Pab8q0dlRnzbciySuvZiyqwcD_9x8yLy0ZQVqUuE7L5bonQkow3wrKxb30YDpP2bhiQ0qoSeR3YVh7SJuvMZeifj0b0VvlGR0tC2r-kOJQh0GISkkkdwkY0cmuSqJy-g5AHWY6JqnNnirg9WyWTBP7TRxaaHtkKiIYxzFUFCN1miXu_WyWTQSADlpYT8OiK")
