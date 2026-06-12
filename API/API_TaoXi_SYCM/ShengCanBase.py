import re
import requests

from extra.extra_reqlog import req_log
from extra.logger_ import logger
from config import UA


class ShengCanBaseApi:
    """生意参谋基础登录态，负责从首页提取 token、userId 和 session。"""

    # 检测 cookie 是否失效，后续请求依赖这里提取到的三个值。
    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua}
        self.token, self.userId, self.session = self.get_sycm_token()  # noqa
        if not self.session and not self.token and not self.userId:
            raise Exception("cookie失效")

    def get_sycm_token(self):  # noqa
        """
        获取生意参谋的token和用户ID
        """
        try:
            session = requests.Session()
            url = "https://sycm.taobao.com/portal/home.htm"  # noqa
            headers = {
                "User-Agent": self.ua,
                "cookie": self.cookie,
                "referer": "https://havanalogin.taobao.com/",
                "Host": "sycm.taobao.com",  # noqa
            }

            # 只发送一次请求获取必要信息
            response = session.get(url=url, headers=headers, timeout=30)
            req_log(response, context="生意参谋首页登录态")
            response.raise_for_status()  # 检查HTTP错误

            # 提取token和userId
            token_match = re.findall(r"legalityToken=(.*?);", response.text)
            userid_match = re.findall(r"mainUserId=(.*?);", response.text)

            if token_match and userid_match:
                logger.success(f"SycmAPI初始化成功，userId={userid_match[0]}")  # noqa
                return token_match[0], userid_match[0], session
            else:
                logger.error("未能提取到token或userid,cookie可能已过期")
                return None, None, None

        except requests.RequestException as e:
            logger.error(f"请求过程中发生错误: {e}")
            return None, None, None
        except Exception as e:
            logger.error(f"获取token时发生未知错误: {e}")
            return None, None, None
