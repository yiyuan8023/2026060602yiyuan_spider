import datetime
import re
import time
from sys import _getframe

import requests
from logger_ import logger
from settings import UA


class ShengCanBaseApi:
    # 检测cookie有没有失效
    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua}
        self.token, self.userId, self.session = self.get_sycm_token()
        if not self.session and not self.token and not self.userId:
            raise Exception("cookie失效")

    def get_sycm_token(self):
        """
        获取生意参谋的token和用户ID
        """
        try:
            session = requests.Session()
            url = 'https://sycm.taobao.com/portal/home.htm'
            headers = {
                'User-Agent': self.ua,
                'cookie': self.cookie,
                'referer': 'https://havanalogin.taobao.com/',
                'Host': 'sycm.taobao.com'
            }

            # 只发送一次请求获取必要信息
            response = session.get(url=url, headers=headers)
            response.raise_for_status()  # 检查HTTP错误

            # 提取token和userId
            token_match = re.findall(r"legalityToken=(.*?);", response.text)
            userId_match = re.findall(r"mainUserId=(.*?);", response.text)

            if token_match and userId_match:
                logger.success(f"SycmAPI初始化成功，token={token_match[0]},userId={userId_match[0]}")
                print(f"token={token_match[0]},userId={userId_match[0]},session = {session}")
                return token_match[0], userId_match[0], session
            else:
                logger.error("未能提取到token或userId，cookie可能已过期")
                return None, None, None

        except requests.RequestException as e:
            logger.error(f"请求过程中发生错误: {e}")
            return None, None, None
        except Exception as e:
            logger.error(f"获取token时发生未知错误: {e}")
            return None, None, None

    @staticmethod
    def req_log(res: requests.models.Response):
        """
        针对request请求的response对象的日志，通配
        # _getframe(1) 返回调用函数的名称，用于定位信息
        """
        if res.status_code == 200:
            logger.info(f"在{_getframe(1)}发起了调用,请求成功（status_code:{res.status_code}）")
            return True
        else:
            logger.error(f"在{_getframe(1)}发起了调用,请求失败（status_code:{res.status_code}）")
            return False
