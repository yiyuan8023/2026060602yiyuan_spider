# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:40:00
- 最近修改：2026-06-10 21:40:00
- 文件用途：封装拼多多数据中心流量数据接口请求，返回平台原始 JSON。
- 业务范围：适用于流量数据-流量看板-数据总览接口，日期和目标表由任务脚本配置。
- 依赖入口：使用 API.API_Pdd.API_Pdd_Base.PddBaseApi。
- 验收方式：修改后执行 py_compile 和 API_Pdd 包导入探针；真实请求由单店铺单日期任务验证。
- 注意事项：API 层不做中文字段映射、不生成唯一 key、不执行数据库写入。
"""

from typing import Any, Dict, Optional

from API.API_Pdd.API_Pdd_Base import PddBaseApi


class PddFlowApi(PddBaseApi):
    """拼多多数据中心流量数据接口。"""

    def flow_board_overview(self, begin_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """流量数据-流量看板-数据总览。"""
        payload = {
            "beginDate": begin_date,
            "crawlerInfo": "",
            "endDate": end_date,
        }
        return self.post_json(
            "https://mms.pinduoduo.com/sydney/api/mallFlow/queryMallFlowOverView",
            payload,
            context="拼多多流量看板数据总览",
        )
