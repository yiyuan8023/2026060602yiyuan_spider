# File: MySellerBaseAPI
import hashlib
import json
import os
import re
from urllib.parse import urlencode

import requests

from config import UA
from date_utils import get_millisecond_timestamp
from extra.extra_reqlog import req_log

path_ = os.path.join(os.path.dirname(__file__), "cn_en_mapping.json")
with open(path_, "r", encoding="utf8") as f:
    cn_en_mapping = json.load(f)


class MySellerBaseAPI:
    """淘系商家工作台基础 API，负责 mtop token、Cookie 更新和字段映射。"""

    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua}

    @staticmethod
    def get_sign(token, t, data):
        """商家工作台 mtop H5 签名：md5(token&t&appKey&data)。"""
        appkey = "12574478"  # noqa
        p1 = token + "&" + str(t) + "&" + appkey + "&" + data
        return hashlib.md5(p1.encode()).hexdigest()

    def get_cookie_token(self, cookie=None):
        """请求轻量用户接口，借平台 Set-Cookie 刷新 _m_h5_tk token。"""
        api = "https://h5api.m.taobao.com/h5/mtop.user.getusersimple/1.0/"
        data = "{}"
        t = get_millisecond_timestamp()
        sign = self.get_sign("undefined", t, data)
        params = {
            "jsv": "2.7.4",
            "appKey": "12574478",
            "t": t,
            "sign": sign,
            "api": "mtop.user.getUserSimple",
            "v": "1.0",
            "type": "jsonp",
            "dataType": "jsonp",
            "callback": "mtopjsonp1",  # noqa
            "data": data,
        }
        url = api + "?" + urlencode(params)
        headers = {"user-agent": self.ua, "cookie": cookie if cookie else self.cookie}
        res = requests.get(url, headers=headers)
        req_log(res)

        if res.headers and res.headers.get("Set-Cookie"):
            try:
                # _m_h5_tk 下划线前半段是 mtop 签名 token，后半段是过期时间。
                _m_h5_tk = re.findall("_m_h5_tk=(.*?);", res.headers["Set-Cookie"])[0]
                token = _m_h5_tk.split("_")[0]
            except Exception:
                _m_h5_tk = None
                token = None

            try:
                _m_h5_tk_enc = re.findall(
                    "_m_h5_tk_enc=(.*?);", res.headers["Set-Cookie"]
                )[0]
            except Exception:
                _m_h5_tk_enc = None

            return {
                "token": token,
                "_m_h5_tk_enc": _m_h5_tk_enc,
                "_m_h5_tk": _m_h5_tk,
            }
        else:
            return None

    @staticmethod
    def get_new_cookie(cookie_str, _m_h5_tk, _m_h5_tk_enc, filter_=None):
        """
        更新 Cookie 中的 mtop token。

        Args:
            cookie_str: 原始 cookie 字符串。
            _m_h5_tk: 新的 _m_h5_tk 值。
            _m_h5_tk_enc: 新的 _m_h5_tk_enc 值。
            filter_: 需要过滤掉的 cookie key 列表。
        """
        cookie_dict = {}
        for item in cookie_str.split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                if not filter_ or key not in filter_:
                    cookie_dict[key] = value

        if _m_h5_tk:
            cookie_dict["_m_h5_tk"] = _m_h5_tk
        if _m_h5_tk_enc:
            cookie_dict["_m_h5_tk_enc"] = _m_h5_tk_enc
        return "; ".join([f"{key}={value}" for key, value in cookie_dict.items()])

    def cn_to_en(self, d: dict, kk: str):
        """按映射表把平台中文字段转换为内部英文字段。"""
        en_dict = {}
        for k, v in cn_en_mapping[kk].items():
            en_dict[k] = d[v]
        return en_dict
