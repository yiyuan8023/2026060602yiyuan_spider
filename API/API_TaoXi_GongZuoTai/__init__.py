"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:24:53
- 最近修改：2026-06-12 18:21:46
- 文件用途：声明淘系商家工作台 API 包对外入口，集中暴露宝贝报表、订单报表、退款报表、价保管理、订单详情 API 和订单详情解析函数。
- 业务范围：适用于调用 API_TaoXi_GongZuoTai 包的任务脚本、导入探针和后续商家工作台能力扩展。
- 依赖入口：使用 API_TaoXi_GongZuoTai_Trade.TaoXiGongZuoTaiTradeApi、API_TaoXi_GongZuoTai_OrderReport.TaoXiGongZuoTaiOrderReportApi、API_TaoXi_GongZuoTai_RefundReport.TaoXiGongZuoTaiRefundReportApi、API_TaoXi_GongZuoTai_PriceProtection.TaoXiGongZuoTaiPriceProtectionApi、API_TaoXi_GongZuoTai_OrderDetail.TaoXiGongZuoTaiOrderDetailApi 和 parser_order_discount_details.parse_order_discount_details。
- 验收方式：修改后执行 py_compile；执行包导入探针验证 __all__ 暴露入口。
- 注意事项：包入口只做导出，不放业务配置、真实 Cookie、数据库写入或平台请求。
"""

from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Trade import (
    TaoXiGongZuoTaiTradeApi,
)
from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_OrderReport import (
    TaoXiGongZuoTaiOrderReportApi,
)
from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_RefundReport import (
    TaoXiGongZuoTaiRefundReportApi,
)
from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_PriceProtection import (
    TaoXiGongZuoTaiPriceProtectionApi,
)
from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_OrderDetail import (
    TaoXiGongZuoTaiOrderDetailApi,
)
from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_GovSubsidyAudit import (
    TaoXiGongZuoTaiGovSubsidyAuditApi,
)
from API.API_TaoXi_GongZuoTai.parser_order_discount_details import (
    parse_order_discount_details,
)

__all__ = [
    "TaoXiGongZuoTaiGovSubsidyAuditApi",
    "TaoXiGongZuoTaiOrderDetailApi",
    "TaoXiGongZuoTaiOrderReportApi",
    "TaoXiGongZuoTaiPriceProtectionApi",
    "TaoXiGongZuoTaiRefundReportApi",
    "TaoXiGongZuoTaiTradeApi",
    "parse_order_discount_details",
]
