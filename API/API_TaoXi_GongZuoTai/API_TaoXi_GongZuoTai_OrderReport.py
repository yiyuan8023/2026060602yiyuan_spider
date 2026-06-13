# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 17:13:52
- 最近修改：2026-06-12 17:15:30
- 文件用途：封装淘系商家工作台交易已卖出宝贝订单报表接口，负责新版字段配置读取、报表导出申请、下载链接解析和 Excel 解析。
- 业务范围：适用于商家工作台交易页面的已卖出宝贝“订单报表”导出。
- 依赖入口：继承 API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Base.TaoXiGongZuoTaiBaseApi，使用 downloader.core.Downloader、date_utils 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、单日期验证报表生成、Excel 类型校验和异常日志。
- 注意事项：订单报表业务 API 与宝贝销售明细报表 API 分离；日志不得输出完整 Cookie、签名下载 URL 或敏感请求参数。
"""

from datetime import datetime
from time import sleep
from urllib.parse import urlencode

from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Base import (
    TaoXiGongZuoTaiBaseApi,
)
from date_utils import get_date
from downloader.core import Downloader
from extra.extra_error import handle_request_error
from extra.logger_ import logger


class TaoXiGongZuoTaiOrderReportApi(TaoXiGongZuoTaiBaseApi):
    """淘系商家工作台订单报表 API，独立于宝贝销售明细报表。"""

    ORDER_REPORT_TYPE = "1"
    EXPORT_APPLY_API = "https://trade.taobao.com/trade/itemlist/list_export_order.htm"
    EXPORT_LIST_API = "mtop.taobao.trade.order.exportlist"
    EXPORT_PREPARE_API = "mtop.com.taobao.order.sold.export"
    SOLD_REFERER = "https://myseller.taobao.com/home.htm/trade-platform/tp/sold"

    def list_export_order_report(self, start_timestamp, end_timestamp):
        """创建订单报表导出任务，下载并解析 Excel 明细。"""
        report_date = get_date(None, "%Y-%m-%d %H:%M")
        logger.info(f"正在导出商家工作台订单报表，范围={start_timestamp}-{end_timestamp}")
        select_field_ids = self.get_order_report_field_ids()
        data = self._build_export_order_payload(
            start_timestamp,
            end_timestamp,
            select_field_ids,
        )
        response = self._submit_export_order(data, context="商家工作台订单报表导出申请")

        if "两次报表申请需要控制在 5 分钟以上" in response.text:
            logger.info("五分钟之内已有报表申请，等待3分钟后重新创建")
            sleep(60 * 3)
            report_date = get_date(None, "%Y-%m-%d %H:%M")
            response = self._submit_export_order(data, context="商家工作台订单报表导出重试")

        if "两次报表申请需要控制在 5 分钟以上" in response.text:
            logger.warning("商家工作台订单报表申请过于频繁，改为查询本次申请附近的已生成报表")

        for retry_index in range(1, 7):
            logger.info(f"第{retry_index}次查询商家工作台订单报表列表")
            export_data = self.query_order_export_list(
                page=1,
                log_success=retry_index == 1,
            )
            report = self._find_order_report(export_data, report_date)
            if report and report.get("exportStatus") == "exportFail":
                logger.error(f"商家工作台订单报表生成失败: {report.get('exportErrMsg') or '无错误详情'}")
                return []
            if report and report.get("orderEncrypterStr"):
                download_url = self._build_report_download_url(report)
                logger.info("商家工作台订单报表生成完成，开始下载解析 Excel")
                return self._download_export_records(download_url)

            sleep(60)

        logger.error("商家工作台订单报表获取失败")
        return []

    def get_export_prepare_config(self):
        """读取新版导出弹窗配置，里面包含各报表类型的动态字段 ID。"""
        return self.mtop_request(
            self.EXPORT_PREPARE_API,
            {"type": "online", "operate": "prepare"},
            referer=self.SOLD_REFERER,
        )

    def get_order_report_field_ids(self):
        """按新版弹窗配置获取“订单报表”的全选字段。"""
        prepare_config = self.get_export_prepare_config()
        field_config_map = prepare_config.get("fieldConfigMap") or {}
        groups = field_config_map.get(self.ORDER_REPORT_TYPE) or []
        field_ids = []
        field_names = []
        for group in groups:
            for field in group.get("fields") or []:
                field_id = field.get("fieldId")
                if field_id:
                    field_ids.append(str(field_id))
                    field_names.append(field.get("name") or field_id)

        if not field_ids:
            raise RuntimeError("商家工作台订单报表字段配置为空")

        logger.info(f"商家工作台订单报表字段数={len(field_ids)}，字段={field_names}")
        return ",".join(field_ids)

    def query_order_export_list(self, page=1, log_success=False):
        """查询新版“查看已生成报表”列表。"""
        return self.mtop_request(
            self.EXPORT_LIST_API,
            {"page": page},
            referer=self.SOLD_REFERER,
            log_success=log_success,
        )

    def _submit_export_order(self, data, context):
        headers = {
            "referer": self.SOLD_REFERER,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        return Downloader(
            api=self.EXPORT_APPLY_API,
            method="post",
            cookie=self.cookie,
            params={"_input_charset": "utf8"},
            data=data,
            headers=headers,
            timeout=60,
            context=context,
        ).download_web()

    @staticmethod
    def _build_export_order_payload(start_timestamp, end_timestamp, select_field_ids):
        """新版页面仍提交老导出地址，但字段 ID 必须来自 prepare 动态配置。"""
        return {
            "useCheckcode": "false",  # noqa
            "errorCheckcode": "false",  # noqa
            "payDateBegin": "0",
            "rateStatus": "ALL",
            "orderStatus": "ALL",
            "pageSize": "15",
            "dateEnd": end_timestamp,
            "rxOldFlag": "0",
            "rxSendFlag": "0",
            "dateBegin": start_timestamp,
            "tradeTag": "0",
            "action": "itemlist/ExportOrderAction",
            "rxHasSendFlag": "0",
            "auctionType": "0",
            "close": "0",
            "notifySendGoodsType": "ALL",
            "sellerMemoFlag": "0",
            "useOrderInfo": "false",
            "logisticsService": "ALL",
            "isQnNew": "true",
            "pageNum": "1",
            "o2oDeliveryType": "ALL",
            "rxAuditFlag": "0",
            "queryOrder": "desc",
            "holdStatus": "0",
            "rxElectronicAuditFlag": "0",
            "queryMore": "true",
            "payDateEnd": "0",
            "rxWaitSendflag": "0",  # noqa
            "sellerMemo": "0",
            "tabCode": "latest3Months",
            "rxElectronicAllFlag": "0",
            "rxSuccessflag": "0",  # noqa
            "unionSearchTotalNum": "0",
            "refund": "ALL",
            "unionSearchPageNum": "0",
            "yushouStatus": "ALL",  # noqa
            "deliveryTimeType": "ALL",
            "payMethodType": "ALL",
            "orderType": "ALL",
            "appName": "ALL",
            "exportType": TaoXiGongZuoTaiOrderReportApi.ORDER_REPORT_TYPE,
            "fileType": "xlsx",
            "selectFieldIds": select_field_ids,
            "newExportPlatform": "true",
            "event_submit_do_apply_export": "1",
        }

    @classmethod
    def _find_order_report(cls, export_data, report_date):
        detail_list = export_data.get("detailList") or export_data.get("pageShowDataList") or []
        reports = [
            report
            for report in detail_list
            if str(report.get("exportType")) == cls.ORDER_REPORT_TYPE
        ]
        logger.info(
            [
                {
                    "exportId": report.get("exportId"),
                    "applyTime": report.get("applyTime"),
                    "exportStatus": report.get("exportStatus"),
                    "exportType": report.get("exportType"),
                }
                for report in reports[:5]
            ]
        )

        for report in reports:
            if cls._is_near_report_time(report.get("applyTime"), report_date):
                return report
        return None

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
    def _build_report_download_url(report):
        file_pointer = report.get("orderEncrypterStr")
        if not file_pointer:
            raise RuntimeError("商家工作台订单报表缺少下载指针")
        params = {
            "f_p": file_pointer,
            "apply_time": report.get("applyTime") or "",
            "start_time": report.get("startTimeStr") or "",
            "end_time": report.get("endTimeStr") or "",
            "order_status": report.get("orderStatus") or "",
            "export_id": report.get("exportId") or "",
            "isQnNew": "true",
        }
        return "https://trade.taobao.com/trade/itemlist/export_by_tfs.do?" + urlencode(params)

    def _download_export_records(self, download_url):
        """下载商家工作台导出的订单报表 Excel，并统一转为字典列表。"""
        try:
            records = Downloader(
                api=download_url,
                cookie=self.cookie,
                timeout=60,
                context="商家工作台订单报表下载",
            ).download_excel(engine="openpyxl", validate_excel=True)
            return records if isinstance(records, list) else []
        except Exception as exc:
            return handle_request_error(exc, context="商家工作台订单报表下载") or []
