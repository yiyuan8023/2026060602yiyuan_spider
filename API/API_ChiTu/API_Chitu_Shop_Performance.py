"""
开发说明：
- 作者：一元
- 创建时间：2025-06-26 16:17:00
- 最近修改：2026-06-10 17:30:00
- 文件用途：封装赤兔店铺绩效相关导出任务创建、下载和 Excel 解析能力。
- 业务范围：适用于赤兔店铺绩效商品咨询分析报表导出。
- 依赖入口：使用 ChituBaseAPI、excel_tool.reader.read_excel_to_dict、extra.logger_。
- 验收方式：修改后执行 py_compile、导入探针；接口变更后用单店铺单日期验证导出任务和解析行数。
- 注意事项：API 层不写数据库；非 Excel 内容必须按赤兔错误处理，不得继续解析。
"""

from API.API_ChiTu.API_Chitu_Base import ChituBaseAPI, ChituReportError
from API.API_ChiTu.API_Chitu_Clear_A_Glance import is_excel_content
from excel_tool.reader import read_excel_to_dict
from extra.logger_ import logger


class ChituShopPerformanceAPI(ChituBaseAPI):
    def __init__(self, cookie, password, shop_name):
        super().__init__(cookie=cookie, password=password, shop_name=shop_name)

    def build_product_consultation_payload(self, start_date, end_date):
        return {
            "dateType": "dateRange",
            "chatItemType": "ALL",
            "range": {"from": start_date, "to": end_date},
            "quickDate": None,
            "from": start_date,
            "to": end_date,
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
            "excludeBuyerLink": True,
        }

    def product_consultation_analysis(self, start_date, end_date):
        payload = self.build_product_consultation_payload(start_date, end_date)
        task_id = self.create_export(payload)
        export_content = self.download_export(task_id)
        if not is_excel_content(export_content):
            raise ChituReportError(f"{self.shop_name} 赤兔商品咨询分析下载内容不是 Excel")

        records = read_excel_to_dict(export_content)
        logger.info(
            f"{self.shop_name} 赤兔商品咨询分析 {start_date}-{end_date} "
            f"解析行数: {len(records or [])}"
        )
        return records or []
