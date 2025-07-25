import io
from urllib.parse import urlencode

import pandas as pd
import requests

from ShengCanApi.ShengCanBase import ShengCanBaseApi
from logger_ import logger
from extra_time import get_date
from settings import UA


class Flow(ShengCanBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def shop_from__flow_from_build_day(self, days=-1):
        """
        店铺来源》》流量来源构成 日
        """
        api = "https://sycm.taobao.com/flow/gray/excel.do?"
        params = {
            "_path_": "v4/excel/shop/source/v3",
            "device": 2,
            "dateType": "day",
            "dateRange": f"{get_date(days)}|{get_date(days)}",
            "belong": "all"
        }
        url = api + urlencode(params)
        print(url)
        res = requests.get(url, headers={
            "User-Agent": UA,
            "cookie": self.cookie})
        self.req_log(res)
        try:
            data = io.BytesIO(res.content)
            df = pd.read_excel(data,skiprows=5)
            if df.empty:
                return {}
            else:
                items = df.to_dict('records')
                return items
        except Exception as e:
            # logger.error(f"{res.text}")
            return None

    def shop_from__flow_from_build__shop_flow_day(self,days=-1):
        api = "https://sycm.taobao.com/flow/gray/excel.do?"
        params = {
            "_path_": "v4/excel/shop/source/summay/v4",
            "dateType": "day",
            "dateRange": f"{get_date(days)}|{get_date(days)}",
            "crowdType": "all",
            "needCate":"undefined"
        }
        url = api + urlencode(params)
        # print(url)
        res = requests.get(url, headers={
            "User-Agent": UA,
            "cookie": self.cookie})
        self.req_log(res)
        try:
            res_data = []
            data = io.BytesIO(res.content)
            all_sheets = pd.read_excel(data, sheet_name=None, skiprows=5)
            items_dict={}
            for sheet_name, df in all_sheets.items():
                # print(sheet_name)
                # print(df)
                # print(f"Sheet: {sheet_name}")  # _全店：店铺渠道, 经营优势来源渠道; _流量载体：无线流量来源, 经营优势来源渠道
                if df.empty:
                    pass
                else:
                    items_tmp = df.to_dict('records')
                    items_dict[sheet_name] = items_tmp

            return items_dict
        except Exception as e:
            # logger.error(f"{res.text}")
            return None
    def goods_from__listen_good_flow_day(self,item_id,days=-1):
        api = "https://sycm.taobao.com/flow/excel.do?"
        params = {
            "_path_": "v6/excel/item/crowdtype/source/v3",
            "belong": "all",
            "dateType": "day",
            "dateRange": f"{get_date(days)}|{get_date(days)}",
            "crowdType": "all",
            "device": "2",
            "itemId": item_id,
            "order": "desc",
            "orderBy": "uv",

        }
        url = api + urlencode(params)
        # print(url)
        res = requests.get(url, headers={
            "User-Agent": UA,
            "cookie": self.cookie})
        self.req_log(res)
        try:
            data = io.BytesIO(res.content)
            df = pd.read_excel(data,skiprows=5)
            if df.empty:
                return {}
            else:
                items = df.to_dict('records')
                return items
        except Exception as e:
            # logger.error(f"{res.text}")
            return None

    def goods_from__listen_good_flow_day_new(self,item_id,days=-1):
        api = "https://sycm.taobao.com/flow/excel.do?"
        params = {
            "_path_": "qzt/item/crowdtype/source/download",
            "dateType": "day",
            "dateRange": f"{get_date(days)}|{get_date(days)}",
            "crowdType": "all",
            "itemId": item_id,
            "order": "desc",
            "orderBy": "uv",
            "flowBizType":"classic"

        }
        url = api + urlencode(params)
        # print(url)
        res = requests.get(url, headers={
            "User-Agent": UA,
            "cookie": self.cookie})
        self.req_log(res)
        try:
            data = io.BytesIO(res.content)
            data.seek(0)
            df = pd.read_excel(data,sheet_name="无线流量来源", skiprows=5)
            if df.empty:
                return None,None
            else:
                items = df.to_dict('records')
                try:
                    data.seek(0)
                    df2=pd.read_excel(data,sheet_name="经营优势来源渠道", skiprows=5)
                    print(df2.to_dict('records'))
                    df2 = df2.rename(columns={'渠道名称': '三级来源'})
                    df2["一级来源"]="经营优势"
                    df2["二级来源"] = "经营优势"
                    items2=df2.to_dict('records')
                    # items.extend(items2)
                    return items,items2
                except:
                    return items,None

        except Exception as e:
            # logger.error(f"{res.text}")
            return None,None

#  """https://sycm.taobao.com/flow/gray/excel.do?_path_=v4/excel/shop/source/summay/v4
#  &dateType=day
#  &dateRange=2025-04-11|2025-04-11
#  &crowdType=all
#  &needCate=undefined"""
#
#
# Flow("thw=cn; wk_cookie2=1b76aa0113fd20e5edc5b5c1c9ae2156; wk_unb=UoH%2B4NPsNoWZlw%3D%3D; useNativeIM=false; xlly_s=1; t=218d274ebf8ab40b00a3a454d226715e; cookie2=1076d1d87978137db0e21e0dc538b143; _tb_token_=fe73773ee3584; _samesite_flag_=true; 3PcFlag=1744445720498; sgcookie=E100MYQUh5eO760V5pAbyciO7Rim8uJFmPnLpS81Oj6ycZe67T7domXP0NNYih5NpRcPisDias%2BB3M4ByI4M6GKTWSzMNR6LWFvDvKP9CqAZ8ka%2FTGbPrC2xcAmpNj3lLiSp; unb=2212373938588; sn=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; uc1=cookie21=U%2BGCWk%2F7oPIg&cookie14=UoYaj4zhXvYLVg%3D%3D; csg=fa6cb78b; _cc_=URm48syIZQ%3D%3D; cancelledSubSites=empty; skt=53358bd45c948dfa; _euacm_ac_l_uid_=2212373938588; 2212373938588_euacm_ac_c_uid_=2212375622312; 2212373938588_euacm_ac_rs_uid_=2212375622312; _portal_version_=new; cc_gray=1; XSRF-TOKEN=38bef1e9-ee67-4f66-a3da-bbfc07586974; mtop_partitioned_detect=1; _m_h5_tk=a29946d09806cae53627b7b545d8a6ea_1744454724125; _m_h5_tk_enc=0fedad765e74e21a98f7e51e6bdfc1b9; _euacm_ac_rs_sid_=551723820; JSESSIONID=2CBC9CC982A550662A539A0EE87ED583; tfstk=g0An73bTaGZjNgiOBC1InM23lIk9v61573FR2_IrQGS_9ynBJdby2hgSR6LPq3xOfLCR9WKMZh-9J7CdehjyAhs896QdUgxAfBIpyMQPUEK7weCpyy96DEPp9v18Z615amnxMjUBR_1rgTA3Ly1NPZ2EwTWz76_8_AOyBjLBRPz34qpZMumFqU6F43WFbF7AbkSzL3Wa_asaTaPFzGuGfG7z8JyE_57Rzgze4_uM7G_Paw-PLVYZ_voOvMSW_c_Pr0hDqYR1-9j28M8pJClOLJTOj7PysdX10jIga7RG-Fe9KZVEiGJpUBCwTcrR_E99YNfmZzbMnF5F-3GbO6827LWHZYUfVdYwHOv_J2_MtEAloOkz2gBD_BCBImVA0dTyZO8Im-_9UEdpEHn_aMpD7hXv6lFA_BxHTOfV4Nwa3cMYNNuJ_8w5LN_GDnSmQrHCNzRmSV2V-971853iS8GhLN_GDV0g3_6F5wPO.").shop_from__flow_from_build_day()