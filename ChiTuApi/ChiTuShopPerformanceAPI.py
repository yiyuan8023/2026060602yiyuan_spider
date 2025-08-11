# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-06-26
# Time: 16:17
# Project: jide
# File: ChiTuShopPerformanceAPI
import io
import json
from urllib.parse import urlencode

import numpy as np
import pandas as pd

import requests
from ChiTuApi.ChiTuBaseAPI import ChiTuABasePI
from logger_ import logger

"""
赤兔》》店铺绩效
"""


class ChiTuShopPerformanceAPI(ChiTuABasePI):
    def __init__(self, cookie, password):
        """
        初始化
        """
        super().__init__(cookie)
        self.password = password
        self.verify_status = self.verify_info()
        logger.info(f"ChiTuShopPerformanceAPI 初始化,导出报表状态:{self.verify_status}")

    def product_consultation_analysis(self,from_,to_):
        """
        商品咨询分析
        :return:
        """
        data = {
            "dateType": "dateRange",
            "chatItemType": "ALL",
            "range": {
                "from": from_,
                "to": to_
            },
            "quickDate": None,
            "from": from_,
            "to": to_,
            "queryDateType": "DAY",
            "filterDays": [],
            "exportType": "SHOP_ITEM_ASK_V2",
            "showDelayData": False,
            "kpiType": "shop",
            "filterField": None,
            "sortField": "include_enter_shop_card_service_num",
            "sortDirection": "DESC",
            "handleSubmit": True,
            "itemViewType": "ITEM",
            "pageSize": 10,
            "pageNum": 1,
            "itemGroupType": "ITEM",
            "itemIds": [],
            "queryOneItem": False,
            "clickHouseSearch": True,
            "kpiCompareType": None,
            "customExport": True,
            "wangwangExpandColumns": [],
            "detailExport": False,
            "excludeBuyerLink": True
        }
        export_status,taskids=self.create_export(data)
        if export_status:
            export_content=self.export_download(taskids)
            try:
                data = io.BytesIO(export_content)
                df = pd.read_excel(data)
                df.replace({np.nan: ''}, inplace=True)
                items = df.to_dict('records')
                return items
            except Exception as e:
                logger.error(f"{export_content},错误信息：{e}")
                return None
