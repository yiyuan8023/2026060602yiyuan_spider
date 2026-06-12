# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:40:00
- 最近修改：2026-06-10 21:40:00
- 文件用途：封装拼多多数据中心服务数据接口请求，返回平台原始 JSON。
- 业务范围：适用于服务数据-售后数据接口，日期和目标表由任务脚本配置。
- 依赖入口：使用 API.API_Pdd.API_Pdd_Base.PddBaseApi。
- 验收方式：修改后执行 py_compile 和 API_Pdd 包导入探针；真实请求由单店铺单日期任务验证。
- 注意事项：API 层不处理店铺、字段中文映射、唯一 key 和数据库写入。
"""

from typing import Any, Dict, Optional

from API.API_Pdd.API_Pdd_Base import PddBaseApi


class PddServiceApi(PddBaseApi):
    """拼多多数据中心服务数据接口。"""

    def after_sales_data(self, stat_day: str) -> Optional[Dict[str, Any]]:
        """服务数据-售后数据。"""
        payload = {
            "queryDate": stat_day,
            "crawlerInfo": "",
        }
        return self.post_json(
            "https://mms.pinduoduo.com/sydney/api/saleQuality/querySaleQualityDetailInfo",
            payload,
            context="拼多多服务售后数据",
        )
