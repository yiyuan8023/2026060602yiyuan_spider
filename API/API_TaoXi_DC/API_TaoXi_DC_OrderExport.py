# -*- coding: utf-8 -*-
"""DChain fulfillment order export API."""

from datetime import datetime, timedelta
from time import sleep

from API.API_TaoXi_DC.API_TaoXi_DC_Base import TaoXiDCBaseApi
from downloader.core import Downloader
from extra.extra_error import handle_request_error
from extra.logger_ import logger


class TaoXiDCOrderExportApi(TaoXiDCBaseApi):
    """Create DChain order export tasks, poll GEI task center, and download Excel."""

    ORDER_LIST_API = "/portal/v1/order/orders"
    USER_INFO_API = "/portal/v1/user/info"
    GEI_HOST = "https://tools.cbbs.tmall.com"
    EXPORT_TASK_CODE = "ALL_EXPORT_SCP_ORDER_BY_SEGMENT"
    GEI_EXPORT_API = f"{GEI_HOST}/gei/export/task/{EXPORT_TASK_CODE}"
    GEI_TASK_LIST_API = f"{GEI_HOST}/gei/task/list"
    GEI_EXPORT_FILE_API = f"{GEI_HOST}/gei/export/task/{{task_id}}"
    TASK_RECORD_PAGE_SIZE = 50
    EXPORT_SUCCESS_STATUS = "FINISHED"
    EXPORT_FAILED_STATUS = {"ERROR", "CANCEL", "CANCELED", "FAIL", "FAILED"}
    EXPORT_NO_DATA_MARKERS = (
        "没有数据需要导出",
        "请检查导出条件",
    )
    EXPORT_CONTEXT_EXPIRED_MARKERS = (
        "用户信息已过期",
        "重新点击一次查询",
        "resetQuery",
    )

    def query_order_list(self, payload, page=1, page_size=20):
        params = dict(payload)
        params["pageIndex"] = page
        params["pageSize"] = page_size
        return self.request_json(
            self.ORDER_LIST_API,
            params=params,
            context="DChain订单列表查询",
            log_success=page == 1,
        )

    def query_user_info(self):
        response_json = self.request_json(
            self.USER_INFO_API,
            context="DChain用户信息查询",
            log_success=False,
        )
        return response_json.get("data") or {}

    def refresh_order_query_context(self, payload):
        """Refresh page query context before retrying GEI export."""
        self.query_order_list(payload, page=1, page_size=20)
        logger.info("DChain订单查询上下文已刷新，准备重新创建导出任务")

    def create_all_order_export(self, payload):
        export_payload = self.prepare_export_payload(payload)
        token = self.get_scm_token()
        response_json = self.request_json(
            self.GEI_EXPORT_API,
            method="post",
            data={
                "_scm_token_": token,
                "query": self.compact_json(export_payload),
            },
            headers={
                "source": "ascp",
                "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
                "origin": "https://web.scm.tmall.com",
            },
            context="DChain全部订单导出创建",
            timeout=60,
        )
        task_id = str((response_json.get("data") or {}).get("taskId") or "")
        if not task_id:
            raise RuntimeError(f"DChain导出创建未返回taskId: {self._safe_export_response(response_json)}")
        logger.info(f"DChain全部订单导出任务已创建，taskId={task_id}")
        return task_id

    def prepare_export_payload(self, payload):
        export_payload = dict(payload)
        skip_warehouse_filter = export_payload.pop("_skipWarehouseFilter", False)
        export_payload.setdefault("bizStatus", 0)
        export_payload.setdefault("isHistory", False)
        export_payload.setdefault("orderCodeType", 2)
        if not skip_warehouse_filter:
            export_payload.setdefault("warehouseDeliveryMode", 2)
            export_payload.setdefault("isMerchant", True)
        export_payload.setdefault("queryCode", "")

        if "userDTO" not in export_payload:
            user_info = self.query_user_info()
            if user_info:
                export_payload["userDTO"] = user_info
        return export_payload

    def query_task_records(self, page=1, page_size=TASK_RECORD_PAGE_SIZE, **filters):
        params = {
            "pageIndex": page,
            "pageSize": page_size,
            "taskType": "EXPORT",
            "taskSubType": "",
        }
        params.update({key: value for key, value in filters.items() if value not in (None, "", [])})
        return self.request_json(
            self.GEI_TASK_LIST_API,
            params=params,
            headers={"source": "ascp"},
            context="DChain文件中心任务列表",
            log_success=page == 1,
        )

    def export_order_records(
        self,
        payload,
        max_retries=10,
        sleep_seconds=60,
        max_export_attempts=2,
    ):
        last_error = None
        for export_attempt in range(1, max_export_attempts + 1):
            if export_attempt > 1:
                self.refresh_order_query_context(payload)

            task_id = self.create_all_order_export(payload)
            for retry_index in range(1, max_retries + 1):
                logger.info(f"第{retry_index}次查询DChain订单导出任务，taskId={task_id}")
                task = self.find_task_by_id(task_id)
                if task and self._is_failed_task(task):
                    error_message = task.get("errorMessage") or task.get("msg") or "unknown error"
                    if self._is_no_data_task(task):
                        logger.warning(f"DChain订单导出无数据，taskId={task_id}，message={error_message}")
                        return []
                    if export_attempt < max_export_attempts and self._is_context_expired_task(task):
                        last_error = RuntimeError(
                            f"DChain订单导出失败，taskId={task_id}，status={task.get('taskStatus')}，message={error_message}"
                        )
                        logger.warning(
                            f"DChain订单导出上下文过期，准备第{export_attempt + 1}次尝试，"
                            f"taskId={task_id}，message={error_message}"
                        )
                        break
                    raise RuntimeError(
                        f"DChain订单导出失败，taskId={task_id}，status={task.get('taskStatus')}，message={error_message}"
                    )
                if task and self._is_success_task(task):
                    download_url = self._extract_download_url(task)
                    logger.info(f"DChain订单导出完成，taskId={task_id}，开始下载Excel")
                    return self.download_export_records(download_url)

                if retry_index < max_retries:
                    sleep(sleep_seconds)
            else:
                raise RuntimeError(f"DChain订单导出超时，taskId={task_id}")

        raise last_error or RuntimeError("DChain订单导出失败，已达到最大重试次数")

    def download_latest_success_order_export(self, task_type=None):
        task = self.find_latest_success_task(task_type=task_type)
        if not task:
            logger.warning("未找到DChain最近成功订单导出任务")
            return []
        download_url = self._extract_download_url(task)
        return self.download_export_records(download_url)

    def find_task_by_id(self, task_id, max_pages=5):
        for page in range(1, max_pages + 1):
            response_json = self.query_task_records(page=page, taskId=task_id)
            for task in self._extract_task_list(response_json):
                if str(task.get("taskId")) == str(task_id):
                    return task
            if len(self._extract_task_list(response_json)) < self.TASK_RECORD_PAGE_SIZE:
                break
        return None

    def find_latest_success_task(self, task_type=None, max_pages=5):
        task_code = task_type or self.EXPORT_TASK_CODE
        for page in range(1, max_pages + 1):
            response_json = self.query_task_records(
                page=page,
                gmtCreateStart=self._recent_task_start_time(days=30),
            )
            tasks = self._extract_task_list(response_json)
            for task in tasks:
                if str(task.get("taskStatus")) != self.EXPORT_SUCCESS_STATUS:
                    continue
                if task_code and str(task.get("taskCode")) != task_code:
                    continue
                return task
            if len(tasks) < self.TASK_RECORD_PAGE_SIZE:
                break
        return None

    def download_export_records(self, download_url):
        try:
            records = Downloader(
                api=download_url,
                cookie=self.cookie,
                headers={
                    "source": "ascp",
                    "referer": self.page_referer,
                },
                timeout=60,
                context="DChain订单导出下载",
            ).download_excel(engine="openpyxl", validate_excel=True, dtype=str)
            return records if isinstance(records, list) else []
        except Exception as exc:
            return handle_request_error(exc, context="DChain订单导出下载") or []

    @classmethod
    def build_order_export_payload(
        cls,
        start_time,
        end_time,
        warehouse="merchant",
        date_field="tradeCreateTimeRange",
        order_code_type=2,
        biz_status=0,
        is_history=False,
    ):
        payload = {
            date_field: cls._format_time_range(start_time, end_time),
            "bizStatus": biz_status,
            "isHistory": is_history,
            "orderCodeType": order_code_type,
            "queryCode": "",
        }
        if warehouse in (None, "", "all", "全部", "全部仓"):
            payload["_skipWarehouseFilter"] = True
        else:
            payload["warehouseDeliveryMode"] = cls._warehouse_delivery_mode(warehouse)
            payload["isMerchant"] = warehouse != "cn"
        return payload

    @staticmethod
    def _format_time_range(start_time, end_time):
        return f"{start_time}/{end_time}"

    @staticmethod
    def _warehouse_delivery_mode(warehouse):
        if warehouse in ("cn", "cainiao", "rookie", 0):
            return 0
        if warehouse in ("merchant", "seller", "商家仓", 2):
            return 2
        raise ValueError(f"未知DChain仓库类型: {warehouse}")

    @staticmethod
    def _extract_task_list(response_json):
        data = response_json.get("data") or []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("dataSource") or data.get("list") or []
        return []

    @classmethod
    def _extract_download_url(cls, task):
        task_id = task.get("taskId")
        if task.get("url"):
            return task.get("url")
        if task_id:
            return cls.GEI_EXPORT_FILE_API.format(task_id=task_id)
        return ""

    @classmethod
    def _is_success_task(cls, task):
        return str(task.get("taskStatus")) == cls.EXPORT_SUCCESS_STATUS

    @classmethod
    def _is_failed_task(cls, task):
        return str(task.get("taskStatus")) in cls.EXPORT_FAILED_STATUS

    @classmethod
    def _is_no_data_task(cls, task):
        error_message = str(task.get("errorMessage") or task.get("msg") or "")
        if any(marker in error_message for marker in cls.EXPORT_NO_DATA_MARKERS):
            return True
        return "GEI_P10000" in error_message and "totalCount" in error_message

    @classmethod
    def _is_context_expired_task(cls, task):
        error_message = str(task.get("errorMessage") or task.get("msg") or "")
        return any(marker in error_message for marker in cls.EXPORT_CONTEXT_EXPIRED_MARKERS)

    @staticmethod
    def _recent_task_start_time(days=30):
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _safe_export_response(response_json):
        data = response_json.get("data")
        if isinstance(data, dict):
            return {
                "success": response_json.get("success"),
                "data_keys": sorted(data.keys()),
                "message": response_json.get("message") or response_json.get("errorMessage"),
            }
        return {
            "success": response_json.get("success"),
            "data_type": type(data).__name__,
            "message": response_json.get("message") or response_json.get("errorMessage"),
        }
