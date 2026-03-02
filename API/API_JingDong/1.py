import requests
import json

url = "https://szgateway.jd.com/szpaas/lowcode/szajax/query/memberOverview.ajax?User-mup=1727418572164&User-mnp=f98d6dcb0c757b94e938dce9453fd04d&uuid=369bbccb-4b5d-4570-ac1e-ba7aac5f3dcc"

payload = json.dumps(
    {
        "filterList": [
            {
                "propertyName": "dt",
                "values": ["2024-09-24"],
                "op": ">=",
                "type": "string",
            },
            {
                "propertyName": "dt",
                "values": ["2024-09-24"],
                "op": "<=",
                "type": "string",
            },
            {
                "propertyName": "time_interval",
                "values": ["BY_DAY"],
                "op": "=",
                "type": "string",
            },
        ],
        "dimList": ["dt", "time_interval"],
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
            "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_brandmem_card_90d",
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
            "traceId": "369bbccb-4b5d-4570-ac1e-ba7aac5f3dcc",
            "date": "2024-09-24",
            "startDate": "2024-09-24",
            "endDate": "2024-09-24",
            "dateType": "day",
        },
    }
)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Referer": "https://sz.jd.com/szweb/sz/view/brandMember/memberOverview.html",
    "Cookie": "__jdu=17128841794611080014451; shshshfpa=ff199980-2ccb-2f94-ea01-0d2a87125880-1712884180; shshshfpx=ff199980-2ccb-2f94-ea01-0d2a87125880-1712884180; unpl=JF8EAOVnNSttXEtRAhhXH0YUQ1UAW1xYTx9ROzQBBg5eQwFWH1ESRRF7XlVdWBRKHx9ubxRUWlNLVw4aACsSEXtdVV9fD0oeBm5vNWRdURxUAhMFEkIXJV06Kw99IB55bmdgKlw2S1UEGgIeFxZKXFdXEAl7FANfZjVUW1hIXQweAh0aFUxdVF9UCUoXBmpjBWRcaEtcASsCGhMRS1hRWFwJSB4zX2IFVVxdTVYEHAsrEyBJXFVbXQ9DHgZuV0c6ivH8g4WqVEXFlNOL4dkQCE0XAGZuAFRbUE5TBRsDEhMRS1hRWl04SicA; ipLoc-djd=15-1213-3038-59931; _base_=YKH2KDFHMOZBLCUV7NSRBWQUJPBI7JIMU5R3EFJ5UDHJ5LCU7R2NILKK5UJ6GLA2RGYT464UKXAI5KK7PNC5B5UHJ2HVQ4ENFP57OC6UPRTPT7BYXJ5UY7WDLCIQ3KIZTCNE6YVKRXISUNWUBGVW24EBBWS3GKYL2ZCNGXSSG4SOQWCP5WPWO6EFS7HEHMRWVKBRVHB33TFD45K2XF6THXXYXAU2WY74DWFDQ6GKT47K7XGVE7YEL3DXFKRPELDLJPMYLPHA2QEJEOMMXYF2GDYNTS7WGAUXFEWRJ3CTKDBDWMHUKJQF4ZFOTNBBYBIZRXZYERXXIG6ATE2WEVXHOS7UI73DYVSQUEJLGXRUIAOMDVFLTMMJDHVJG2NPHNWQXMSSL3WSB2Z4JN5GJFJV6ALJWI; __jdv=251704139|direct|-|none|-|1727230535804; user-key=047aa9da-6d8f-408c-bb48-dca5623e47aa; cn=0; ceshi3.com=000; is_sz_old_version=false; shshshfpb=BApXS8H2lLvdA7zeQ3ozBIFjIZF081OlaBlDJRq9m9xJ1MmqyBYC2; 3AB9D23F7A4B3C9B=PFDPVWVZYAOF4COE4E56DQF7WA3ZGR46C3SRYPLNO7N7OT6KOBAWAQRA362QCCK2A37KZRYUR64TBYEL7IRHW3HHP4; wlfstk_smdl=s3lx5v4mt32il5seoyzrr4y7zbng54tx; TrackID=1BiHvxCugBxiujZ3kodQixQor-PYENN-AYb3lTg-BPPU8ywawhq6Tx6a3Z9PmLWqyiWbaIZaHBEAQTiVbNrDGlj6NvHrwEQT35XH6v-7i1z8; thor=9B7D261423F5AFC41F84C40CE88F8B16B2C1FBC5C0005208B587D52A0194E4EEE47B43E3995F85D7B581A8A5AF54D5A606F3393E4967B559073C70E91410588605D701417166AAD6802B20A437F02ACA368A1FF085EEA7816930FFE491FDD44AF93BAF4B55467A219AEB9284827418A7AA34C2EFD787E3494A708D321B44E81CA24FE805D9683987EF52E753AA296003; light_key=AASBKE7rOxgWQziEhC_QY6yat38ie3qlkXPYjLdzzQ9fa0WKDiZTDPg7buj9nfGqagApqmc65MnV3U3bWjx68gPFb08jZQ; pinId=O3Tk9AZNlW3r7oU18LMekJzlVsJt5LNd; pin=%E6%9D%9C%E6%8B%89%E7%BB%B4%E7%89%B9_%E4%B8%80%E5%85%83; unick=ef9uxz36m64usn; _tp=nE6veHKcCp5FmsyJjRk3fJdd6VWO94cT4GZ86iq2y0x7g43mKG5u4%2BKBLCtBiStdL3FI9Er12WV%2Fp6pwcmTfMg%3D%3D; _pst=%E6%9D%9C%E6%8B%89%E7%BB%B4%E7%89%B9_%E4%B8%80%E5%85%83; __jdc=251704139; 3AB9D23F7A4B3CSS=jdd03PFDPVWVZYAOF4COE4E56DQF7WA3ZGR46C3SRYPLNO7N7OT6KOBAWAQRA362QCCK2A37KZRYUR64TBYEL7IRHW3HHP4AAAAMSGFGFAGIAAAAADKMDWR2NWMHAP4X; __jda=251704139.17128841794611080014451.1712884179.1727416096.1727418488.50; flash=3_WKqpfLS0bJR4MhAt4-fqS1eXcw9OLyMB5WfdwCR5fBuFi6X2bRXIN12uMVgw4ypFdYVp4i4GMyDOb3kQs681yJUAn6s9oeh1ptBuGoyWdOCuG1Re04uZFEBMwndgkwSymQf_vugRhAL3U1bpXdReVY0juicT6tYEHgFhNt0NxWlPixOlgLGJV_fk7q**; __jdb=251704139.2.17128841794611080014451|50.1727418488",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Host": "szgateway.jd.com",
    "Connection": "keep-alive",
}
"https://szgateway.jd.com/szpaas/lowcode/szajax/query/memberOverview.ajax?User-Mup=1727418572164&User-Mnp=f98d6dcb0c757b94e938dce9453fd04d&uuid=369bbccb-4b5d-4570-ac1e-ba7aac5f3dcc"
"https://szgateway.jd.com/szpaas/lowcode/szajax/query/memberOverview.ajax?User-mup=1727418572164&User-mnp=f98d6dcb0c757b94e938dce9453fd04d&uuid=369bbccb-4b5d-4570-ac1e-ba7aac5f3dcc"
# print(payload)
# print(url)
response = requests.request("POST", url, headers=headers, data=payload)
# print(response.request.headers)
# print(response.text)
