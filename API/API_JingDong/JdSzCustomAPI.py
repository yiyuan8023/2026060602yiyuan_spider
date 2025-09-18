# -*- coding: utf-8 -*-
# @Time : 2024/9/18 17:48
# @Author : Shao0000
# @Email : Shao0000@aliyun.com
# @File : JdSzCustomAPI.py
# @Project : JDSZ
import json
from urllib.parse import urlencode

import requests

from API_Jdsz_Base import JdSzAPI
from settings_pass import UA


class JdSzCustomAPI(JdSzAPI):
    """
        京东商智》》客户
        """

    def __init__(self, cookie=None, shop_name=None,account_name=None):
        # 初始化cookie和店铺名称
        super().__init__(cookie,shop_name,account_name)

    def fetch_fans_summary__data_summary(self, startDate, endDate, date):
        """
        关注店铺用户》》关注店铺用户概况》》数据概况
        :return:
        """
        host = "https://sz.jd.com"
        api = "/sz/api/cust/fansSummary/detail.ajax"
        params = {
            "date": date,
            "startDate": startDate,
            "endDate": endDate
        }
        url = host + api + "?" + urlencode(params)
        headers = self.common_headers(api, host)
        res = requests.get(url=url, headers=headers)
        self.req_log(res)
        # print(res.json())
        return res.json()

    def fetch_vip_summary__data_summary(self, startDate, endDate, date):
        """
        品牌会员》》会员概况》》数据概况
        :return:
        """
        host = "https://szgateway.jd.com"
        api = "/szpaas/lowcode/szajax/query/memberOverview.ajax"
        user_mnp_mup = self.fetch_user_mnp_mup(api, host, self.ua)
        params = {

            "User-mup": str(user_mnp_mup["User-Mup"]),
            "User-mnp": user_mnp_mup["User-Mnp"],
            "uuid": user_mnp_mup["Uuid"]
        }

        payload = json.dumps({
            "filterList": [
                {
                    "propertyName": "dt",
                    "values": [
                        startDate
                    ],
                    "op": ">=",
                    "type": "string"
                },
                {
                    "propertyName": "dt",
                    "values": [
                        endDate
                    ],
                    "op": "<=",
                    "type": "string"
                },
                {
                    "propertyName": "time_interval",
                    "values": [
                        "BY_DAY"
                    ],
                    "op": "=",
                    "type": "string"
                }
            ],
            "dimList": [
                "dt",
                "time_interval"
            ],
            "metricList": [
                "jdr_sch_user_authentication_member_shop_cnt_shopversion_brandmem@date_end&brandmem_card",
                "jdr_sch_user_authentication_member_shop_cnt_shopversion_brandmem_increase@brandmem_card",
                "jdr_sch_user_open_member_shop_cnt_shopversion_brandmem@brandmem_card",
                "jdr_sch_user_invalid_member_shop_cnt_shopversion_brandmem@brandmem_card",
                "jdr_sch_user_authentication_member_shop_cnt_shopversion_brandmem_client@brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz@brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_dis_qtty_shopversion_brandmem_sz@brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_amt_shopversion_brandmem_sz@brandmem_card",
                "jdr_sch_mkt_brow_shop_cnt_shopversion_brandmem_sz@brandmem_card&browse_brand",
                "jdr_sch_mkt_brow_shop_qtty_shopversion_brandmem_sz@brandmem_card&browse_brand",
                "jdr_sch_mkt_brow_sku_qtty_shopversion_brandmem_sz@brandmem_card&browse_brand",
                "jdr_sch_user_follow_sku_sku_qtty_shopversion_brandmem@brandmem_card&follow_brand",
                "jdr_sch_mkt_brow_shop_cnt_shopversion_brandmem_sz@brandmem_card&add_cart",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_ld30_rebuy_brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_brandmem_card_ld30",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_rebuy_90d_brandmem_card",
                "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_brandmem_card_90d"
            ],
            "groupList": [],
            "attributeList": [],
            "commonParam": {
                "platformId": 0,
                "userErp": "",
                "period": 0,
                "startTime": 0,
                "endTime": 0,
                "indexFreq": "OFFLINE",
                "description": "开卡会员数据概览指标数据集-指标服务1",
                "annotation": "基础",
                "page": -1,
                "pageSize": 100,
                "resAppKey": "lowcode2772",
                "traceId":  params["uuid"],
                "date": date,
                "startDate": startDate,
                "endDate": endDate,
                "dateType": "day"
            }
        })
        headers = {
            'User-Agent': self.ua,
            'Referer': 'https://sz.jd.com/szweb/sz/view/brandMember/memberOverview.html',
            'Cookie': self.cookie,
            'Content-Type': 'application/json'
        }

        url=host+api+"?"+urlencode(params)
        res = requests.post( url=url, headers=headers, data=payload)
        self.req_log(res)
        return res.json()


