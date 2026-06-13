# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 18:10:00
- 最近修改：2026-06-12 18:10:00
- 文件用途：封装淘系商家工作台交易退款管理售后单报表接口，负责字段配置读取、报表导出申请、报表列表查询和 Excel 下载解析。
- 业务范围：适用于 https://myseller.taobao.com/home.htm/trade-platform/refund-list 的“批量导出”新报表流程。
- 依赖入口：继承 TaoXiGongZuoTaiBaseApi，使用 downloader.core.Downloader、date_utils 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、单日期验证报表生成、Excel 类型校验和解析行数。
- 注意事项：不记录完整 Cookie、签名下载 URL 或敏感请求参数；导出任务受平台 5 分钟间隔限制。
"""

import json
from datetime import datetime, time
from time import sleep

from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Base import (
    TaoXiGongZuoTaiBaseApi,
)
from date_utils import get_date
from downloader.core import Downloader
from extra.extra_error import handle_request_error
from extra.logger_ import logger


class TaoXiGongZuoTaiRefundReportApi(TaoXiGongZuoTaiBaseApi):
    """淘系商家工作台退款管理售后单报表 API。"""

    REFUND_REPORT_TYPE = "1"
    EXPORT_BUTTON_ID = "SELLER_EXPORT_DISPUTE_LIST_NEW"
    EXPORT_CONFIG_API = "mtop.alibaba.refundface2.qianniu.export.config"
    EXPORT_LIST_API = "mtop.alibaba.refundface2.qianniu.export.list"
    DISPUTE_LIST_API = "mtop.alibaba.refundface2.disputeservice.qianniu.pc.disputelistv2"
    REFUND_REFERER = "https://myseller.taobao.com/home.htm/trade-platform/refund-list"

    def list_export_refund_report(self, start_timestamp, end_timestamp):
        """创建退款售后单报表导出任务，下载并解析 Excel 明细。"""
        start_timestamp = int(start_timestamp)
        end_timestamp = self._normalize_end_timestamp(int(end_timestamp))
        report_date = get_date(None, "%Y-%m-%d %H:%M")
        logger.info(
            f"正在导出商家工作台退款售后单报表，范围={start_timestamp}-{end_timestamp}"
        )

        export_type, select_field_ids = self.get_refund_report_field_ids()
        params = self._build_refund_export_params(
            start_timestamp,
            end_timestamp,
            export_type,
            select_field_ids,
        )
        response_data = self._submit_refund_export(params)
        error_message = self._extract_error_message(response_data)

        if "5" in error_message and "分钟" in error_message:
            logger.info("五分钟之内已有退款报表申请，等待3分钟后重新创建")
            sleep(60 * 3)
            report_date = get_date(None, "%Y-%m-%d %H:%M")
            response_data = self._submit_refund_export(params)
            error_message = self._extract_error_message(response_data)

        if error_message:
            logger.warning(f"商家工作台退款售后单报表申请返回提示: {error_message}")

        for retry_index in range(1, 7):
            logger.info(f"第{retry_index}次查询商家工作台退款售后单报表列表")
            export_data = self.query_refund_export_list(
                page=1,
                log_success=retry_index == 1,
            )
            report = self._find_refund_report(
                export_data,
                report_date,
                start_timestamp,
                end_timestamp,
            )
            if report and str(report.get("status")) == "3":
                logger.error(
                    f"商家工作台退款售后单报表生成失败: {report.get('exportErrMsg') or '无错误详情'}"
                )
                return []
            if report and str(report.get("status")) == "2" and report.get("filePath"):
                logger.info("商家工作台退款售后单报表生成完成，开始下载解析 Excel")
                return self._download_export_records(report["filePath"])

            sleep(60)

        logger.error("商家工作台退款售后单报表获取失败")
        return []

    def get_export_prepare_config(self):
        """读取新版退款导出弹窗配置，包含售后单字段 ID。"""
        return self.mtop_request(
            self.EXPORT_CONFIG_API,
            {"type": "online", "operate": "prepare"},
            referer=self.REFUND_REFERER,
        )

    def get_refund_report_field_ids(self):
        """按平台配置获取退款售后单全量导出字段。"""
        prepare_config = self.get_export_prepare_config()
        field_config_map = prepare_config.get("fieldConfigMap") or {}
        export_type = (
            self.REFUND_REPORT_TYPE
            if self.REFUND_REPORT_TYPE in field_config_map
            else next(iter(field_config_map), "")
        )
        groups = field_config_map.get(export_type) or []
        field_ids = []
        field_names = []
        for group in groups:
            for field in group.get("fields") or []:
                field_id = field.get("fieldId")
                if field_id:
                    field_ids.append(str(field_id))
                    field_names.append(field.get("name") or field_id)

        if not field_ids:
            raise RuntimeError("商家工作台退款售后单报表字段配置为空")

        logger.info(
            f"商家工作台退款售后单报表字段数={len(field_ids)}，字段={field_names}"
        )
        return export_type, ",".join(field_ids)

    def query_refund_export_list(self, page=1, log_success=False):
        """查询“查看已生成报表”退款报表列表。"""
        return self.mtop_request(
            self.EXPORT_LIST_API,
            {
                "type": "online",
                "operate": "getList",
                "pageNum": page,
                "pageSize": 10,
            },
            referer=self.REFUND_REFERER,
            log_success=log_success,
        )

    def _submit_refund_export(self, params):
        request_data = {
            "params": json.dumps(params, ensure_ascii=False, separators=(",", ":"))
        }
        return self.mtop_post_request(
            self.DISPUTE_LIST_API,
            request_data,
            referer=self.REFUND_REFERER,
        )

    @classmethod
    def _build_refund_export_params(
        cls,
        start_timestamp,
        end_timestamp,
        export_type,
        select_field_ids,
    ):
        return {
            "subPageGray": "0",
            "privacySwitchIsCheck": False,
            "isQnNew": True,
            "isHideNick": True,
            "quickQuerySelect": "",
            "quickQueryChange": False,
            "autoRefundToolSelect": "",
            "refundStatusSelect": json.dumps(["-1"], separators=(",", ":")),
            "bizTypeSelect": "",
            "csStatusSelect": "",
            "csStatusAndDutySelect": "",
            "refundReasonSelect": "",
            "gridTab": "",
            "applyDatetimePickerStartTime": str(start_timestamp),
            "applyDatetimePickerEndTime": str(end_timestamp),
            "disputeTypeSelect": "",
            "refundFeeInputStart": "",
            "refundFeeInputEnd": "",
            "insteadRefundSelect": "",
            "interceptStatusSelect": "",
            "cpSelect": "",
            "paymentMethodSelect": "",
            "returnShippingType": "",
            "unionSearch": "",
            "pageNo": 1,
            "selectFieldIds": select_field_ids,
            "newExportPlatform": "true",
            "exportType": export_type,
            "exportRemember": "true",
            "btnId": cls.EXPORT_BUTTON_ID,
        }

    @classmethod
    def _find_refund_report(
        cls,
        export_data,
        report_date,
        start_timestamp,
        end_timestamp,
    ):
        detail_list = export_data.get("pageShowDataList") or export_data.get("detailList") or []
        reports = [report for report in detail_list if report.get("exportId")]
        logger.info(
            [
                {
                    "exportId": report.get("exportId"),
                    "gmtCreate": report.get("gmtCreate"),
                    "status": report.get("status"),
                    "startCreatedTime": report.get("startCreatedTime"),
                    "endCreatedTime": report.get("endCreatedTime"),
                    "exportCount": report.get("exportCount"),
                }
                for report in reports[:5]
            ]
        )

        expected_start = cls._format_timestamp(start_timestamp)
        expected_end = cls._format_timestamp(end_timestamp)
        for report in reports:
            if (
                report.get("startCreatedTime") == expected_start
                and report.get("endCreatedTime") == expected_end
                and cls._is_near_report_time(report.get("gmtCreate"), report_date)
            ):
                return report

        for report in reports:
            if cls._is_near_report_time(report.get("gmtCreate"), report_date):
                return report

        return None

    @staticmethod
    def _normalize_end_timestamp(end_timestamp):
        end_datetime = datetime.fromtimestamp(end_timestamp / 1000)
        if end_datetime.time() == time.min:
            end_datetime = datetime.combine(end_datetime.date(), time(23, 59, 59))
        return int(end_datetime.timestamp() * 1000)

    @staticmethod
    def _format_timestamp(timestamp):
        return datetime.fromtimestamp(int(timestamp) / 1000).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _is_near_report_time(apply_time, report_date):
        if not apply_time:
            return False
        try:
            apply_datetime = datetime.strptime(apply_time[:16], "%Y-%m-%d %H:%M")
            report_datetime = datetime.strptime(report_date, "%Y-%m-%d %H:%M")
        except ValueError:
            return False
        return abs((apply_datetime - report_datetime).total_seconds()) <= 5 * 60

    @staticmethod
    def _extract_error_message(response_data):
        if not isinstance(response_data, dict):
            return ""
        result_data = response_data.get("resultData")
        if isinstance(result_data, dict):
            return result_data.get("errorMsg") or result_data.get("message") or ""
        if isinstance(result_data, str):
            return result_data if "分钟" in result_data else ""
        return response_data.get("errorMsg") or response_data.get("message") or ""

    def _download_export_records(self, download_url):
        """下载商家工作台退款售后单报表 Excel，并统一转为字典列表。"""
        try:
            records = Downloader(
                api=download_url,
                cookie=self.cookie,
                timeout=60,
                context="商家工作台退款售后单报表下载",
            ).download_excel(engine="openpyxl", validate_excel=True)
            return records if isinstance(records, list) else []
        except Exception as exc:
            return handle_request_error(exc, context="商家工作台退款售后单报表下载") or []
