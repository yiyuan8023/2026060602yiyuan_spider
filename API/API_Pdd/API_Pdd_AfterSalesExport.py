# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-13 07:46:00
- 最近修改：2026-06-13 07:46:00
- 文件用途：封装拼多多售后工作台列表、分组统计、批量导出、已生成报表查询和 Excel 下载能力。
- 业务范围：适用于 https://mms.pinduoduo.com/aftersales/aftersale_list 的售后列表与报表导出链路；当前已验证老链路 /mercury/mms/afterSales/* 可用。
- 依赖入口：继承 API.API_Pdd.API_Pdd_Base.PddBaseApi，导出文件下载统一走 downloader.core.Downloader。
- 验收方式：修改后执行 py_compile 和 API_Pdd 包导入探针；真实请求时先用单店铺 Cookie 验证列表查询、报表列表和 Excel 下载。
- 注意事项：日志不得输出完整 Cookie、签名下载 URL 或报表敏感内容；正式任务脚本写库前先确认筛选区间和主键。
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

from downloader.core import Downloader
from extra.logger_ import logger

from API.API_Pdd.API_Pdd_Base import PddBaseApi


class PddAfterSalesExportApi(PddBaseApi):
    """拼多多售后工作台导出 API。"""

    BASE_URL = "https://mms.pinduoduo.com"
    AFTER_SALES_REFERER = f"{BASE_URL}/aftersales/aftersale_list?msfrom=mms_sidenav"

    QUERY_LIST_API = f"{BASE_URL}/mercury/mms/afterSales/queryList"
    QUERY_PARAMS_API = f"{BASE_URL}/mercury/mms/afterSales/queryParams"
    QUERY_COUNT_API = f"{BASE_URL}/mercury/mms/afterSales/queryCount"
    QUERY_GROUP_COUNT_API = f"{BASE_URL}/mercury/mms/afterSales/queryGroupCount"
    APPLY_EXCEL_REPORT_API = f"{BASE_URL}/mercury/mms/afterSales/applyExcelReport"
    QUERY_EXCEL_EXPORT_LIST_API = f"{BASE_URL}/mercury/mms/afterSales/queryExcelExportList"
    QUERY_EXCEL_REPORT_URL_API = f"{BASE_URL}/mercury/mms/afterSales/queryExcelReportUrl"

    NEW_APPLY_ASYNC_EXPORT_API = (
        f"{BASE_URL}/mercury/after_sales/apply_async_excel_export"
    )
    NEW_QUERY_ASYNC_EXPORT_LIST_API = (
        f"{BASE_URL}/mercury/after_sales/async_excel_export_list"
    )
    NEW_QUERY_EXCEL_URL_API = f"{BASE_URL}/mercury/after_sales/query_excel_url"

    STATUS_RUNNING = 1
    STATUS_SUCCESS = 2
    STATUS_FAILED = 3
    DEFAULT_PAGE_SIZE = 10
    DEFAULT_ROLE_ID = 1
    AFTER_SALES_USER_AGENT = "Mozilla/5.0"
    EXPORT_PAYLOAD_TEMPLATE = {
        "pageSize": DEFAULT_PAGE_SIZE,
        "quickSearchType": None,
        "searchText": None,
        "batchSearchList": None,
        "batchSearchType": None,
        "afterSalesType": None,
        "subAfterSalesTypeIn": None,
        "subAfterSalesTypeNotIn": None,
        "afterSalesStatusList": None,
        "reasonCodeList": None,
        "sellerAfterSalesShipping": None,
        "operateType": None,
        "minRefundAmount": None,
        "maxRefundAmount": None,
        "startCreatedTime": None,
        "endCreatedTime": None,
        "startCloseTime": None,
        "endCloseTime": None,
        "logisticsRecallStatusList": None,
        "platformJoined": None,
        "speedRefund": None,
        "disputeRefund": None,
        "merchantAppeal": None,
        "promiseSecondShipWaitShip": None,
        "orderByExpireTimeAsc": None,
        "orderByCreatedAtDesc": None,
        "pageNumber": 1,
        "mallId": None,
        "userId": None,
        "roleId": DEFAULT_ROLE_ID,
        "userName": None,
        "mallRemarkStatus": None,
        "mallRemarkTag": None,
        "assignedProcessorId": None,
        "assignedProcessorStatus": None,
        "fromAfterSalesListPage": None,
    }

    def build_after_sales_headers(self) -> Dict[str, str]:
        """补充售后工作台请求头。"""
        headers = self.build_headers()
        headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json;charset=UTF-8",
                "Origin": self.BASE_URL,
                "Referer": self.AFTER_SALES_REFERER,
                "User-Agent": self.AFTER_SALES_USER_AGENT,
            }
        )
        return headers

    def query_params(self) -> Dict[str, Any]:
        """查询售后页面筛选配置。"""
        return self.post_json(
            self.QUERY_PARAMS_API,
            {},
            headers=self.build_after_sales_headers(),
            context="拼多多售后工作台筛选参数",
        ) or {}

    def query_count(self) -> Dict[str, Any]:
        """查询顶部快捷统计。"""
        return self.post_json(
            self.QUERY_COUNT_API,
            {},
            headers=self.build_after_sales_headers(),
            context="拼多多售后工作台顶部统计",
        ) or {}

    def query_group_count(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """查询售后分组数量。"""
        normalized_payload = self._normalize_list_payload(payload)
        return self.post_json(
            self.QUERY_GROUP_COUNT_API,
            normalized_payload,
            headers=self.build_after_sales_headers(),
            context="拼多多售后工作台分组统计",
        ) or {}

    def query_list(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """查询售后列表。"""
        normalized_payload = self._normalize_list_payload(payload)
        return self.post_json(
            self.QUERY_LIST_API,
            normalized_payload,
            headers=self.build_after_sales_headers(),
            context="拼多多售后工作台列表",
        ) or {}

    def query_export_list(self) -> List[Dict[str, Any]]:
        """查询“查看已生成报表”列表。"""
        response_json = self.post_json(
            self.QUERY_EXCEL_EXPORT_LIST_API,
            {},
            headers=self.build_after_sales_headers(),
            context="拼多多售后工作台已生成报表列表",
        ) or {}
        result = response_json.get("result") or []
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        if isinstance(result, dict):
            page_items = result.get("pageItems") or result.get("list") or []
            return [item for item in page_items if isinstance(item, dict)]
        return []

    def query_async_export_list(self) -> List[Dict[str, Any]]:
        """查询新版异步导出列表。当前店铺下可为空。"""
        response_json = self.post_json(
            self.NEW_QUERY_ASYNC_EXPORT_LIST_API,
            {},
            headers=self.build_after_sales_headers(),
            context="拼多多售后工作台异步报表列表",
        ) or {}
        result = response_json.get("result") or []
        return [item for item in result if isinstance(item, dict)]

    def apply_excel_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """提交老链路批量导出任务。"""
        normalized_payload = self.normalize_export_payload(payload)
        response_json = self.post_json(
            self.APPLY_EXCEL_REPORT_API,
            normalized_payload,
            headers=self.build_after_sales_headers(),
            context="拼多多售后工作台批量导出申请",
        ) or {}
        self._ensure_success(response_json, context="拼多多售后工作台批量导出申请")
        return response_json

    def query_excel_report_url(self, report_id: Any) -> str:
        """查询老链路导出文件下载地址。"""
        payload = {"id": report_id}
        response_json = self.post_json(
            self.QUERY_EXCEL_REPORT_URL_API,
            payload,
            headers=self.build_after_sales_headers(),
            context=f"拼多多售后工作台报表下载地址 report_id={report_id}",
        ) or {}
        if self._response_success(response_json):
            download_url = self._extract_download_url(response_json)
            if download_url:
                return download_url

        fallback_json = self.post_json(
            self.NEW_QUERY_EXCEL_URL_API,
            payload,
            headers=self.build_after_sales_headers(),
            context=f"拼多多售后工作台新版报表下载地址 report_id={report_id}",
        ) or {}
        self._ensure_success(fallback_json, context="拼多多售后工作台报表下载地址")
        download_url = self._extract_download_url(fallback_json)
        if not download_url:
            raise RuntimeError(f"售后导出报表 {report_id} 未返回可用下载地址")
        return download_url

    def download_export_records(self, download_url: str) -> List[Dict[str, Any]]:
        """下载售后导出 Excel 并返回字典列表。"""
        records = Downloader(
            api=download_url,
            cookie=self.cookie,
            timeout=60,
            context="拼多多售后工作台报表下载",
        ).download_excel(engine="openpyxl", validate_excel=True)
        return records if isinstance(records, list) else []

    def export_after_sales_records(
        self,
        payload: Dict[str, Any],
        *,
        timeout_seconds: int = 300,
        poll_seconds: int = 30,
    ) -> List[Dict[str, Any]]:
        """创建售后导出任务，等待生成完成后下载解析 Excel。"""
        normalized_payload = self.normalize_export_payload(payload)
        previous_report_ids = self.collect_report_ids(self.query_export_list())
        self.apply_excel_report(normalized_payload)
        report = self.wait_report_ready(
            normalized_payload,
            previous_report_ids=previous_report_ids,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
        )
        report_id = report.get("id")
        if report_id in ("", None):
            raise RuntimeError("售后导出报表已生成，但未拿到报表 ID")
        download_url = self.query_excel_report_url(report_id)
        return self.download_export_records(download_url)

    def wait_report_ready(
        self,
        payload: Dict[str, Any],
        *,
        previous_report_ids: Optional[Set[Any]] = None,
        timeout_seconds: int = 300,
        poll_seconds: int = 30,
    ) -> Dict[str, Any]:
        """轮询报表列表，等待指定导出任务生成完成。"""
        deadline = time.time() + timeout_seconds
        previous_report_ids = set(previous_report_ids or set())
        last_seen_status = None

        while time.time() <= deadline:
            reports = self.query_export_list()
            report = self.find_best_matching_report(
                reports,
                payload=payload,
                previous_report_ids=previous_report_ids,
            )
            if report:
                status = report.get("status")
                if status != last_seen_status:
                    logger.info(
                        f"{self.shop_name or '拼多多店铺'} 售后导出报表状态更新，"
                        f"report_id={report.get('id')}，status={status}，"
                        f"apply_time={report.get('applyTime')}，generate_time={report.get('generateTime')}"
                    )
                    last_seen_status = status

                if status == self.STATUS_SUCCESS:
                    return report
                if status == self.STATUS_FAILED:
                    raise RuntimeError(f"售后导出报表生成失败，report_id={report.get('id')}")
            else:
                logger.info(f"{self.shop_name or '拼多多店铺'} 暂未在报表列表匹配到目标售后导出任务")

            time.sleep(max(poll_seconds, 1))

        raise TimeoutError(f"等待拼多多售后导出报表完成超时，已等待 {timeout_seconds} 秒")

    def normalize_export_payload(self, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """按页面真实字段整理导出入参。"""
        normalized_payload = dict(self.EXPORT_PAYLOAD_TEMPLATE)
        normalized_payload.update(payload or {})

        identity_defaults = self.get_export_identity_defaults()
        if not normalized_payload.get("roleId"):
            normalized_payload["roleId"] = identity_defaults.get("roleId") or self.DEFAULT_ROLE_ID
        if not normalized_payload.get("userName"):
            normalized_payload["userName"] = identity_defaults.get("userName")

        required_fields = ("startCreatedTime", "endCreatedTime")
        missing_fields = [field_name for field_name in required_fields if not normalized_payload.get(field_name)]
        if missing_fields:
            raise ValueError(f"售后导出缺少必要时间范围字段: {missing_fields}")
        return normalized_payload

    def get_export_identity_defaults(self) -> Dict[str, Any]:
        """从已生成报表中回填导出身份字段。"""
        reports = self.query_export_list()
        if not reports:
            return {"roleId": self.DEFAULT_ROLE_ID, "userName": None}

        latest_report = reports[0]
        request_obj = latest_report.get("requestObj") or {}
        return {
            "roleId": request_obj.get("roleId") or self.DEFAULT_ROLE_ID,
            "userName": request_obj.get("userName") or latest_report.get("operatorName"),
        }

    @classmethod
    def collect_report_ids(cls, reports: Sequence[Dict[str, Any]]) -> Set[Any]:
        """收集当前报表列表中的报表 ID。"""
        report_ids: Set[Any] = set()
        for report in reports:
            report_id = report.get("id")
            if report_id not in ("", None):
                report_ids.add(report_id)
        return report_ids

    def find_best_matching_report(
        self,
        reports: Iterable[Dict[str, Any]],
        *,
        payload: Dict[str, Any],
        previous_report_ids: Set[Any],
    ) -> Optional[Dict[str, Any]]:
        """按 requestObj 和时间区间匹配最新报表。"""
        normalized_payload = self.normalize_export_payload(payload)
        matched_reports: List[Dict[str, Any]] = []
        for report in reports:
            report_id = report.get("id")
            if previous_report_ids and report_id in previous_report_ids:
                continue
            if not self._report_matches_payload(report, normalized_payload):
                continue
            matched_reports.append(report)

        if not matched_reports:
            return None

        matched_reports.sort(
            key=lambda item: (
                int(item.get("applyTime") or 0),
                int(item.get("id") or 0),
            ),
            reverse=True,
        )
        return matched_reports[0]

    @staticmethod
    def _normalize_list_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        normalized_payload = {"pageNumber": 1, "pageSize": 10}
        if payload:
            normalized_payload.update(payload)
        return normalized_payload

    @staticmethod
    def _extract_download_url(response_json: Optional[Dict[str, Any]]) -> str:
        if not isinstance(response_json, dict):
            return ""
        result = response_json.get("result")
        if isinstance(result, str) and result.strip():
            return result.strip()
        if isinstance(result, dict):
            for key in ("excelUrl", "downloadUrl", "url", "fileUrl"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return ""

    @staticmethod
    def _response_success(response_json: Optional[Dict[str, Any]]) -> bool:
        return bool(isinstance(response_json, dict) and response_json.get("success") is True)

    @classmethod
    def _ensure_success(cls, response_json: Optional[Dict[str, Any]], *, context: str):
        if cls._response_success(response_json):
            return
        if isinstance(response_json, dict):
            error_message = response_json.get("errorMsg") or response_json.get("message") or "未知错误"
            raise RuntimeError(f"{context}失败: {error_message}")
        raise RuntimeError(f"{context}失败: 未返回有效 JSON")

    def _report_matches_payload(self, report: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        request_obj = report.get("requestObj") or {}
        comparable_fields = (
            "startCreatedTime",
            "endCreatedTime",
            "quickSearchType",
            "searchText",
            "batchSearchType",
            "afterSalesType",
            "sellerAfterSalesShipping",
            "operateType",
            "userName",
            "roleId",
        )
        for field_name in comparable_fields:
            payload_value = payload.get(field_name)
            report_value = request_obj.get(field_name)
            if payload_value in ("", None, []):
                if report_value in ("", None, []):
                    continue
                continue
            if str(payload_value) != str(report_value):
                return False
        return True
