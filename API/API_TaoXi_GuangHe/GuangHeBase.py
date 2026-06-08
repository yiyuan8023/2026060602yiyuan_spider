import hashlib
import json
from http.cookies import SimpleCookie

import requests

from extra.extra_date import get_millisecond_timestamp
from extra.extra_reqlog import req_log
from config import UA


# 淘宝 mtop H5 接口 appKey，来自浏览器 Network 请求参数，不是店铺密钥。
APP_KEY = "12574478"


class GuangHeBaseApi:
    """光合平台 mtop 基础 API，负责 Cookie session、token 和签名请求。"""

    def __init__(self, cookie, referer):
        self.cookie = cookie
        self.referer = referer
        self.session = requests.Session()
        self._load_cookie(cookie)

    def _load_cookie(self, cookie):
        """将数据库里取出的 Cookie 字符串灌入 session，供 mtop 请求复用。"""
        simple_cookie = SimpleCookie()
        simple_cookie.load(cookie)
        for name, morsel in simple_cookie.items():
            self.session.cookies.set(name, morsel.value, domain=".taobao.com", path="/")

    def _token(self):
        """mtop 签名使用 _m_h5_tk 中下划线前面的 token。"""
        token_value = (
            self.session.cookies.get("_m_h5_tk", domain=".taobao.com")
            or self.session.cookies.get("_m_h5_tk")
            or ""
        )
        return token_value.split("_")[0]

    @staticmethod
    def _sign(token, timestamp, data_text):
        """mtop h5 签名公式：md5(token&t&appKey&data)。"""
        sign_text = f"{token}&{timestamp}&{APP_KEY}&{data_text}"
        return hashlib.md5(sign_text.encode("utf-8")).hexdigest()

    def _mtop_request(self, api, data, version="1.0"):
        """统一发起 mtop 请求，自动处理 token 过期后的 Cookie 刷新重试。"""
        last_response = None
        for _ in range(3):
            timestamp = str(get_millisecond_timestamp())
            data_text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            params = {
                "jsv": "2.6.1",
                "appKey": APP_KEY,
                "t": timestamp,
                "sign": self._sign(self._token(), timestamp, data_text),
                "api": api,
                "v": version,
                "dataType": "json",
                "type": "json",
                "syncCookieMode": "true",
                "preventFallback": "true",
                "data": data_text,
            }
            headers = {
                "User-Agent": UA,
                "referer": self.referer,
            }
            response = self.session.get(
                f"https://h5api.m.taobao.com/h5/{api}/{version}/",
                params=params,
                headers=headers,
                timeout=30,
            )
            req_log(response, context=f"光合mtop:{api}", raise_error=True)
            response_json = response.json()
            last_response = response_json
            ret_text = "|".join(response_json.get("ret", []))
            # token 过期时平台会刷新 _m_h5_tk，下一轮重新签名即可。
            if "TOKEN" in ret_text.upper() or "令牌" in ret_text:
                continue
            if not any(item.startswith("SUCCESS") for item in response_json.get("ret", [])):
                raise RuntimeError(ret_text)
            return response_json

        raise RuntimeError(f"mtop请求失败: {last_response}")

    @staticmethod
    def _format_day(day):
        return str(day).replace("-", "")
