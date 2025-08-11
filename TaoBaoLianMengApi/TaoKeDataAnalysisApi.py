# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-04-21
# Time: 13:31
# Project: jide
# File: TaoKeDataAnalysis

import requests

from TaoBaoLianMengApi.TaoKeBaseApi import TaoKeBaseApi
from extra.extra_date import get_millisecond_timestamp
from extra.extra_reqlog import req_log
from extra.logger_ import logger

from cookie_manager.extra_cookie import get_cookie_value


class TaoKeDataAnalysisApi(TaoKeBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def goods_analysis__goods_management(self,start_time,end_time):
        """
        商品分析》》商品管理
        :return:
        """
        url = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/shopkeeper.rpt.taskstart.json"
        params = {
            "t": get_millisecond_timestamp(),
            "_tb_token_": get_cookie_value(self.cookie,'_tb_token_'),
            "startTime": f"{start_time} 00:00:00",
            "endTime": f"{end_time} 23:59:59",
            "bizType": 126,
            "ext": '{"level3Dim":null,"orderMetric":"alipayAmt","orderType":"desc"}'
        }
        # data = json.dumps(data, separators=(',', ':'))
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": self.cookie,
            "user-agent":self.ua,
            "referer":"https://ad.alimama.com/portal/v2/report/item/list.htm",
            "origin": "https://ad.alimama.com",
            'Host': 'ad.alimama.com',
        }
        res=requests.get(url=url, headers=headers, params=params)
        if req_log(res):
            logger.success(f'成功！！！创建任务日期:{start_time}')
            return res.json()
        else:
            logger.error(f'失败！！！创建任务日期:{start_time}')
            return None

# TaoKeDataAnalysisobj=TaoKeDataAnalysisApi("dnk=; t=61f6d9516106249f280ae435a10c9a79; lgc=; wk_cookie2=1de33e37072f0ef696f0385c1905c161; _tb_token_=313e8b0136b3; wk_unb=UoH%2B4NPsNoWZlw%3D%3D; cookie2=154930697d8a50696d572651f93a5a2b; _nk_=; cna=QpKMIIUcNlICASeqbVq05Ozi; xlly_s=1; uc1=cookie14=UoYajlesvxuitQ%3D%3D&cookie21=W5iHLLyFfoaZ; lid=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; unb=2212373938588; sgcookie=E100eK9lKaPAvPh32Rhx0Wrk22pCjCjkxB5bozkp8amFcgczA32rvWtf1NHfxUu2ojxtBs783DIwl9uxSO34BRayC0%2Bb7lIdr%2FyMhdwJdjXBG549bamGOo6ypc%2B71miUKwlv; cancelledSubSites=empty; csg=2f4422ce; sn=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; t_alimama=61a98c96f54dedf558765806181d701a; cookie2_alimama=19a2abd438b281694af2208a040b428a; v_alimama=0; rurl=aHR0cHM6Ly9hZC5hbGltYW1hLmNvbS9pbmRleC5odG0%2FZm9yd2FyZD1odHRwcyUzQSUyRiUyRmFkLmFsaW1hbWEuY29tJTJGcG9ydGFsJTJGdjIlMkZyZXBvcnQlMkZpdGVtJTJGbGlzdC5odG0%3D; _m_h5_c=6a5c8b7aa8045e90516350f359fe6a7d_1745223219638%3B3a04235078f07f07512f5242c8c14469; tfstk=gxktDiGH_eYGwNwkIdOhi6XQPkKhqBjZbu01nt20SBgLRqH0GCuDHx3mJhPX7RDxJmuUmtAZo2CbDyrms-2gGoaIWtcijRtvHmi7Gq4mjGlEr06iICycHRy4hUYkELmib-ybnpuDJ1WQDuvc1-O3dEXkwvTkELm61lymAUDDxFBT5uXbh5NfOwaU4N6jlS6IAyr4cNZfCHnQ8y61h1a_OMZ74r6jl-tKAyrbhlG5U1UVgr6xa5Suv3IGvcnZplFTPDdPhtB_ea2SfXBAHSr761m_Jt6jpjFCm3z6aM44IPoLXqJPQRNxGA2ICe9bFbuKH7wJihPsDX34Ivtf1zGiSJMswi6jvRUjyvVdWeUSQDMzdWvW2DMESckKmi9bx44IbAwvF3yTCPwLYxYFCrhIGAVa3NTYuvnICjIriYDRw__uyof6vHCVg5ZeyUqq_cjFPuZLrHmhgsPHNkUkvHCVg5ZUvzx3rs54tQ1..")
# TaoKeDataAnalysisobj.goods_Analysis__goods_management("2025-04-19","2025-04-19")
# TaoKeDataAnalysisobj.task_status_list()