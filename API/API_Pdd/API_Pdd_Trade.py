# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:40:00
- 最近修改：2026-06-10 21:40:00
- 文件用途：封装拼多多数据中心交易数据接口请求，返回平台原始 JSON 和必要的字体映射。
- 业务范围：适用于交易数据-数据总览接口，日期范围和入库表由任务脚本配置。
- 依赖入口：使用 API.API_Pdd.API_Pdd_Base.PddBaseApi。
- 验收方式：修改后执行 py_compile 和 API_Pdd 包导入探针；真实请求由单店铺单日期任务验证。
- 注意事项：API 层不处理店铺列表、目标表名、字段中文映射和数据库写入。
"""

from typing import Any, Dict, Optional, Tuple

from API.API_Pdd.API_Pdd_Base import PddBaseApi


class PddTradeApi(PddBaseApi):
    """拼多多数据中心交易数据接口。"""

    def trade_overview(
        self,
        start_date: str,
        end_date: str,
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, str]]:
        """交易数据-数据总览。"""
        headers, font_mapping = self.build_font_headers_and_mapping()
        payload = {
            "queryType": 7,
            "queryDate": end_date,
            "startDate": start_date,
            "endDate": end_date,
        }
        response_json = self.post_json(
            "https://mms.pinduoduo.com/sydney/api/mallTrade/queryMallTradeList",
            payload,
            headers=headers,
            context="拼多多交易数据总览",
        )
        return response_json, font_mapping
