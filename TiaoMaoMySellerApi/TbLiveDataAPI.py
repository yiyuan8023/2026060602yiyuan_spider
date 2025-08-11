# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-07-16
# Time: 10:22
# Project: jide
# File: TbLiveDataAPI
"""
淘宝直播》》数据
"""

import json
import re
from urllib.parse import urlencode
import requests

from TiaoMaoMySellerApi.MySellerBase import MySellerBaseAPI
from extra.extra_date import get_min_max_timestamps
from extra.extra_reqlog import req_log


class TbLiveDataAPI(MySellerBaseAPI):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def live_overview(self, begin_date, end_date):
        # tb_zbzkt_数据_直播概览_每日分析_202507 # noqa
        api = "https://h5api.m.taobao.com/h5/mtop.dreamweb.query.general.generalquery/1.0/"
        # cookie_token = self.get_cookie_token(self.cookie)
        # print(cookie_token)
        # token = cookie_token["token"]
        # new_cookie = self.get_new_cookie(self.cookie, cookie_token["_m_h5_tk"], cookie_token["_m_h5_tk_enc"],
        #                                  filter=['tfstk'])
        # print(new_cookie)
        # t = get_min_max_timestamps()
        data = r'{"dataApi":"dataQRForm","param":"{\"queryCycleCode\":\"30d\",\"queryCycleStartDate\":\"\",\"queryCycleEndDate\":\"\",\"cpType\":\"cd\",\"calType\":\"uv\",\"dataQRFormId\":\"live_overview_dashboard_v2\",\"orderColumn\":\"ds\",\"orderType\":\"1\",\"queryUserRole\":\"ALL\",\"beginDate\":\"%s\",\"endDate\":\"%s\",\"time\":\"\"}"}' % (
        begin_date, end_date)
        sign = self.get_sign(token, t, data)
        params = {
            "jsv": "2.7.4",
            "appKey": "12574478",
            "t": t,
            "sign": sign,
            "api": "mtop.dreamweb.query.general.generalQuery",
            "v": "1.0",
            "preventFallback": "true",
            "type": "jsonp",
            "dataType": "jsonp",
            "callback": "mtopjsonp71",
            "data": data,

        }
        headers = {
            "referer": "https://liveplatform.taobao.com/restful/index/live/overview",
            "user-agent": self.ua,
            "cookie": new_cookie
        }
        url = api + "?" + urlencode(params)
        res = requests.get(url=url, headers=headers)
        if req_log(res):
            json_str = re.findall(r'mtopjsonp\d+\((.*?)\)', res.text)
            res_json = json.loads(json_str[0])
            print(res.headers)
            return res_json
        else:
            return None

# t=TbLiveDataAPI("thw=cn; t=61f6d9516106249f280ae435a10c9a79; wk_cookie2=167378e44dd073cc15b504cc30abf9be; wk_unb=UUpgT7aDm3jPjxplCg%3D%3D; cookie2=134e92970db3c0c52345642bcb0135a9; _tb_token_=e3950d6f556f7; _samesite_flag_=true; cancelledSubSites=empty; 3PcFlag=1752628029700; xlly_s=1; sgcookie=E100qyy2Ra%2FcjvJ7F0bvAd4JQ%2BYrUOQm%2BQ5XBXUGsteaJeWcZXudvpx91nhbByIiHMIdHkGH%2FIVLciGnzBpRSV695zbR5sFlCg%2BZKbXinNBCuXG8E2UWfUdYtqc6%2FJ%2FhkJw1; uc1=cookie21=UtASsssmfufd&cookie14=UoYbySf%2FNS5aUA%3D%3D; unb=2208167046031; sn=%E5%B0%8F%E5%90%89%E6%97%97%E8%88%B0%E5%BA%97%3Axj; csg=da54df81; skt=8e6dd665dfff0278; _cc_=VT5L2FSpdA%3D%3D; cna=v21ZIJhrkh0CASeqbVqkh3yc; mtop_partitioned_detect=1; _m_h5_tk=786aecd3606aff659b1e48e82fb16fdc_1752722469758; _m_h5_tk_enc=0fce762b33969ae9b0531105725d9abe; x5sec=7b2274223a313735323731343632392c22733b32223a2234666334393936333237613330666437222c22617365727665723b33223a22307c4350656134634d4745506a35762f662f2f2f2f2f2f774561447a49794d4467784e6a63774e4459774d7a45374d5369414244446b6f6f616f2b502f2f2f2f3842227d; aui=2208167046031; sca=9a7fddc7; tfstk=gO8ESnwBU23Emz6dxF_z3kJx74bpBakj-U65ZQAlO9XHFHZuzQpi9zGRRgYPQIcdd0npUhJkBM6hVXBlZKRVP9xBN_zy9OQWO_GpQLR23_ZWAXeu9FJ4PyMKvQ4PPaDjhqgX9B_RrxsayCQ89_1zr625ZG2GP_rVWcrX9BQ865wochALaBK5JMbkENjG967lt6buSf5PNTblKg2gjsXGraXlrljGa6yuEyvksf5RITblxLbi__hRdabYhsjnsdyyXtatJy62tOzure0RYtl1k1B27JshHBYUzzoRTMWDtOk3XFHCjQIyy7UPmBxvesv3KYWJ7CYHmKD_A9xVaItyt24GRedHmgYmeuvV8LSD-GPu8NbOLN5MobZACFWBEeSiGrS5SEsc-hitdg_FgLYpL7zknCOXJGLr3RXJAsQGaUh04TSl4zeRs1B2yHyu4MfO_tGZ_gkMGovtjd042uIL61Wj9gq82MfO_tGZ_uERvxCNhXIl.; isg=BHR0zyHmoN_YKjScvFbssOWJRTLmTZg3ZDpCkA7ARv-oeQ7DNlkdxVl__bGhgdCP")
# print(t.live_overview("20250713","20250715"))
