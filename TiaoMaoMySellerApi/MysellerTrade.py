import json
from time import sleep
from urllib.parse import urlencode

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from lxml import etree

import requests

from TiaoMaoMySellerApi.MySellerBase import MySellerBaseAPI
from extra.downloader import Downloader
from extra.extra_date import get_date, get_time_ago
from extra.extra_error import handle_request_error
from extra.extra_reqlog import req_log
from extra.logger_ import logger


class MySellerTradeAPI(MySellerBaseAPI):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def taobao_list_export_order(self, start_timestamp, end_timestamp):
        """
        创建下载任务
        tb_商家工作台_交易_已卖出宝贝_宝贝报表明细_202504
        """
        # 获取报表下载时间
        report_date = get_date(None, "%Y-%m-%d %H:%M")
        # print(report_date)
        # logger.info(f"正在导出{start_timestamp}-{end_timestamp}明细数据")

        api = "https://trade.taobao.com/trade/itemlist/list_export_order.htm"
        params = {
            "_input_charset": "utf8",
        }
        data = {"useCheckcode": False,
                "errorCheckcode": False,
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
                "rxWaitSendflag": "0",
                "sellerMemo": "0",
                "tabCode": "latest3Months",
                "rxElectronicAllFlag": "0",
                "rxSuccessflag": "0",
                "unionSearchTotalNum": "0",
                "refund": "ALL",
                "unionSearchPageNum": "0",
                "yushouStatus": "ALL",
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
            "user-agent": self.ua,
            "cookie": self.cookie
        }

        url = None

        for i in range(1, 5):
            if not url:
                logger.info(f"第{i}次查看,报表尚未生成完成，等待1分钟后重新检查...")
                res = requests.post(api, params=params, data=data, headers=headers)
                req_log(res)

                # 第一次请求，不能生成报表，需要等待
                if i == 1:
                    if "两次报表申请需要控制在 5 分钟以上" in res.text:
                        logger.info(f"五分钟之内有创建报表,等待3分钟后创新创建")
                        sleep(60 * 3)
                        report_date = get_date(None, "%Y-%m-%d %H:%M")
                        res = requests.post(api, params=params, data=data, headers=headers)

                url = self.extract_reports_from_html(res.text, report_date)
                # url = f"https://trade.taobao.com/trade/itemlist/export_by_tfs.do?f_p=oss%2Ftradeorderexport%2ForderExportData%2F24723487011.ossprivate.xlsx-8c91c21d9cb8b176fbb706e0c08c1726-items&amp;apply_time=2025-08-08+09%3A31%3A02&amp;start_time=2025-08-05+00%3A00%3A00&amp;end_time=2025-08-08+00%3A00%3A00&amp;order_status=%C8%AB%B2%BF&amp;export_id=24723487011"

                if url:
                    logger.info(url)

                    try:
                        # 这里的下载链接，必须传入cookie可以
                        data = Downloader(url, cookie=self.cookie).download_excel()
                        df = pd.read_excel(data, skiprows=0, engine='openpyxl')
                        # 所有的NaN值（缺失值）替换为None
                        df.replace({np.nan: None}, inplace=True)
                        # 将数据转换为字典列表
                        return [] if df.empty else df.to_dict('records')
                    except Exception as e:
                        return handle_request_error(e)

                else:
                    sleep(60)

        logger.error("报表获取失败")
        return None

    @staticmethod
    def extract_reports_from_html(html_content, report_date):
        """
        从HTML对象中提取报表信息
        参数:html_content: HTML内容（字符串或文件对象）
        返回: dict: 包含所有报表信息的字典
        """

        # 如果是lxml的Element对象，转换为字符串
        if hasattr(html_content, 'getroot') or str(type(html_content)) == "<class 'lxml.etree._Element'>":
            html_string = etree.tostring(html_content, encoding='unicode', method='html')
        else:
            html_string = html_content

        soup = BeautifulSoup(html_string, 'html.parser')  # 解析HTML内容
        li_elements = soup.select('ul.sheet-list li')  # 查找所有li标签

        # 提取信息到字典中
        reports_list = []

        for index, li in enumerate(li_elements, 1):
            # 报表申请时间

            apply_time = li.select_one('h2.sheet-item-hd').text.replace('报表申请时间：', '').strip()[:-3]

            # 成交时间
            caption = li.select_one('table.sheet-item caption').text.replace('成交时间：', '').strip()

            # 下载链接（提取所有类型的报表）
            download_elements = li.select('div.sheet-status a')

            # 如果有下载链接，只取第一个
            if download_elements:
                title = download_elements[0].get('title')
                download_link = download_elements[0].get('href')
                status = "已完成"
            else:
                title = None
                download_link = None
                status = "正在生成中"

            reports_list.append(
                {'index': index,
                 'apply_time': apply_time,
                 'caption': caption,
                 'status': status,
                 'title': title,
                 'download_link': download_link})

        logger.info(reports_list)

        report_date_add = get_time_ago(n=-1, unit='minutes', base_date=report_date, date_format="%Y-%m-%d %H:%M")
        for report in reports_list:
            # 前后一分钟的报表
            if report_date == report.get('apply_time')   or report.get('apply_time') ==  report_date_add:
                url = report.get('download_link')
                return url

        return None


if __name__ == '__main__':
    Obj = MySellerTradeAPI(cookie='A')
    # Obj.taobao_list_export_order(start_timestamp="2023-05-01 00:00:00", end_timestamp="2023-05-31 23:59:59")

    with open(r'C:\Users\admin\Desktop\新建 文本文档.txt', 'r', encoding='utf-8') as file:
        html_content = file.read()

    # 调用函数提取报表信息
    reports_data = Obj.extract_reports_from_html(html_content, '2025-08-06 12:26')

    # 打印结果
    print(json.dumps(reports_data, ensure_ascii=False, indent=2))
