# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 20:24:44
- 最近修改：2026-06-10 20:24:44
- 文件用途：提供淘系直播中控台 API 公共能力，包括 mtop token 刷新、签名、Cookie 更新和字段映射读取。
- 业务范围：适用于 API_TaoXi_ZhiBo 包内直播中控台接口，当前服务直播概览每日分析数据采集。
- 依赖入口：使用 requests、config.UA、date_utils.get_millisecond_timestamp、extra.extra_reqlog.req_log 和本包 cn_en_mapping.json。
- 验收方式：修改后执行 py_compile；新增公共入口后执行包导入探针和单店铺、单日期接口验证。
- 注意事项：基础 API 不写业务表、不保存 Cookie；日志不得输出完整 Cookie、签名 URL 或敏感请求参数。
"""

import hashlib
import json
import os
import re
from urllib.parse import urlencode

import requests

from config import UA
from date_utils import get_millisecond_timestamp
from extra.extra_reqlog import req_log


APP_KEY = "12574478"
MAPPING_PATH = os.path.join(os.path.dirname(__file__), "cn_en_mapping.json")
with open(MAPPING_PATH, "r", encoding="utf-8") as mapping_file:
    cn_en_mapping = json.load(mapping_file)


class TaoXiZhiBoBaseApi:
    """淘系直播中控台基础 API，负责 mtop 签名、token 刷新和字段映射。"""

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
        req_log(response)

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

    def cn_to_en(self, raw_item: dict, mapping_key: str):
        """按映射表把平台原始字段转换为目标中文字段。"""
        return {
            cn_field: raw_item.get(raw_field)
            for cn_field, raw_field in cn_en_mapping[mapping_key].items()
        }