# JdSzCustomAPI(
#     "__jdu=17128841794611080014451; shshshfpa=ff199980-2ccb-2f94-ea01-0d2a87125880-1712884180; shshshfpx=ff199980-2ccb-2f94-ea01-0d2a87125880-1712884180; pinId=5ielbAPrAn16XSvstWe_upOTLmjz9-rFtX37H5_fCPs; _tp=PA0O05611ewkh35ThCZAsOo4flYQqIDKRm%2FbgAr64D19Eftp%2F46HvUXpP4o9gI09s8vIaqreO6VE7N6K5pJprU6NSp4kZ6bUnZ5d23bMXII%3D; _pst=%E5%87%AF%E8%BF%AA%E4%BB%95%E6%97%97%E8%88%B0%E5%BA%97%E4%B8%80%E5%85%83; user-key=da48b6ce-07a5-4d08-8a49-e80e2c922e79; unpl=JF8EAOVnNSttXEtRAhhXH0YUQ1UAW1xYTx9ROzQBBg5eQwFWH1ESRRF7XlVdWBRKHx9ubxRUWlNLVw4aACsSEXtdVV9fD0oeBm5vNWRdURxUAhMFEkIXJV06Kw99IB55bmdgKlw2S1UEGgIeFxZKXFdXEAl7FANfZjVUW1hIXQweAh0aFUxdVF9UCUoXBmpjBWRcaEtcASsCGhMRS1hRWFwJSB4zX2IFVVxdTVYEHAsrEyBJXFVbXQ9DHgZuV0c6ivH8g4WqVEXFlNOL4dkQCE0XAGZuAFRbUE5TBRsDEhMRS1hRWl04SicA; areaId=15; ipLoc-djd=15-1213-3038-59931; __jdv=181111935|lianmeng__10__www.baidu.com|t_1003608409_|tuiguang|51462d5e599e40a59ceb5cb79db5b8f0|1725869542226; _base_=YKH2KDFHMOZBLCUV7NSRBWQUJPBI7JIMU5R3EFJ5UDHJ5LCU7R2NILKK5UJ6GLA2RGYT464UKXAI5KK7PNC5B5UHJ2HVQ4ENFP57OC6UPRTPT7BYXJ5UY7WDLCIQ3KIZTCNE6YVKRXISUNWUBGVW24EBBWS3GKYL2ZCNGXSSG4SOQWCP5WPWO6EFS7HEHMRWVKBRVHB33TFD45K2XF6THXXYXAU2WY74DWFDQ6GKT47K7XGVE7YEL3DXFKRPELDLJPMYLPHA2QEJEOMMXYF2GDYNTS7WGAUXFEWRJ3CTKDBDWMHUKJQF4ZFOTNBBYBIZRXZYERXXIG6ATE2WEVXHOS7UI73DYVSQUEJLGXRUIAOMDVFLTMMJDHVJG2NPHNWQXMSSL3WSB2Z4JN5GJFJV6ALJWI; is_sz_old_version=false; wlfstk_smdl=urgxoitkxnfvnkh1tkc13xshwwa8n83i; TrackID=1jsk3EVQ5IgP4DVE5miBzyqpAMPpNJyEiLCPPSQNojZu_hjksoj4_ZR-E3qzbd2ZmyZiYnhwE7gR3LR4uqhD6Sqtmguc1uwX0c4dUOtbr1N6-zLxp9SjyxaT16LrCxjzH; thor=CD29DD035C470B44B96F330154F60EED5DC3E4A3D4C1C3E4A7C8CF36225341A10C7E6752AA190B24F7D56EBA0850979A6D17CFFA73F938D22F928CCF1CC7D788B7E0CDDD843E9ACEA912FF14F3E60DA97D34B84367B0AC5BD8F9371D0050FB8BDB7B35395C395B353CC25E3D3D90E285698C527FAD8AE9BB2C19C0BB81500075880EF2BD50AA84FAECC97E37A126E8EF; light_key=AASBKE7rOxgWQziEhC_QY6yahxfvfx9EFRdoAajTB9aJegmUb2pTJk-O0oud3JBG3HVTYsfCwdUpmF0zFcmR8dli7_uIrQ; pin=%E5%87%AF%E8%BF%AA%E4%BB%95%E6%97%97%E8%88%B0%E5%BA%97%E4%B8%80%E5%85%83; unick=x5iv1c85wjle9d; ceshi3.com=000; cn=0; shshshfpb=BApXSd8DKAPdA7zeQ3ozBIFjIZF081OlaBlDJRq9k9xJ1MmqyBYC2; 3AB9D23F7A4B3C9B=PFDPVWVZYAOF4COE4E56DQF7WA3ZGR46C3SRYPLNO7N7OT6KOBAWAQRA362QCCK2A37KZRYUR64TBYEL7IRHW3HHP4; __jdc=251704139; 3AB9D23F7A4B3CSS=jdd03PFDPVWVZYAOF4COE4E56DQF7WA3ZGR46C3SRYPLNO7N7OT6KOBAWAQRA362QCCK2A37KZRYUR64TBYEL7IRHW3HHP4AAAAMSAR4KSWIAAAAACBRTXY5BAVSS5QX; flash=3_kXuANb5qt2Qjd4k5NHYb2bIGJJZSUI-b5zHv_peTvglPgO63ZLZZfbcIaNXTsJJLdfw5eblX6FMI4f4Lcy3pMf0nNY6R_uTCpgf9_hpTrgWkOMiOjzHIX2SzHY9sDehlnTrHf2c0I9T6MhjQaH_kRR_-YjKT2MN3qehnMai9I4GR9N-MOQXA-Ug76l18oj44; __jda=251704139.17128841794611080014451.1712884179.1726727382.1726729788.37; __jdb=251704139.5.17128841794611080014451|37.1726729788").fetch_vip_summary__data_summary()
