# File: MysellerTrade
import json
from urllib.parse import urlencode

from lxml import etree

import requests

from TiaoMaoMySellerApi.MySellerBase import MySellerBaseAPI
from extra.extra_date import get_date
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
        print(report_date)

        logger.info(f"正在导出{start_timestamp}-{end_timestamp}明细数据")
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
                # "unionSearchTotalNum": "0",
                # "refund": "ALL",
                "unionSearchPageNum": "0",
                "yushouStatus": "ALL",
                "deliveryTimeType": "ALL",
                "payMethodType": "ALL",
                "orderType": "ALL",
                "appName": "ALL",
                "exportType": "2",
                "fileType": "xlsx",
                "selectFieldIds": "1,2,3,4,5,6,7,8,9,10,11,17,19,20,21,22,23,24,12,13,14,15,16,18,28,29,30,25,26,27,31,32,35,33,34",
                "newExportPlatform": True,
                "event_submit_do_apply_export": "1",
                }

        headers = {
            "referer": "https://myseller.taobao.com/home.htm/trade-platform/tp/sold",
            "Content-Type": "application/x-www-form-urlencoded",
            "user-agent": self.ua,
            "cookie": self.cookie
        }
        res = requests.post(api, params=params, data=data, headers=headers)

        req_log(res)

        try:
            # 获取报表生成信息
            html = etree.HTML(res.text)
            create_time = html.xpath("//h2[@class='sheet-item-hd']/text()")

            if "正在生成订单报表" not in res.text:
                logger.info(f"五分钟之内有创建报表,返回的是历史的:{create_time}")
                return {
                    "code": 1,
                    "message": "五分钟之内已经生成过了,返回的是历史的",
                    "data": create_time
                }
            else:
                logger.info(f"新导出任务,返回的是新的:{create_time[0:1]}")
                return {
                    "code": 1,
                    "message": "新导出任务,返回的是新的",
                    "data": create_time[0:1]
                }

        except Exception as e:
            logger.error(e)
            return {
                "code": 0,
                "message": f"{e, e.args}",
                "data": None
            }

    def trade_order_exportlist(self):
        """
        交易订单导出列表
        :return:
        """
        api = "https://h5api.m.taobao.com/h5/mtop.taobao.trade.order.exportlist/1.0/"
        cookie_token = self.get_cookie_token(self.cookie)
        token = cookie_token["token"]
        new_cookie = self.get_new_cookie(self.cookie, cookie_token["_m_h5_tk"], cookie_token["_m_h5_tk_enc"])
        data = '{"page":"1"}'
        t = self.get_time_13()
        sign = self.get_sign(token, t, data)
        params = {
            "jsv": "2.6.1",
            "appKey": "12574478",
            "t": t,
            "sign": sign,
            "api": "mtop.taobao.trade.order.exportlist",
            "v": "1.0",
            "ttid": "11320@taobao_WEB_9.9.99",
            "type": "jsonp",
            "valueType": "string",
            "dataType": "originaljsonp",
            "callback": "mtopjsonp14",
            "data": data,

        }
        headers = {
            "user-agent": self.ua,
            "cookie": new_cookie
        }
        res = requests.get(url=api, params=params, headers=headers)
        req_log(res)
        return res.text

    def export_by_tfs(self, f_p, apply_time, startTimeStr, endTimeStr, orderStatus, exportId):
        api = "https://trade.taobao.com/trade/itemlist/export_by_tfs.do"
        params = {
            "f_p": f_p,
            "apply_time": apply_time,
            "start_time": startTimeStr,
            "end_time": endTimeStr,
            "order_status": orderStatus,
            "export_id": exportId,
            "isQnNew": "true",
        }
        headers = {
            "user-agent": self.ua,
            "cookie": self.cookie,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        }
        res = requests.get(url=api, params=params, headers=headers)
        self.req_log(res)
        return res.content

    def disputelist(self):
        api = "https://h5api.m.taobao.com/h5/mtop.alibaba.refundface2.disputeservice.qianniu.pc.disputelist/1.0/"
        cookie_token = self.get_cookie_token(self.cookie)
        token = cookie_token["token"]
        new_cookie = self.get_new_cookie(self.cookie, cookie_token["_m_h5_tk"], cookie_token["_m_h5_tk_enc"])
        data = {
            "data": '{"params":"{\\"subPageGray\\":\\"0\\",\\"privacySwitchIsCheck\\":false,\\"isQnNew\\":true,\\"isHideNick\\":true,\\"quickQuerySelect\\":\\"\\",\\"quickQueryChange\\":false,\\"autoRefundToolSelect\\":\\"\\",\\"refundStatusSelect\\":\\"-9999\\",\\"bizTypeSelect\\":\\"-1\\",\\"csStatusSelect\\":\\"\\",\\"refundReasonSelect\\":\\"\\",\\"unionSearch\\":\\"\\",\\"disputeIdInput\\":\\"\\",\\"logisticsNoInput\\":\\"\\",\\"pageNo\\":1}"}'
        }
        t = self.get_time_13()

        sign = self.get_sign(token, t, data["data"])
        params = {
            "jsv": "2.6.1",
            "appKey": "12574478",
            "t": t,
            "sign": sign,
            "api": "mtop.alibaba.refundface2.disputeservice.qianniu.pc.disputelist",
            "v": "1.0",
            "ttid": "11320@taobao_WEB_9.9.99",
            "type": "originaljson",
            "dataType": "json",

        }
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": self.ua,
            "cookie": new_cookie
        }
        # print(urlencode(data))
        # # print(payload)
        res = requests.post(url=api, params=params, headers=headers, data=data)
        self.req_log(res)
        return res.json()

    def refund2_download_check(self, dataKey, downloadUrl):
        """
        检查下载任务
        :return:
        """
        api = "https://refund2.taobao.com/dispute/download/downloadCheck.json"
        params = {
            "dataKey": dataKey
        }
        headers = {
            "user-agent": self.ua,
            "cookie": self.cookie,
            "referer": f"https://refund2.taobao.com{downloadUrl}",
        }
        res = requests.get(url=api, params=params, headers=headers)
        self.req_log(res)
        return res.text

    def refund2_download_excel(self, dataKey):
        """
        退款excel下载
        :return:
        """
        api = "https://refund2.taobao.com/dispute/download/downloadDisputeList.json"
        params = {
            "dataKey": dataKey
        }
        headers = {
            "user-agent": self.ua,
            "cookie": self.cookie,
        }
        res = requests.get(url=api, params=params, headers=headers)
        self.req_log(res)
        print(res.content)
        return res.content

    def prepare_download(self, downloadUrl):
        url = f"https://refund2.taobao.com{downloadUrl}"
        headers = {
            "user-agent": self.ua,
            "cookie": self.cookie,
            "Referer": "https://myseller.taobao.com/home.htm/trade-platform/refund-list"
        }
        res = requests.get(url=url, headers=headers)
        self.req_log(res)
        return res.text

