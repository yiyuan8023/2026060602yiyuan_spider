# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-23 19:05:00
- 最近修改：2026-06-23 19:05:00
- 文件用途：封装商家工作台国家补贴审计工作台订单导出接口，负责审计订单查询、导出任务创建、任务列表查询和 Excel 下载解析。
- 业务范围：适用于 https://myseller.taobao.com/home.htm/gov-subsidy/audit-manage 的“审计管理-订单导出”。
- 依赖入口：继承 TaoXiGongZuoTaiBaseApi，使用 downloader.core.Downloader 解析平台导出的 Excel。
- 验收方式：执行 py_compile；用单店铺查询导出记录和下载最新成功任务验证字段、行数、目标表写入。
- 注意事项：不记录完整 Cookie、签名下载 URL 或平台敏感参数；任务创建和下载由 job 层控制。
"""

import json
from time import sleep

from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Base import (
    TaoXiGongZuoTaiBaseApi,
)
from downloader.core import Downloader
from extra.extra_error import handle_request_error
from extra.logger_ import logger


class TaoXiGongZuoTaiGovSubsidyAuditApi(TaoXiGongZuoTaiBaseApi):
    """国家补贴审计工作台 API。"""

    AUDIT_REFERER = "https://myseller.taobao.com/home.htm/gov-subsidy/audit-manage"
    AUDIT_ORDER_QUERY_API = "mtop.alibaba.sc.center.gov.subsidy.audit.order.query"
    AUDIT_SYNC_JOB_CREATE_API = "mtop.alibaba.sc.center.gov.subsidy.audit.syncJob.create"
    AUDIT_SYNC_JOB_QUERY_API = "mtop.alibaba.sc.center.gov.subsidy.audit.syncJob.query"

    EXPORT_TASK_TYPE = "4"
    TASK_STATUS_SUCCESS = "5"
    TASK_QUERY_PAGE_SIZE = 50
    TASK_QUERY_MAX_PAGES = 8

    def query_audit_order_list(self, params):
        """只读查询审计订单列表，用于确认筛选条件和导出总量。"""
        return self.mtop_request(
            self.AUDIT_ORDER_QUERY_API,
            params,
            referer=self.AUDIT_REFERER,
        )

    def query_audit_export_tasks(self, page=1, page_size=10, types_str=EXPORT_TASK_TYPE):
        """查询审计工作台导出记录。"""
        return self.mtop_request(
            self.AUDIT_SYNC_JOB_QUERY_API,
            {
                "pageIndex": page,
                "pageSize": page_size,
                "typesStr": types_str,
            },
            referer=self.AUDIT_REFERER,
            log_success=page == 1,
        )

    def create_audit_order_export(self, params):
        """创建审计订单导出任务。"""
        request = {
            "govSubsidyAuditOrderRequest": params,
        }
        create_data = self.mtop_request(
            self.AUDIT_SYNC_JOB_CREATE_API,
            {
                "request": json.dumps(request, ensure_ascii=False, separators=(",", ":")),
                "type": self.EXPORT_TASK_TYPE,
            },
            referer=self.AUDIT_REFERER,
        )
        logger.info(
            f"国家补贴审计订单导出任务创建返回: "
            f"{self._summarize_create_response(create_data)}"
        )
        return create_data

    def export_audit_order_records(
        self,
        params,
        max_retries=10,
        sleep_seconds=60,
    ):
        """创建导出任务，轮询成功后下载 Excel 明细。"""
        export_params = self._with_total_page_size(params)
        create_data = self.create_audit_order_export(export_params)
        create_task_ids = self._extract_task_identifiers(create_data)
        if create_task_ids:
            logger.info(f"国家补贴审计订单导出创建任务标识: {sorted(create_task_ids)}")

        tracked_task_ids = set(create_task_ids)
        last_matching_tasks = []
        for retry_index in range(1, max_retries + 1):
            logger.info(f"第{retry_index}次查询国家补贴审计订单导出记录")
            export_data = self._query_audit_export_task_pages()
            matching_tasks = self._find_matching_tasks(
                export_data,
                export_params,
                task_ids=tracked_task_ids,
            )
            if matching_tasks:
                last_matching_tasks = matching_tasks
                for matching_task in matching_tasks:
                    tracked_task_ids.update(self._extract_task_identifiers(matching_task))
            task = self._find_matching_success_task(
                export_data,
                export_params,
                task_ids=tracked_task_ids,
            )
            if task:
                download_url = self._extract_download_url(task)
                logger.info("国家补贴审计订单导出完成，开始下载解析 Excel")
                return self._download_export_records(
                    download_url,
                    expected_year=export_params.get("year"),
                )

            if retry_index in {1, max_retries} or retry_index % 3 == 0:
                if matching_tasks:
                    logger.warning(
                        "国家补贴审计订单导出已匹配到任务但未成功: "
                        f"{self._summarize_task_list(matching_tasks, export_params)}"
                    )
                else:
                    logger.warning(
                        "国家补贴审计订单导出暂未匹配到成功任务: "
                        f"{self._summarize_task_candidates(export_data, export_params)}"
                    )

            if retry_index < max_retries:
                sleep(sleep_seconds)

        if last_matching_tasks:
            logger.error(
                "国家补贴审计订单导出超时，最后一次匹配到的任务状态: "
                f"{self._summarize_task_list(last_matching_tasks, export_params)}"
            )
        else:
            logger.error("国家补贴审计订单导出超时，未获取到成功任务")
        return []

    def download_latest_success_audit_order_export(self, params=None):
        """下载最近一条成功的审计订单导出记录。"""
        export_data = self.query_audit_export_tasks(page=1, page_size=20)
        task = self._find_matching_success_task(export_data, params or {})
        if not task:
            logger.warning("没有找到可下载的国家补贴审计订单成功导出记录")
            return []
        download_url = self._extract_download_url(task)
        return self._download_export_records(download_url, expected_year=(params or {}).get("year"))

    def _query_audit_export_task_pages(self, max_pages=None):
        max_pages = max_pages or self.TASK_QUERY_MAX_PAGES
        combined_page_data = []
        first_data = {}
        for page in range(1, max_pages + 1):
            export_data = self.query_audit_export_tasks(
                page=page,
                page_size=self.TASK_QUERY_PAGE_SIZE,
            )
            if page == 1:
                first_data = export_data

            page_data = (export_data.get("data") or {}).get("pageData") or []
            combined_page_data.extend(page_data)
            if len(page_data) < self.TASK_QUERY_PAGE_SIZE:
                break

        combined_data = dict(first_data)
        raw_data = dict((first_data.get("data") or {}))
        raw_data["pageData"] = combined_page_data
        raw_data["queriedPages"] = min(max_pages, (len(combined_page_data) + self.TASK_QUERY_PAGE_SIZE - 1) // self.TASK_QUERY_PAGE_SIZE)
        combined_data["data"] = raw_data
        return combined_data

    def _with_total_page_size(self, params):
        export_params = dict(params)
        query_params = dict(export_params)
        query_params["pageIndex"] = 1
        query_params["pageSize"] = 1
        response_data = self.query_audit_order_list(query_params)
        total = (response_data.get("data") or {}).get("total")
        if total:
            export_params["pageSize"] = int(total)
        export_params.setdefault("pageIndex", 1)
        return export_params

    def _find_matching_success_task(self, export_data, params, task_ids=None):
        for task in self._find_matching_tasks(export_data, params, task_ids=task_ids):
            if str(task.get("status")) != self.TASK_STATUS_SUCCESS:
                continue
            if task.get("downloadUrlExpire") == "true":
                continue
            if self._extract_download_url(task):
                return task
        return None

    def _find_matching_tasks(self, export_data, params, task_ids=None):
        page_data = (export_data.get("data") or {}).get("pageData") or []
        matching_tasks = []
        for task in page_data:
            if str(task.get("type")) != self.EXPORT_TASK_TYPE:
                continue
            if task_ids and self._task_matches_identifiers(task, task_ids):
                matching_tasks.append(task)
                continue
            if params and self._task_matches_params(task, params):
                matching_tasks.append(task)
        return matching_tasks

    @staticmethod
    def _task_matches_params(task, params):
        return not TaoXiGongZuoTaiGovSubsidyAuditApi._task_param_mismatches(
            task,
            params,
        )

    @staticmethod
    def _task_param_mismatches(task, params):
        request_text = task.get("request") or ""
        try:
            request_data = json.loads(request_text)
        except (TypeError, ValueError):
            return ["request_json"]

        raw_params = request_data.get("govSubsidyAuditOrderRequest") or {}
        if isinstance(raw_params, str):
            try:
                raw_params = json.loads(raw_params)
            except (TypeError, ValueError):
                return ["request_params_json"]

        compare_keys = [
            "auditAreaId",
            "auditCategory",
            "auditTemplateId",
            "city",
            "exception",
            "pro",
            "sellerId",
            "source",
            "year",
            "ztSeller",
        ]
        return [
            key
            for key in compare_keys
            if key in params and str(raw_params.get(key)) != str(params.get(key))
        ]

    @staticmethod
    def _task_matches_identifiers(task, task_ids):
        candidate_values = {
            str(value)
            for key, value in task.items()
            if key in {"id", "taskId", "jobId", "syncJobId", "bizId"} and value is not None
        }
        return bool(candidate_values & {str(task_id) for task_id in task_ids})

    @classmethod
    def _extract_task_identifiers(cls, data):
        task_ids = set()
        cls._collect_task_identifiers(data, task_ids)
        return task_ids

    @classmethod
    def _collect_task_identifiers(cls, data, task_ids):
        if isinstance(data, dict):
            for key, value in data.items():
                if key in {"id", "taskId", "jobId", "syncJobId", "bizId"} and value is not None:
                    task_ids.add(str(value))
                elif isinstance(value, (dict, list)):
                    cls._collect_task_identifiers(value, task_ids)
        elif isinstance(data, list):
            for item in data:
                cls._collect_task_identifiers(item, task_ids)

    @staticmethod
    def _summarize_create_response(create_data):
        if not isinstance(create_data, dict):
            return str(type(create_data).__name__)
        safe_keys = (
            "success",
            "code",
            "message",
            "msg",
            "errorCode",
            "errorMsg",
            "canRetry",
            "id",
            "taskId",
            "jobId",
            "syncJobId",
            "bizId",
        )
        summary = {key: create_data.get(key) for key in safe_keys if key in create_data}
        if "data" in create_data:
            summary["data"] = TaoXiGongZuoTaiGovSubsidyAuditApi._safe_json_summary(
                create_data.get("data")
            )
        summary["keys"] = sorted(create_data.keys())
        return json.dumps(summary, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _safe_json_summary(value, depth=0):
        if depth >= 3:
            return type(value).__name__
        if isinstance(value, dict):
            summary = {}
            for key, item_value in list(value.items())[:20]:
                lowered_key = str(key).lower()
                if any(word in lowered_key for word in ("cookie", "token", "sign", "password", "url", "request")):
                    summary[key] = "<hidden>"
                    continue
                summary[key] = TaoXiGongZuoTaiGovSubsidyAuditApi._safe_json_summary(
                    item_value,
                    depth + 1,
                )
            summary["keys"] = sorted(value.keys())
            return summary
        if isinstance(value, list):
            return [
                TaoXiGongZuoTaiGovSubsidyAuditApi._safe_json_summary(item, depth + 1)
                for item in value[:5]
            ]
        if isinstance(value, str):
            return value[:200] + "..." if len(value) > 200 else value
        return value

    @classmethod
    def _summarize_task_candidates(cls, export_data, params, limit=5):
        page_data = (export_data.get("data") or {}).get("pageData") or []
        summaries = [
            cls._summarize_task(task, params, index=index)
            for index, task in enumerate(page_data[:limit], 1)
        ]
        return json.dumps(summaries, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def _summarize_task_list(cls, tasks, params, limit=5):
        summaries = [
            cls._summarize_task(task, params, index=index)
            for index, task in enumerate(tasks[:limit], 1)
        ]
        return json.dumps(summaries, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def _summarize_task(cls, task, params, index=None):
        summary = {
            "type": task.get("type"),
            "status": task.get("status"),
            "expired": task.get("downloadUrlExpire"),
            "has_download_url": bool(cls._extract_download_url(task)),
            "mismatch": cls._task_param_mismatches(task, params) if params else [],
            "request": cls._summarize_task_request(task),
            "result": cls._summarize_task_result(task),
        }
        if index is not None:
            summary["index"] = index
        for key in ("id", "taskId", "jobId", "syncJobId", "bizId"):
            if task.get(key) is not None:
                summary[key] = task.get(key)
        return summary

    @staticmethod
    def _summarize_task_request(task):
        request_text = task.get("request") or ""
        try:
            request_data = json.loads(request_text)
        except (TypeError, ValueError):
            return {"parse_error": True}

        raw_params = request_data.get("govSubsidyAuditOrderRequest") or {}
        if isinstance(raw_params, str):
            try:
                raw_params = json.loads(raw_params)
            except (TypeError, ValueError):
                return {"parse_error": True}
        if not isinstance(raw_params, dict):
            return {"parse_error": True}

        safe_keys = [
            "auditAreaId",
            "auditCategory",
            "auditTemplateId",
            "city",
            "exception",
            "pro",
            "sellerId",
            "source",
            "year",
            "ztSeller",
        ]
        return {key: raw_params.get(key) for key in safe_keys if key in raw_params}

    @staticmethod
    def _extract_download_url(task):
        result_text = task.get("result") or ""
        try:
            result_data = json.loads(result_text)
        except (TypeError, ValueError):
            return ""
        return result_data.get("downloadUrl") or ""

    @staticmethod
    def _summarize_task_result(task):
        result_text = task.get("result") or ""
        if not result_text:
            return {}
        try:
            result_data = json.loads(result_text)
        except (TypeError, ValueError):
            return {"parse_error": True}
        if not isinstance(result_data, dict):
            return {"type": type(result_data).__name__}

        safe_keys = [
            "success",
            "code",
            "message",
            "msg",
            "errorCode",
            "errorMsg",
        ]
        summary = {key: result_data.get(key) for key in safe_keys if key in result_data}
        summary["keys"] = sorted(result_data.keys())
        summary["has_download_url"] = bool(result_data.get("downloadUrl"))
        return summary

    def _download_export_records(self, download_url, expected_year=None):
        """下载国家补贴审计工作台订单导出 Excel 并转为字典列表。"""
        try:
            records = Downloader(
                api=download_url,
                cookie=self.cookie,
                timeout=60,
                context="国家补贴审计工作台订单导出下载",
            ).download_excel(engine="openpyxl", validate_excel=True, dtype=str)
            records = records if isinstance(records, list) else []
            self._validate_export_records(records, expected_year)
            return records
        except Exception as exc:
            return handle_request_error(exc, context="国家补贴审计工作台订单导出下载") or []

    @staticmethod
    def _validate_export_records(records, expected_year=None):
        if not records or not expected_year:
            return

        year_values = {
            str(record.get("审计年份")).strip()
            for record in records
            if record.get("审计年份") not in (None, "")
        }
        if year_values and year_values != {str(expected_year)}:
            raise ValueError(
                f"国家补贴审计订单导出年份不匹配: expected_year={expected_year}, "
                f"export_years={sorted(year_values)}, records={len(records)}；"
                "已停止写库，请检查平台筛选条件或 auditAreaId/year 是否匹配"
            )
