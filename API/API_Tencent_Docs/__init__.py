# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-25 18:27:44
- 最近修改：2026-06-25 18:27:44
- 文件用途：提供腾讯文档 API 包的统一导出入口，暴露文件导出类和深圳KA发货明细解析函数。
- 业务范围：适用于 jobs 下腾讯文档任务对 API_Tencent_Docs 包的稳定导入。
- 依赖入口：使用 API_Tencent_Docs_File.TencentDocsFileApi 和 parser_shenzhen_ka_delivery。
- 验收方式：执行 py_compile，并执行包导入探针。
- 注意事项：只维护包级导入，不写平台 Cookie、业务表名或数据库逻辑。
"""

from API.API_Tencent_Docs.API_Tencent_Docs_File import TencentDocsFileApi
from API.API_Tencent_Docs.parser_anhui_bicheng_huimaimai_2026_order import (
    parse_anhui_bicheng_huimaimai_2026_order_records,
    validate_anhui_bicheng_huimaimai_2026_order_headers,
)
from API.API_Tencent_Docs.parser_anhui_ka_delivery import (
    parse_anhui_ka_delivery_records,
    validate_anhui_ka_delivery_headers,
)
from API.API_Tencent_Docs.parser_online_lead_assignment_dealer import (
    parse_online_lead_assignment_dealer_records,
    validate_online_lead_assignment_dealer_headers,
)
from API.API_Tencent_Docs.parser_shenzhen_ka_delivery import (
    parse_shenzhen_ka_delivery_records,
    validate_shenzhen_ka_delivery_headers,
)
from API.API_Tencent_Docs.parser_wanshang_youxuan_2026_delivery import (
    parse_wanshang_youxuan_2026_delivery_records,
    validate_wanshang_youxuan_2026_delivery_headers,
)

__all__ = [
    "TencentDocsFileApi",
    "parse_anhui_bicheng_huimaimai_2026_order_records",
    "validate_anhui_bicheng_huimaimai_2026_order_headers",
    "parse_anhui_ka_delivery_records",
    "validate_anhui_ka_delivery_headers",
    "parse_online_lead_assignment_dealer_records",
    "validate_online_lead_assignment_dealer_headers",
    "parse_shenzhen_ka_delivery_records",
    "validate_shenzhen_ka_delivery_headers",
    "parse_wanshang_youxuan_2026_delivery_records",
    "validate_wanshang_youxuan_2026_delivery_headers",
]
