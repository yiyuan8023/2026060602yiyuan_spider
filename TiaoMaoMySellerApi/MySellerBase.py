
# File: MySellerBaseAPI
import json
import os
import re
from sys import _getframe
from urllib.parse import urlencode

from extra.extra_date import get_millisecond_timestamp
from extra.extra_reqlog import req_log
from extra.logger_ import logger
import hashlib
import time
import requests
from extra.settings import UA

path_ = os.path.join(os.path.dirname(__file__), "cn_en_mapping.json")
with open(path_, 'r', encoding='utf8') as f:
    cn_en_mapping = json.load(f)


class MySellerBaseAPI:
    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua}

    @staticmethod
    def get_sign(token, t, data):
        appkey = "12574478"  # noqa
        p1 = token + "&" + str(t) + "&" + appkey + "&" + data
        return hashlib.md5(p1.encode()).hexdigest()

    def get_cookie_token(self, cookie=None):
        api = 'https://h5api.m.taobao.com/h5/mtop.user.getusersimple/1.0/'
        data = '{}'
        t = get_millisecond_timestamp()
        sign = self.get_sign("undefined", t, data)
        params = {
            'jsv': '2.7.4',
            'appKey': '12574478',
            't': t,
            'sign': sign,
            'api': 'mtop.user.getUserSimple',
            'v': '1.0',
            'type': 'jsonp',
            'dataType': 'jsonp',
            'callback': 'mtopjsonp1',  # noqa
            'data': data,
        }
        url = api + "?" + urlencode(params)
        headers = {"user-agent": self.ua, "cookie": cookie if cookie else self.cookie}
        res = requests.get(url, headers=headers)
        req_log(res)

        print(res.headers)

        if res.headers and res.headers.get("Set-Cookie"):

            try:
                #  _m_h5_tk=f40338c2e6e593cfbc292bab5bf98414_1755688942842;
                _m_h5_tk = re.findall("_m_h5_tk=(.*?);", res.headers["Set-Cookie"])[0]
                token = _m_h5_tk.split("_")[0]
            except Exception as e:
                _m_h5_tk = None
                token = None

            try:
                _m_h5_tk_enc = re.findall("_m_h5_tk_enc=(.*?);", res.headers["Set-Cookie"])[0]
            except Exception as e:
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
        更新的cookie
        :param cookie_str:原始 cookie 字符串
        :param _m_h5_tk: 新的 _m_h5_tk 值
        :param _m_h5_tk_enc: 新的 _m_h5_tk_enc 值
        :param filter_: 需要过滤掉的 cookie key 列表
        :return:更新后的 cookie 字符串
        """
        cookie_dict = {}
        for item in cookie_str.split(';'):
            # 去掉空格并分割键值对
            if '=' in item:
                key, value = item.strip().split('=', 1)
                if not filter_:
                    cookie_dict[key] = value
                else:
                    if key not in filter_:
                        cookie_dict[key] = value
                    else:
                        pass
        if _m_h5_tk:
            cookie_dict['_m_h5_tk'] = _m_h5_tk
        if _m_h5_tk_enc:
            cookie_dict['_m_h5_tk_enc'] = _m_h5_tk_enc
        cookie_str = "; ".join([f"{key}={value}" for key, value in cookie_dict.items()])
        return cookie_str

    def cn_to_en(self, d: dict, kk: str):
        en_dict = {}
        for k, v in cn_en_mapping[kk].items():
            # print(k,v)
            en_dict[k] = d[v]
        return en_dict

# a = MySellerBaseAPI(
#     'DI_T_=7VjQ9AVLnHHfjQL11bW5CjgGv695uHvHVmgRFez5ucq9jz6LtpCjQL11bW5CjgGv695uHvHVmgRFez5ucq9jz6LtpC; thw=cn; wk_cookie2=1de33e37072f0ef696f0385c1905c161; wk_unb=UoH%2B4NPsNoWZlw%3D%3D; cookie2=1f35fdb60154c915bc4e0a6e9c5246d4; t=80b5d362e8d5aecdda506d71fb64566c; _tb_token_=3df5be8be1811; _samesite_flag_=true; xlly_s=1; 3PcFlag=1744348480120; sgcookie=E100Lt6d11kmGOYS0IPsvdznykR%2Fy%2BJ4FUl68ut4cmfde6of5HuJPEfk8uFDyEeqOR7VgLFfE4GzFV7dTlTEqgEb5qQtcuY9weAb%2BIC3qzZ8EHG6Hk44e74dxygBXgIz3U4l; unb=2212373938588; sn=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; uc1=cookie14=UoYaj4s1XlauQQ%3D%3D&cookie21=UIHiLt3xSalX; csg=26ee041a; _cc_=WqG3DMC9EA%3D%3D; cancelledSubSites=empty; skt=d67b6c46b9659f4c; mtop_partitioned_detect=1; _m_h5_tk=f024c0db57db31aca629cbd1de5c3135_1744356964263; _m_h5_tk_enc=f2ccde2e19d9efe3e7afff0c8a0793d4; tfstk=grsEROcCakEUgaAp-GtruMj8gzxpP3PbxgOWETXkdBAhd2Oo41CGRL6kN35Pa_RBrWKC415d6e_CEg9l4CXDFJF8pGWl6_o5PHT541WAEBmBA_9rpG5qVDNLJTmyV3VbGoZfp9tJqSNaCZhjpL9kKvcWKOmMVLyEWCeAp9K-BAGulNXKavFsSBvkZR-MUpoHq2xkSRJy3QxktUciSKAMq3YnqCvMeLvntDAuQOA9E3vHq_xgQLOMZbFXqnhXne25Js5D5APb5IWH_0mlxuLBg7LMBIIadUAAKG3s58pe8IXH_SQt9KYGeUS-e08cKZCJn6c3aQINIMbci5gBtZJPhaW3xcxCv9bDriV-rs-FaEjH7Ymejhdebdj0Fqd1bB1lYF2j0UtGcExh5PFBPHJVZMCEU0fcCtspWgPqsQQBHhvP2-0yaUjPqbpMBISR8b0y-dpwGRyNpaUfkk-MA2g-yeH9QIwpr43J-dpwGRyZy4LLMdRbpUf..')
# print(a.get_sign("c87c8dca420cad0bec218b9a54a6bf3c","1744441472741",''))
