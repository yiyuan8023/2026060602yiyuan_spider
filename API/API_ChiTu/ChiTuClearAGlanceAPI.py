# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-04-29
# Time: 10:47
# Project: jide
# File: ChiTuClearAGlanceAPI
# -*- coding: utf-8 -*-
# @Time : 2024/8/27 16:53
# @Author : Shao0000
# @Email : Shao0000@aliyun.com
# @File : ChiTuClearAGlanceAPI.py
# @Project : ChiTuPro
import io
from urllib.parse import urlencode

import numpy as np
import pandas as pd


import requests
from API.API_ChiTu.ChiTuBaseAPI import ChiTuABasePI
from logger_ import logger

"""
赤兔》》一目了然
"""


class ChiTuClearAGlanceAPI(ChiTuABasePI):
    def __init__(self, cookie, password):
        """
        初始化
        """
        super().__init__(cookie)
        self.password = password
        self.verify_status = self.verify_info()
        self.report_map = self.fetch_report_list()
        logger.info(f"ChiTuClearAGlanceAPI 初始化,导出报表状态:{self.verify_status}")
        logger.info(
            f"{self.shop_name} 赤兔一目了然自定义报表映射关系 {self.report_map}"
        )

    def fetch_report_list(self):
        """
        获取报表list
        """
        api = "https://kf.topchitu.com/api/report/"
        headers = {
            "User-Agent": self.ramdom_ua(),
            "referer": "https://kf.topchitu.com/web/homepage/team",
            "cookie": self.cookie,
        }
        res = requests.get(api, headers=headers)
        # print(res.json())
        self.req_log(res)
        report_map = {}
        for i in res.json():
            report_map[i["name"]] = {"id": i["id"], "shopKpi": i["shopKpi"]}
        return report_map

    # def verify_password(self):
    #     """
    #     密码验证
    #     """
    #     api = "https://kf.topchitu.com/api/export-verify/verify-password"
    #     data = {
    #         "password": self.password
    #     }
    #     headers = {
    #         "User-Agent": self.ramdom_ua(),
    #         "cookie": self.cookie,
    #         "content-type": "application/json"
    #     }
    #     res = requests.post(url=api, data=json.dumps(data), headers=headers)
    #     if res.status_code == 200 and not res.text:
    #         logger.success("密码正确")
    #         return True
    #     else:
    #         logger.error("密码错误")
    #         return False
    #
    # def verify_info(self):
    #     """
    #     验证导出状态
    #     """
    #     api = "https://kf.topchitu.com/api/export-verify/export-verify-info"
    #     headers = {
    #         "User-Agent": self.ramdom_ua(),
    #         "cookie": self.cookie,
    #     }
    #     res = requests.get(api, headers=headers)
    #     self.req_log(res)
    #     verify_status = res.json()["exportVerifyStatus"]
    #     if verify_status:
    #         return verify_status
    #     else:
    #         return self.verify_password()

    def export_table(self, report_name, from_, to_):
        """, from_, to_
        报表导出
        """
        if report_name in self.report_map.keys():
            report_id = self.report_map[report_name]["id"]
            shopKpi = self.report_map[report_name]["shopKpi"]
            if shopKpi:
                kpiType = "shop"
                exportType = "CUSTOM_SHOP_KPI"
            else:
                kpiType = "ww"
                exportType = "CUSTOM_WW_KPI"
            api = "https://kf.topchitu.com/api/export/kpi?"
            params = {
                "dateType": "dateRange",
                "range": "[object Object]",
                "from": from_,
                "to": to_,
                "queryDateType": "DAY",
                "filterDays": "",
                "exportType": exportType,
                "showDelayData": "false",
                "kpiType": kpiType,
                "reportId": report_id,
                "handleSubmit": "true",
                "customExport": "false",
                "wangwangExpandColumns": "",
                "_version": "21",
            }
            headers = {
                "User-Agent": self.ramdom_ua(),
                "cookie": self.cookie,
            }
            url = api + urlencode(params)
            res = requests.get(url, headers=headers)
            self.req_log(res)
            try:
                data = io.BytesIO(res.content)
                df = pd.read_excel(data)
                df.replace({np.nan: ""}, inplace=True)
                items = df.to_dict("records")
                return items
            except Exception as e:
                logger.error(f"{res.text},错误信息：{e}")
                return None
        else:
            logger.error(f"该{report_name}未创建")
            return None