# m=MySellerTradeAPI('thw=cn; wk_cookie2=1de33e37072f0ef696f0385c1905c161; wk_unb=UoH%2B4NPsNoWZlw%3D%3D; t=61f6d9516106249f280ae435a10c9a79; xlly_s=1; cookie2=112de8da413521694820b810eb275b0d; _tb_token_=e3e65e33b73be; _samesite_flag_=true; 3PcFlag=1745544422298; sgcookie=E1001CWMWBHtyQsr2R0jRK6Ow%2FhyJZEAS%2FJ7CS4YDvMUhVHAizZwWBynHx9dwW5Uxe55TvgcuNtJPL7P0pcBZvNACZKAdpfRibuvq40yyNqMqBVDhJdU%2Fhfp0RQN9nbrOivJ; unb=2212373938588; sn=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; uc1=cookie21=VFC%2FuZ9aj3yE&cookie14=UoYajlClMl8STA%3D%3D; csg=a34d35ba; _cc_=V32FPkk%2Fhw%3D%3D; cancelledSubSites=empty; skt=04a9e25a0de8784c; cna=v21ZIJhrkh0CASeqbVqkh3yc; mtop_partitioned_detect=1; _m_h5_tk=2c089f65ac29c9434d1007e1e5555a1a_1745554149127; _m_h5_tk_enc=dc88e7402f01e36825ada229473b2e5a; tfstk=gCnj-MDynsfjT0ZOCrvzdV8KYcr6LL-eDOwtKAIVBoExfhHtOlrwnPu7BflkIKqqB5Gsa7cagxJmPOMnNSIa7E21f7kTbKVwIfata72Zud2q5RNrwxS4_cglfvDi0KqwnoD0jldeTHrsnxqGqvoAxmsRyRkRD-evzuIwbkwpTH-EHEe0bYdEbVwAW7wFXlUYW3B8Z-IY6fUAygFuIRCYBipWF721H5FAXzK8pRsYXlhteLwTw-ETkfH-Na-7UdPjhKA4WFHAdOoYNGItV8dg9xTC0Ji4htNZF7TWk0sQlWHYNGdHdU4L17mpaUMo6qh4EftBNk3nNcaLfn13h4HQ2SrpRaZjUjmQDDOf08z_G4nYPOItpxFuJVGXGZVxuba3ezB6x8lUwxmxPdf-HXPbD8UyvpM8W4o0-mRRck3n3out9Q74M2wO4gjUOLvR5Tahf8NeFL_GShpkI0rbsrFgk82PTL95GuUYE8NeFL_GSreuULJWFsZR.')
# print(m.disputelist())
# print(m.refund2_download_check("22123756223121745566023836"))
# m.refund2_download_excel("22123756223121745569463226")
# """
# https://refund2.taobao.com/dispute/download/downloadDisputeList.json?dataKey=22123756223121745561074567
# """
