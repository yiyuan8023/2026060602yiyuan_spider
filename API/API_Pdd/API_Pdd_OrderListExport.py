# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 23:40:00
- 最近修改：2026-06-12 23:40:00
- 文件用途：封装拼多多订单列表页批量导出任务的配置读取、任务创建、列表轮询和 CSV 下载能力。
- 业务范围：适用于 https://mms.pinduoduo.com/orders/list 的订单批量导出；近三个月订单与历史订单共用同一任务列表和下载链路。
- 依赖入口：继承 API.API_Pdd.API_Pdd_Base.PddBaseApi，导出文件下载统一走 downloader.core.Downloader。
- 验收方式：修改后执行 py_compile 和导入探针；真实请求时先单店铺、单日期验证导出配置、任务创建、任务回查和 CSV 解析。
- 注意事项：日志不得输出完整 Cookie、签名下载 URL 或导出文件敏感内容；任务创建存在 5 分钟频控，命中后优先复用最近任务。
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

from downloader.core import Downloader
from extra.logger_ import logger

from API.API_Pdd.API_Pdd_Base import PddBaseApi


class PddOrderListExportApi(PddBaseApi):
    """拼多多订单列表页批量导出 API。"""

    BASE_URL = "https://mms.pinduoduo.com"
    ORDER_LIST_REFERER = "https://mms.pinduoduo.com/orders/list?msfrom=mms_sidenav"
    EXPORT_PREPARE_API = f"{BASE_URL}/mars/shop/orders/export/task/prepare"
    EXPORT_RECENT_ADD_API = f"{BASE_URL}/mars/shop/recentOrders/export/task/add"
    EXPORT_HISTORY_ADD_API = f"{BASE_URL}/mars/shop/historyOrders/export/task/add"
    EXPORT_TASK_LIST_API = f"{BASE_URL}/mars/shop/orders/export/task/list"
    EXPORT_TASK_URL_API = f"{BASE_URL}/mars/shop/orders/export/task/getUrl"

    CUSTOM_TEMPLATE_NAME = "自定义报表"
    STATUS_RUNNING = 0
    STATUS_SUCCESS = 1
    STATUS_FAILED_HINTS = {"失败", "异常", "驳回"}
    SUBMIT_COOLDOWN_HINT = "两次提交时间不得小于5分钟"

    RECENT_EXPORT_KEYS = {
        "orderSn",
        "trackingNumber",
        "goodsId",
        "goodsName",
        "receiveName",
        "virtualMobile",
        "extNumber",
        "orderType",
        "afterSaleType",
        "groupStartTime",
        "groupEndTime",
        "lastStartTime",
        "lastEndTime",
        "pageNumber",
        "pageSize",
        "userId",
        "templateName",
        "titles",
        "rememberTemplate",
        "reasonDesc",
        "reasonType",
        "hideRegionBlackDelayShipping",
        "sameCityDistributionOption",
        "promiseDeliveryStartTime",
        "promiseDeliveryEndTime",
        "promiseDeliveryOption",
        "cityTransportOption",
        "startShippingTime",
        "endShippingTime",
        "delayShippingStatus",
    }
    HISTORY_EXPORT_KEYS = {
        "orderSn",
        "goodsId",
        "receiveName",
        "groupStartTime",
        "orderType",
        "afterSaleType",
        "groupEndTime",
        "pageNumber",
        "pageSize",
        "userId",
        "templateName",
        "titles",
        "rememberTemplate",
        "reasonDesc",
        "reasonType",
    }

    def build_order_headers(self, *, need_anti_content: bool = True) -> Dict[str, str]:
        """补充订单列表页导出接口常用请求头。"""
        headers = self.build_headers(need_anti_content=need_anti_content)
        headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Origin": self.BASE_URL,
                "Referer": self.ORDER_LIST_REFERER,
            }
        )
        return headers

    def prepare_export_config(self) -> Dict[str, Any]:
        """读取导出弹窗配置和字段列表。"""
        response_json = self.get_json(
            self.EXPORT_PREPARE_API,
            headers=self.build_order_headers(),
            context="拼多多订单导出配置",
        )
        return self._extract_result(response_json)

    def normalize_create_payload(
        self,
        payload: Dict[str, Any],
        *,
        export_mode: str,
        prepare_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """按前端白名单规则整理创建任务入参。"""
        source_payload = dict(payload or {})
        whitelist = (
            self.RECENT_EXPORT_KEYS if export_mode == "recent" else self.HISTORY_EXPORT_KEYS
        )
        titles = self._normalize_title_values(source_payload.get("titles"))
        template_name = str(source_payload.get("templateName") or "").strip()

        if not template_name and not titles:
            prepare_config = prepare_config or self.prepare_export_config()
            titles = self.flatten_all_title_ids(prepare_config.get("allTitles"))
            template_name = self.CUSTOM_TEMPLATE_NAME if titles else str(
                prepare_config.get("defaultTemplate") or ""
            ).strip()
            source_payload.setdefault("rememberTemplate", False)

        if titles:
            source_payload["titles"] = titles
            source_payload.setdefault("templateName", self.CUSTOM_TEMPLATE_NAME)
        elif template_name == self.CUSTOM_TEMPLATE_NAME:
            raise ValueError("自定义报表缺少 titles，无法提交导出任务。")

        normalized: Dict[str, Any] = {}
        for key in whitelist:
            if key not in source_payload:
                continue
            value = source_payload.get(key)
            if value in ("", None):
                continue
            if key == "sameCityDistributionOption" and value == 0:
                continue
            normalized[key] = value

        if normalized.get("templateName") == self.CUSTOM_TEMPLATE_NAME and not normalized.get("titles"):
            raise ValueError("自定义报表必须提供字段 ID 列表。")
        return normalized

    def create_export_task(
        self,
        payload: Dict[str, Any],
        *,
        export_mode: str,
        prepare_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """创建导出任务。"""
        normalized_payload = self.normalize_create_payload(
            payload,
            export_mode=export_mode,
            prepare_config=prepare_config,
        )
        api = (
            self.EXPORT_RECENT_ADD_API
            if export_mode == "recent"
            else self.EXPORT_HISTORY_ADD_API
        )
        logger.info(
            f"{self.shop_name or '拼多多店铺'} 创建订单导出任务，mode={export_mode}，"
            f"payload_keys={sorted(normalized_payload.keys())}"
        )
        return (
            self.post_json(
                api,
                normalized_payload,
                headers=self.build_order_headers(),
                context=f"拼多多订单导出任务创建({export_mode})",
            )
            or {}
        )

    def list_export_tasks(
        self,
        *,
        page_number: int = 1,
        page_size: int = 40,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """查询已生成报表列表。"""
        payload = {"pageNumber": page_number, "pageSize": page_size}
        if extra_payload:
            payload.update(extra_payload)
        return (
            self.post_json(
                self.EXPORT_TASK_LIST_API,
                payload,
                headers=self.build_order_headers(),
                context="拼多多订单导出任务列表",
            )
            or {}
        )

    def get_export_download_url(self, job_id: Any) -> str:
        """根据任务 ID 获取导出文件下载链接。"""
        response_json = self.post_json(
            self.EXPORT_TASK_URL_API,
            {"jobId": job_id},
            headers=self.build_order_headers(),
            context=f"拼多多订单导出下载链接 jobId={job_id}",
        )
        download_url = self._extract_download_url(response_json)
        if not download_url:
            raise RuntimeError(f"任务 {job_id} 未返回可用下载链接")
        return download_url

    def wait_task_ready(
        self,
        payload: Dict[str, Any],
        *,
        export_mode: str,
        previous_task_ids: Optional[Set[Any]] = None,
        timeout_seconds: int = 600,
        poll_seconds: int = 10,
        list_page_size: int = 40,
    ) -> Dict[str, Any]:
        """轮询任务列表，等待任务进入完成状态。"""
        deadline = time.time() + timeout_seconds
        last_seen_status = None
        previous_task_ids = set(previous_task_ids or set())

        while time.time() <= deadline:
            response_json = self.list_export_tasks(page_number=1, page_size=list_page_size)
            tasks = self.extract_task_list(response_json)
            task = self.find_best_matching_task(
                tasks,
                payload=payload,
                export_mode=export_mode,
                previous_task_ids=previous_task_ids,
            )

            if task:
                status = task.get("status")
                status_str = str(task.get("statusStr") or "")
                if status != last_seen_status:
                    logger.info(
                        f"{self.shop_name or '拼多多店铺'} 导出任务状态更新，"
                        f"job_id={task.get('id')}，status={status}，status_str={status_str}，"
                        f"progress={task.get('progressRate')}"
                    )
                    last_seen_status = status

                if status == self.STATUS_SUCCESS:
                    return task
                if status not in (None, self.STATUS_RUNNING):
                    raise RuntimeError(
                        f"导出任务失败，job_id={task.get('id')}，status={status}，status_str={status_str or '--'}"
                    )
                if any(hint in status_str for hint in self.STATUS_FAILED_HINTS):
                    raise RuntimeError(
                        f"导出任务异常，job_id={task.get('id')}，status={status}，status_str={status_str}"
                    )
            else:
                logger.info(f"{self.shop_name or '拼多多店铺'} 任务列表中暂未匹配到目标导出任务，继续轮询")

            time.sleep(max(poll_seconds, 1))

        raise TimeoutError(f"等待拼多多导出任务完成超时，已等待 {timeout_seconds} 秒")

    def download_export_records(self, download_url: str) -> List[Dict[str, Any]]:
        """下载并解析导出 CSV。"""
        return Downloader(
            api=download_url,
            timeout=60,
            context="拼多多订单导出 CSV 下载",
        ).download_csv()

    def export_order_records(
        self,
        payload: Dict[str, Any],
        *,
        export_mode: str = "recent",
        timeout_seconds: int = 600,
        poll_seconds: int = 10,
    ) -> List[Dict[str, Any]]:
        """创建导出任务、等待完成并返回解析后的记录。"""
        prepare_config = self.prepare_export_config()
        normalized_payload = self.normalize_create_payload(
            payload,
            export_mode=export_mode,
            prepare_config=prepare_config,
        )
        previous_task_ids = self.collect_task_ids(
            self.list_export_tasks(page_number=1, page_size=40)
        )
        response_json = self.create_export_task(
            normalized_payload,
            export_mode=export_mode,
            prepare_config=prepare_config,
        )
        created_with_cooldown = self._is_submit_cooldown_response(response_json)
        if created_with_cooldown:
            logger.warning(
                f"{self.shop_name or '拼多多店铺'} 命中 5 分钟导出频控，尝试复用最近同条件任务"
            )

        task = self.wait_task_ready(
            normalized_payload,
            export_mode=export_mode,
            previous_task_ids=set() if created_with_cooldown else previous_task_ids,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
        )
        job_id = task.get("id")
        if not job_id:
            raise RuntimeError("导出任务已完成，但未拿到任务 ID")
        download_url = task.get("excelUrl") or self.get_export_download_url(job_id)
        return self.download_export_records(download_url)

    @classmethod
    def flatten_all_title_ids(cls, all_titles: Any) -> List[int]:
        """从 allTitles 结构中拍平字段 ID。"""
        title_ids: List[int] = []
        for group in all_titles or []:
            if not isinstance(group, dict):
                continue
            for child in group.get("children") or []:
                if not isinstance(child, dict):
                    continue
                title_id = child.get("id")
                if isinstance(title_id, int):
                    title_ids.append(title_id)
        return title_ids

    @classmethod
    def extract_task_list(cls, response_json: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """兼容不同返回结构，统一抽取任务列表。"""
        result = cls._extract_result(response_json)
        for key in ("pageItems", "list", "rows", "records", "items"):
            value = result.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        return []

    @classmethod
    def collect_task_ids(cls, response_json: Optional[Dict[str, Any]]) -> Set[Any]:
        """收集当前任务列表里的任务 ID，用于识别新任务。"""
        task_ids: Set[Any] = set()
        for task in cls.extract_task_list(response_json):
            task_id = task.get("id")
            if task_id not in ("", None):
                task_ids.add(task_id)
        return task_ids

    def find_best_matching_task(
        self,
        tasks: Iterable[Dict[str, Any]],
        *,
        payload: Dict[str, Any],
        export_mode: str,
        previous_task_ids: Set[Any],
    ) -> Optional[Dict[str, Any]]:
        """按日期和筛选条件在任务列表中反查目标任务。"""
        matched: List[Dict[str, Any]] = []
        for task in tasks:
            task_id = task.get("id")
            if previous_task_ids and task_id in previous_task_ids:
                continue
            if not self._task_matches_payload(task, payload, export_mode=export_mode):
                continue
            matched.append(task)

        if not matched:
            return None

        matched.sort(
            key=lambda item: (
                int(item.get("createdTime") or 0),
                int(item.get("id") or 0),
            ),
            reverse=True,
        )
        return matched[0]

    @staticmethod
    def resolve_export_mode(start_timestamp: int, end_timestamp: int) -> str:
        """根据日期范围自动判断 recent 或 history。"""
        recent_threshold = datetime.now() - timedelta(days=92)
        if datetime.fromtimestamp(end_timestamp) >= recent_threshold:
            return "recent"
        return "history"

    @classmethod
    def _normalize_title_values(cls, titles: Any) -> List[int]:
        if titles in (None, ""):
            return []
        if isinstance(titles, (list, tuple, set)):
            result: List[int] = []
            for item in titles:
                if isinstance(item, dict):
                    item = item.get("id")
                if item in ("", None):
                    continue
                result.append(int(item))
            return result
        if isinstance(titles, str):
            return [int(part.strip()) for part in titles.replace("，", ",").split(",") if part.strip()]
        raise TypeError(f"不支持的 titles 类型: {type(titles)}")

    @classmethod
    def _extract_result(cls, response_json: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(response_json, dict):
            return {}
        for key in ("result", "data"):
            value = response_json.get(key)
            if isinstance(value, dict):
                return value
            if isinstance(value, list):
                return {"list": value}
        return response_json

    @classmethod
    def _extract_download_url(cls, response_json: Optional[Dict[str, Any]]) -> str:
        if isinstance(response_json, dict):
            result = response_json.get("result")
            if isinstance(result, str) and result.strip():
                return result.strip()
            for key in ("excelUrl", "downloadUrl", "url", "fileUrl"):
                value = response_json.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            if isinstance(result, dict):
                for key in ("excelUrl", "downloadUrl", "url", "fileUrl"):
                    value = result.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
        return ""

    @classmethod
    def _is_submit_cooldown_response(cls, response_json: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(response_json, dict):
            return False
        error_msg = str(response_json.get("errorMsg") or response_json.get("error_msg") or "")
        return cls.SUBMIT_COOLDOWN_HINT in error_msg

    def _task_matches_payload(
        self,
        task: Dict[str, Any],
        payload: Dict[str, Any],
        *,
        export_mode: str,
    ) -> bool:
        comparable_pairs = [
            ("goodsId", "goodsId"),
            ("orderSn", "orderSn"),
            ("receiveName", "receiveName"),
            ("trackingNumber", "trackingNumber"),
            ("virtualMobile", "mobile"),
            ("orderType", "orderType"),
            ("afterSaleType", "afterSaleType"),
            ("delayShippingStatus", "delayShippingStatus"),
        ]
        for payload_key, task_key in comparable_pairs:
            payload_value = payload.get(payload_key)
            if payload_value in ("", None):
                continue
            if str(task.get(task_key) or "") != str(payload_value):
                return False

        if export_mode == "history":
            return self._match_time_pair(
                task,
                payload,
                task_start_key="orderStartTime",
                task_end_key="orderEndTime",
            )
        return self._match_time_pair(
            task,
            payload,
            task_start_key="groupStartTime",
            task_end_key="groupEndTime",
        )

    @staticmethod
    def _match_time_pair(
        task: Dict[str, Any],
        payload: Dict[str, Any],
        *,
        task_start_key: str,
        task_end_key: str,
    ) -> bool:
        payload_start = payload.get("groupStartTime")
        payload_end = payload.get("groupEndTime")
        if payload_start not in ("", None) and str(task.get(task_start_key) or "") != str(payload_start):
            return False
        if payload_end not in ("", None) and str(task.get(task_end_key) or "") != str(payload_end):
            return False
        return True
