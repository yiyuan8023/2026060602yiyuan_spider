# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:24:52
- 最近修改：2026-06-12 09:17:59
- 文件用途：封装淘系商家工作台交易已卖出宝贝报表接口，负责报表导出申请、下载链接解析和 Excel 解析。
- 业务范围：适用于商家工作台交易页面的已卖出宝贝报表明细导出。
- 依赖入口：继承 API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Base.TaoXiGongZuoTaiBaseApi，使用 downloader.core.Downloader、date_utils 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、单日期验证报表生成、Excel 类型校验和异常日志。
- 注意事项：API 层不写业务表、不持有店铺列表和数据库配置；日志不得输出完整 Cookie、签名下载 URL 或敏感请求参数。
"""

import html
from time import sleep

from bs4 import BeautifulSoup
from lxml import etree

from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Base import (
    TaoXiGongZuoTaiBaseApi,
)
from date_utils import get_date, get_time_ago
from downloader.core import Downloader
from extra.extra_error import handle_request_error
from extra.logger_ import logger


class TaoXiGongZuoTaiTradeApi(TaoXiGongZuoTaiBaseApi):
    """淘系商家工作台交易 API，负责导出已卖出宝贝报表。"""

    def list_export_order(self, start_timestamp, end_timestamp):
        """创建已卖出宝贝报表导出任务，下载并解析 Excel 明细。"""
        report_date = get_date(None, "%Y-%m-%d %H:%M")
        logger.info(f"正在导出商家工作台已卖出宝贝明细，范围={start_timestamp}-{end_timestamp}")

        api = "https://trade.taobao.com/trade/itemlist/list_export_order.htm"
        params = {"_input_charset": "utf8"}
        data = {
            "useCheckcode": False,  # noqa
            "errorCheckcode": False,  # noqa
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
            "useOrderInfo": False,
            "logisticsService": "ALL",
            "isQnNew": True,
            "pageNum": "1",
            "o2oDeliveryType": "ALL",
            "rxAuditFlag": "0",
            "queryOrder": "desc",
            "holdStatus": "0",
            "rxElectronicAuditFlag": "0",
            "queryMore": True,
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
            "exportType": "2",
            "fileType": "xlsx",
            "selectFieldIds": "1,2,3,4,5,6,7,8,9,10,11,17,19,20,21,22,23,24,12,13,14,15,16,18,28,29,30,25,26,27,31,32,35,33,34,36,37,38,39,40,41,42,43,44,45",
            "newExportPlatform": True,
            "event_submit_do_apply_export": "1",
        }
        headers = {
            "referer": "https://myseller.taobao.com/home.htm/trade-platform/tp/sold",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        for retry_index in range(1, 5):
            logger.info(f"第{retry_index}次检查商家工作台报表生成状态")
            response = Downloader(
                api=api,
                method="post",
                cookie=self.cookie,
                params=params,
                data=data,
                headers=headers,
                timeout=60,
                context="商家工作台报表导出申请",
            ).download_web()

            if retry_index == 1 and "两次报表申请需要控制在 5 分钟以上" in response.text:
                logger.info("五分钟之内已有报表申请，等待3分钟后重新创建")
                sleep(60 * 3)
                report_date = get_date(None, "%Y-%m-%d %H:%M")
                response = Downloader(
                    api=api,
                    method="post",
                    cookie=self.cookie,
                    params=params,
                    data=data,
                    headers=headers,
                    timeout=60,
                    context="商家工作台报表导出重试",
                ).download_web()

            download_url = self.extract_report_download_url(response.text, report_date)
            if download_url:
                logger.info("商家工作台报表生成完成，开始下载解析 Excel")
                return self._download_export_records(download_url)

            sleep(60)

        logger.error("商家工作台已卖出宝贝报表获取失败")
        return []

    @staticmethod
    def extract_report_download_url(html_content, report_date):
        """从报表列表 HTML 中提取当前申请时间附近的下载链接。"""
        if (
            hasattr(html_content, "getroot")
            or str(type(html_content)) == "<class 'lxml.etree._Element'>"
        ):
            html_string = etree.tostring(
                html_content, encoding="unicode", method="html"
            )
        else:
            html_string = html_content or ""

        soup = BeautifulSoup(html_string, "html.parser")
        reports_list = []
        for index, li_element in enumerate(soup.select("ul.sheet-list li"), 1):
            title_element = li_element.select_one("h2.sheet-item-hd")
            caption_element = li_element.select_one("table.sheet-item caption")
            if not title_element or not caption_element:
                continue

            apply_time = title_element.text.replace("报表申请时间：", "").strip()[:-3]
            caption = caption_element.text.replace("成交时间：", "").strip()
            download_elements = li_element.select("div.sheet-status a")
            download_link = None
            title = None
            status = "正在生成中"
            if download_elements:
                title = download_elements[0].get("title")
                raw_link = download_elements[0].get("href")
                download_link = html.unescape(raw_link) if raw_link else None
                status = "已完成"

            reports_list.append(
                {
                    "index": index,
                    "apply_time": apply_time,
                    "caption": caption,
                    "status": status,
                    "title": title,
                    "download_link": download_link,
                }
            )

        logger.info(
            [
                {
                    "index": report["index"],
                    "apply_time": report["apply_time"],
                    "status": report["status"],
                    "title": report["title"],
                }
                for report in reports_list
            ]
        )

        report_date_add = get_time_ago(
            n=-1,
            unit="minutes",
            base_date=report_date,
            date_format="%Y-%m-%d %H:%M",
        )
        for report in reports_list:
            if report.get("apply_time") in {report_date, report_date_add}:
                return report.get("download_link")

        return None

    def _download_export_records(self, download_url):
        """下载商家工作台导出的 Excel，并统一转为字典列表。"""
        try:
            records = Downloader(
                api=download_url,
                cookie=self.cookie,
                timeout=60,
                context="商家工作台已卖出宝贝报表下载",
            ).download_excel(engine="openpyxl", validate_excel=True)
            return records if isinstance(records, list) else []
        except Exception as exc:
            return handle_request_error(exc, context="商家工作台已卖出宝贝报表下载") or []
