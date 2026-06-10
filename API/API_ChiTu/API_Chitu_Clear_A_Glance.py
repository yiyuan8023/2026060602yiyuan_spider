"""
开发说明：
- 作者：一元
- 创建时间：2025-04-29 10:47:00
- 最近修改：2026-06-10 17:30:00
- 文件用途：封装赤兔一目了然自定义报表列表获取和 Excel 导出解析能力。
- 业务范围：适用于赤兔一目了然「店铺/客服」自定义报表导出，具体报表名由任务脚本 SHOP_CONFIGS 配置。
- 依赖入口：使用 ChituBaseAPI、requests、excel_tool.reader.read_excel_to_dict、extra.logger_。
- 验收方式：修改后执行 py_compile、导入探针，并用单店铺单日期验证报表列表、密码校验、Excel 导出和解析。
- 注意事项：API 层不写业务表；非 Excel 响应必须按赤兔错误处理，不得继续解析。
"""

from urllib.parse import urlencode

import requests

from API.API_ChiTu.API_Chitu_Base import ChituBaseAPI, ChituReportError
from excel_tool.reader import read_excel_to_dict
from extra.logger_ import logger


REPORT_LIST_API = "https://kf.topchitu.com/api/report/"
CUSTOM_KPI_EXPORT_API = "https://kf.topchitu.com/api/export/kpi?"
EXCEL_MAGIC_BYTES = (b"PK", b"\xd0\xcf\x11\xe0")


def is_excel_content(content):
    return bool(content) and content.startswith(EXCEL_MAGIC_BYTES)


class ChituClearAGlanceAPI(ChituBaseAPI):
    def __init__(self, cookie, password, shop_name):
        super().__init__(cookie=cookie, password=password, shop_name=shop_name)
        self.report_map = self.fetch_report_map()
        logger.info(
            f"{self.shop_name} 赤兔一目了然可用报表: {', '.join(self.report_map.keys())}"
        )

    def fetch_report_map(self):
        headers = self._headers({"referer": "https://kf.topchitu.com/web/homepage/team"})
        response = requests.get(REPORT_LIST_API, headers=headers, timeout=30)
        self._log_response(response, "获取一目了然报表列表")
        if response.status_code != 200:
            raise ChituReportError(f"{self.shop_name} 赤兔获取报表列表失败")

        report_map = {}
        for report in response.json():
            report_map[report["name"]] = {
                "id": report["id"],
                "shopKpi": report["shopKpi"],
            }
        return report_map

    def ensure_report(self, report_name):
        if report_name in self.report_map:
            return self.report_map[report_name]

        available_reports = ", ".join(self.report_map.keys())
        raise ChituReportError(
            f"{self.shop_name} 赤兔报表未创建: {report_name}; "
            f"可用报表: {available_reports}"
        )

    def build_export_params(self, report_name, start_date, end_date):
        report = self.ensure_report(report_name)
        if report["shopKpi"]:
            kpi_type = "shop"
            export_type = "CUSTOM_SHOP_KPI"
        else:
            kpi_type = "ww"
            export_type = "CUSTOM_WW_KPI"

        return {
            "dateType": "dateRange",
            "range": "[object Object]",
            "from": start_date,
            "to": end_date,
            "queryDateType": "DAY",
            "filterDays": "",
            "exportType": export_type,
            "showDelayData": "false",
            "kpiType": kpi_type,
            "reportId": report["id"],
            "handleSubmit": "true",
            "customExport": "false",
            "wangwangExpandColumns": "",
            "_version": "21",
        }

    def export_table(self, report_name, start_date, end_date):
        params = self.build_export_params(report_name, start_date, end_date)
        url = CUSTOM_KPI_EXPORT_API + urlencode(params)
        response = requests.get(url, headers=self._headers(), timeout=60)
        self._log_response(response, f"导出一目了然报表 {report_name}")
        if response.status_code != 200:
            raise ChituReportError(
                f"{self.shop_name} 赤兔导出报表失败: "
                f"{response.status_code}, {self._summarize_response(response)}"
            )

        if not is_excel_content(response.content):
            raise ChituReportError(
                f"{self.shop_name} 赤兔导出内容不是 Excel: "
                f"{self._summarize_response(response)}"
            )

        records = read_excel_to_dict(response.content)
        logger.info(
            f"{self.shop_name} 赤兔报表 {report_name} "
            f"{start_date}-{end_date} 解析行数: {len(records or [])}"
        )
        return records or []
