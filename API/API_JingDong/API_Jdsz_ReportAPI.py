# -*- coding: utf-8 -*-
# @Time : 2024/9/18 17:27
# @Author : Shao0000
# @Email : Shao0000@aliyun.com
# @File : API_Jdsz_ReportAPI.py
# @Project : JDSZ
import io
import json
import uuid
from urllib.parse import urlencode, quote
import zipfile
import pandas as pd
import requests

from API.API_JingDong.API_Jdsz_Base import JdszBaseAPI
from extra.downloader import Downloader
from extra.extra_reqlog import req_log


class JdszReportAPI(JdszBaseAPI):
    """
        京东商智》》报表
        """

    def __init__(self, cookie=None):
        # 初始化cookie和店铺名称
        super().__init__(cookie)

    def fetch_report_analysis__my_report(self, start_date, end_date):
        """
        报表分析》》我的报表》》新建报表>>维度：店铺
                                    汇总周期：自然天
                                    查询日期：自定义
                                    选择指标：流量指标、交易指标、其他指标

        todo 预览的只显示五条数据,预览的只显示五条数据,预览的只显示五条数据
        :return:
        """
        host = "https://sz.jd.com"
        api = "/sz/api/selfHelpAnalysis/createPagePreview.ajax"
        indicators = [{"text": "老客户数", "value": "OldUserNum", "selected": True, "index": 1},
                      {"text": "新客户数", "value": "NewUserNum", "selected": True, "index": 2},
                      {"text": "新访客数-全部渠道", "value": "ANUV", "selected": True, "index": 3},
                      {"text": "老访客数-全部渠道", "value": "AOUV", "selected": True, "index": 4},
                      {"text": "加购商品件数-全部渠道", "value": "AAddPie", "selected": True, "index": 5},
                      {"text": "加购客户数-全部渠道", "value": "AAddCustNum", "selected": True, "index": 6},
                      {"text": "商品加购率(SPU)-全部渠道", "value": "AAddRate", "selected": True, "index": 7},
                      {"text": "上架商品数(SPU)", "value": "SheSpuNum", "selected": True, "index": 8}]
        params = {
            "Indicators": json.dumps(indicators),
            "ReportCycle": "0",
            "ReportDim": "0",
            "UpdateNum": "0",
            "endDate": end_date,
            "startDate": start_date
        }
        url = host + api + "?" + urlencode(params)
        headers = self.common_headers(api, host)
        res = requests.get(url=url, headers=headers)
        req_log(res)
        # print(res.json())
        return res.json()

    def sz_api_self_help_analysis_export_preview_list(self, start_date, end_date):
        """
       报表分析》》我的报表》》新建报表>>维度：店铺
                                   汇总周期：自然天
                                   查询日期：自定义
                                   选择指标：流量指标、交易指标、其他指标
        excel 导出方式
       :return:
       """
        host = "https://sz.jd.com"
        api = "/sz/api/selfHelpAnalysis/exportPreviewList.ajax"
        indicators = [{"text": "老客户数", "value": "OldUserNum", "selected": True, "index": 1},
                      {"text": "新客户数", "value": "NewUserNum", "selected": True, "index": 2},
                      {"value": "ANUV", "text": "新访客数-全部渠道", "selected": True, "index": 3},  # noqa
                      {"value": "AOUV", "text": "老访客数-全部渠道", "selected": True, "index": 4},  # noqa
                      {"value": "AAddPie", "text": "加购商品件数-全部渠道", "selected": True, "index": 5},
                      {"value": "AAddCustNum", "text": "加购客户数-全部渠道", "selected": True, "index": 6},
                      {"value": "AAddRate", "text": "商品加购率(SPU)-全部渠道", "selected": True, "index": 7},
                      {"text": "上架商品数(SPU)", "value": "SheSpuNum", "selected": True, "index": 8}]
        user_mnp_mup = self.fetch_user_mnp_mup(api, host, self.ua)
        data = {
            "Indicators": indicators,
            "ReportCycle": "0",
            "ReportDim": "0",
            "UpdateNum": "0",
            "endDate": end_date,
            "startDate": start_date,
            "ReportName": str(uuid.uuid4()),
            "Uuid": str(uuid.uuid4()),
            "User-Mnp": user_mnp_mup["User-Mnp"],
            "User-Mup": user_mnp_mup["User-Mup"],

        }
        data.update(user_mnp_mup)
        # 构建查询字符串
        query_parts = [
            f'ReportDim={data["ReportDim"]}',
            f'Indicators={quote(json.dumps(data["Indicators"], ensure_ascii=False).replace(" ", ""), safe="")}',
            f'startDate={data["startDate"]}',
            f'endDate={data["endDate"]}',
            f'ReportCycle={data["ReportCycle"]}',
            f'UpdateNum={data["UpdateNum"]}',
            f'ReportName={data["ReportName"]}',
            f'User-mup={data["User-Mup"]}',
            f'uuid={data["Uuid"]}',
            f'User-mnp={data["User-Mnp"]}'
        ]

        # 拼接查询字符串
        query_string = '&'.join(query_parts)
        url = host + api
        headers = {
            "user-agent": self.ua,
            "content-type": "application/x-www-form-urlencoded",
            # "accept-encoding": "gzip, deflate, br, zstd",
            # "referer": "https://sz.jd.com/sz/view/selfHelp/reportCreates.html",
            # "cookie": self.cookie
        }
        items = Downloader(url, method="post", data=query_string, timeout=30, headers=headers,
                             cookie=self.cookie).download_zip(file_type='excel')
        # res = requests.post(url=url, headers=headers, data=query_string)
        # req_log(res)
        # excel_bytes = self.read_res_zip(res)
        # df = pd.read_excel(excel_bytes)
        # print(df)
        return items

