# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:24:52
- 最近修改：2026-06-10 21:36:12
- 文件用途：提供淘系商家工作台 API 公共能力，包括基础请求头、mtop token 刷新和 Cookie token 更新。
- 业务范围：适用于 API_TaoXi_GongZuoTai 包内商家工作台接口，当前服务交易已卖出宝贝报表和订单详情采集。
- 依赖入口：使用 requests、config.UA、date_utils.get_millisecond_timestamp 和 extra.extra_reqlog.req_log。
- 验收方式：修改后执行 py_compile；新增公共入口后执行包导入探针，真实请求需用单店铺、单日期验证。
- 注意事项：基础 API 不写业务表、不保存 Cookie；日志不得输出完整 Cookie、签名 URL 或敏感请求参数。
"""

import hashlib
import re
from urllib.parse import urlencode

import requests

from config import UA
from date_utils import get_millisecond_timestamp
from extra.extra_reqlog import req_log


APP_KEY = "12574478"


class TaoXiGongZuoTaiBaseApi:
    """淘系商家工作台基础 API，负责公共请求头和 mtop token 更新。"""

    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua}

    @staticmethod
    def get_sign(token, timestamp, data):
        """mtop H5 签名公式：md5(token&t&appKey&data)。"""
        sign_text = f"{token}&{timestamp}&{APP_KEY}&{data}"
        return hashlib.md5(sign_text.encode("utf-8")).hexdigest()

    def get_cookie_token(self, cookie=None):
        """请求轻量用户接口，借平台 Set-Cookie 刷新 _m_h5_tk token。"""
        api = "https://h5api.m.taobao.com/h5/mtop.user.getusersimple/1.0/"
        data = "{}"
        timestamp = get_millisecond_timestamp()
        sign = self.get_sign("undefined", timestamp, data)
        params = {
            "jsv": "2.7.4",
            "appKey": APP_KEY,
            "t": timestamp,
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
        response = requests.get(url, headers=headers, timeout=30)
        req_log(response, context="商家工作台mtop token")

        set_cookie = response.headers.get("Set-Cookie") if response.headers else None
        if not set_cookie:
            return None

        m_h5_tk = self._match_cookie_value(set_cookie, "_m_h5_tk")
        m_h5_tk_enc = self._match_cookie_value(set_cookie, "_m_h5_tk_enc")
        return {
            "token": m_h5_tk.split("_")[0] if m_h5_tk else None,
            "_m_h5_tk_enc": m_h5_tk_enc,
            "_m_h5_tk": m_h5_tk,
        }

    @staticmethod
    def _match_cookie_value(cookie_text, cookie_name):
        match = re.search(rf"{re.escape(cookie_name)}=(.*?);", cookie_text)
        return match.group(1) if match else None

    @staticmethod
    def get_new_cookie(cookie_str, m_h5_tk, m_h5_tk_enc, filter_=None):
        """更新 Cookie 中的 mtop token，并过滤不稳定字段。"""
        cookie_dict = {}
        for item in cookie_str.split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                if not filter_ or key not in filter_:
                    cookie_dict[key] = value

        if m_h5_tk:
            cookie_dict["_m_h5_tk"] = m_h5_tk
        if m_h5_tk_enc:
            cookie_dict["_m_h5_tk_enc"] = m_h5_tk_enc
        return "; ".join(f"{key}={value}" for key, value in cookie_dict.items())