# JdSzReportAPI(
#     "__jdu=17128841794611080014451; shshshfpa=ff199980-2ccb-2f94-ea01-0d2a87125880-1712884180; shshshfpx=ff199980-2ccb-2f94-ea01-0d2a87125880-1712884180; pinId=5ielbAPrAn16XSvstWe_upOTLmjz9-rFtX37H5_fCPs; _tp=PA0O05611ewkh35ThCZAsOo4flYQqIDKRm%2FbgAr64D19Eftp%2F46HvUXpP4o9gI09s8vIaqreO6VE7N6K5pJprU6NSp4kZ6bUnZ5d23bMXII%3D; _pst=%E5%87%AF%E8%BF%AA%E4%BB%95%E6%97%97%E8%88%B0%E5%BA%97%E4%B8%80%E5%85%83; user-key=da48b6ce-07a5-4d08-8a49-e80e2c922e79; unpl=JF8EAOVnNSttXEtRAhhXH0YUQ1UAW1xYTx9ROzQBBg5eQwFWH1ESRRF7XlVdWBRKHx9ubxRUWlNLVw4aACsSEXtdVV9fD0oeBm5vNWRdURxUAhMFEkIXJV06Kw99IB55bmdgKlw2S1UEGgIeFxZKXFdXEAl7FANfZjVUW1hIXQweAh0aFUxdVF9UCUoXBmpjBWRcaEtcASsCGhMRS1hRWFwJSB4zX2IFVVxdTVYEHAsrEyBJXFVbXQ9DHgZuV0c6ivH8g4WqVEXFlNOL4dkQCE0XAGZuAFRbUE5TBRsDEhMRS1hRWl04SicA; ipLoc-djd=15-1213-3038-59931; __jdv=181111935|lianmeng__10__www.baidu.com|t_1003608409_|tuiguang|51462d5e599e40a59ceb5cb79db5b8f0|1725869542226; _base_=YKH2KDFHMOZBLCUV7NSRBWQUJPBI7JIMU5R3EFJ5UDHJ5LCU7R2NILKK5UJ6GLA2RGYT464UKXAI5KK7PNC5B5UHJ2HVQ4ENFP57OC6UPRTPT7BYXJ5UY7WDLCIQ3KIZTCNE6YVKRXISUNWUBGVW24EBBWS3GKYL2ZCNGXSSG4SOQWCP5WPWO6EFS7HEHMRWVKBRVHB33TFD45K2XF6THXXYXAU2WY74DWFDQ6GKT47K7XGVE7YEL3DXFKRPELDLJPMYLPHA2QEJEOMMXYF2GDYNTS7WGAUXFEWRJ3CTKDBDWMHUKJQF4ZFOTNBBYBIZRXZYERXXIG6ATE2WEVXHOS7UI73DYVSQUEJLGXRUIAOMDVFLTMMJDHVJG2NPHNWQXMSSL3WSB2Z4JN5GJFJV6ALJWI; is_sz_old_version=false; wlfstk_smdl=urgxoitkxnfvnkh1tkc13xshwwa8n83i; TrackID=1jsk3EVQ5IgP4DVE5miBzyqpAMPpNJyEiLCPPSQNojZu_hjksoj4_ZR-E3qzbd2ZmyZiYnhwE7gR3LR4uqhD6Sqtmguc1uwX0c4dUOtbr1N6-zLxp9SjyxaT16LrCxjzH; thor=CD29DD035C470B44B96F330154F60EED5DC3E4A3D4C1C3E4A7C8CF36225341A10C7E6752AA190B24F7D56EBA0850979A6D17CFFA73F938D22F928CCF1CC7D788B7E0CDDD843E9ACEA912FF14F3E60DA97D34B84367B0AC5BD8F9371D0050FB8BDB7B35395C395B353CC25E3D3D90E285698C527FAD8AE9BB2C19C0BB81500075880EF2BD50AA84FAECC97E37A126E8EF; light_key=AASBKE7rOxgWQziEhC_QY6yahxfvfx9EFRdoAajTB9aJegmUb2pTJk-O0oud3JBG3HVTYsfCwdUpmF0zFcmR8dli7_uIrQ; pin=%E5%87%AF%E8%BF%AA%E4%BB%95%E6%97%97%E8%88%B0%E5%BA%97%E4%B8%80%E5%85%83; unick=x5iv1c85wjle9d; ceshi3.com=000; cn=0; shshshfpb=BApXSd8DKAPdA7zeQ3ozBIFjIZF081OlaBlDJRq9k9xJ1MmqyBYC2; 3AB9D23F7A4B3C9B=PFDPVWVZYAOF4COE4E56DQF7WA3ZGR46C3SRYPLNO7N7OT6KOBAWAQRA362QCCK2A37KZRYUR64TBYEL7IRHW3HHP4; __jdc=251704139; __jda=251704139.17128841794611080014451.1712884179.1726727382.1726729788.37; __jdb=251704139.18.17128841794611080014451|37.1726729788; 3AB9D23F7A4B3CSS=jdd03PFDPVWVZYAOF4COE4E56DQF7WA3ZGR46C3SRYPLNO7N7OT6KOBAWAQRA362QCCK2A37KZRYUR64TBYEL7IRHW3HHP4AAAAMSBFTSA4YAAAAAD5GOOHCAMWZRHUX; flash=3_kftlXDt1_K9j_2jqKnka8bON9bAXmZRa5L4Vg91BOPSPzf-gxwxCkbcp3fSvLA8hdQOj3NMpdqoI8WLeAuC54fdfDmjb6jQ0pjEvGl9B4jgk3XEQhjG-32EOGDaPqnFunnS5A3a-an66mRz8On2NmR1aUTpvTt0BqAq4rK0DaLWRz06VaFRWPUgboyndPupW").fetch_report_analysis__my_report__excel()
