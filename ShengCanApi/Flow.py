from urllib.parse import urlencode

import pandas as pd

from ShengCanApi.ShengCanBase import ShengCanBaseApi
from extra.logger_ import logger
from extra.downloader import Downloader
from extra.extra_excel import excel_engine


class Flow(ShengCanBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def shop_from__flow_from_build_day(self, day):
        """
        tb_sycm_流量_店铺来源_流量来源构成_整体_无线端_202504
        """
        api = "https://sycm.taobao.com/flow/gray/excel.do?"
        params = {
            "_path_": "v4/excel/shop/source/v3",
            "device": 2,
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "belong": "all"
        }


        try:
            data = Downloader(self.cookie).download_excel(api, params)
            df = pd.read_excel(data, skiprows=5)
            if df.empty:
                return {}
            else:
                return df.to_dict('records')
        except Exception as e:
            return None

    def shop_from__flow_from_build__shop_flow_day(self,day):
        # 'tb_sycm_流量_店铺来源_流量来源构成_全店来源_新版'

        api = "https://sycm.taobao.com/flow/gray/excel.do?"
        params = {
            "_path_": "v4/excel/shop/source/summay/v4",
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "crowdType": "all",
            "needCate":"undefined"
        }
        try:
            data = Downloader(self.cookie).download_excel(api, params)
            all_sheets = pd.read_excel(data, sheet_name=None, skiprows=5)
            items_dict = {}
            for sheet_name, df in all_sheets.items():
                if not df.empty:
                    items_dict[sheet_name] = df.to_dict('records')
            return items_dict
        except Exception as e:
            logger.error(f"获取店铺来源流量数据失败: day={day}, error={str(e)}")
            return []

    def goods_from__listen_good_flow_day(self,item_id,day):
        """
        "tb_sycm_流量_商品来源_商品来源流量_旧版_202504"
        """
        api = "https://sycm.taobao.com/flow/excel.do?"
        params = {
            "_path_": "v6/excel/item/crowdtype/source/v3",
            "belong": "all",
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "crowdType": "all",
            "device": "2",
            "itemId": item_id,
            "order": "desc",
            "orderBy": "uv",
        }

        try:
            data = Downloader(self.cookie).download_excel(api, params)
            df = pd.read_excel(data, skiprows=5)

            # df.empty 是 pandas DataFrame 的属性
            # 用于检查 DataFrame 是否为空（没有任何行数据）
            # to_dict('records')，将 DataFrame 转换为字典格式
            if df.empty:
                return {}
            else:
                return df.to_dict('records')
        except Exception as e:
            logger.error(f"获取商品流量数据失败: item_id={item_id}, day={day}, error={str(e)}")
            return None

    def goods_from__listen_good_flow_day_new(self,item_id,day):
        """
        tb_sycm_流量_商品来源_商品来源流量_新版_202504
        """

        api = "https://sycm.taobao.com/flow/excel.do?"
        params = {
            "_path_": "qzt/item/crowdtype/source/download",
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "crowdType": "all",
            "itemId": item_id,
            "order": "desc",
            "orderBy": "uv",
            "flowBizType":"classic"
        }

        try:
            data = Downloader(self.cookie).download_excel(api, params)
            engine = excel_engine(data)
            data.seek(0)


            df = pd.read_excel (data, sheet_name="无线流量来源", skiprows=5, engine = engine)
            if df is None or df.empty:
                return None, None
            items = df.to_dict('records')

            try:
                data.seek(0)
                df2 = pd.read_excel(data, sheet_name="经营优势来源渠道", skiprows=5, engine=engine)

                if df2 is not None:
                    df2 = df2.rename(columns={'渠道名称': '三级来源'})
                    df2["一级来源"] = "经营优势"
                    df2["二级来源"] = "经营优势"
                    items2 = df2.to_dict('records')
                    return items, items2
                else:
                    return items, None
            except Exception as e:
                logger.warning(f"读取经营优势来源渠道工作表失败: item_id={item_id}, day={day}, error={str(e)}")
                return items, None
        except Exception as e:
            logger.error(f"获取sheet1新版商品流量数据失败 - item_id: {item_id}, day: {day}, error: {str(e)}")
            return None, None



#  """https://sycm.taobao.com/flow/gray/excel.do?_path_=v4/excel/shop/source/summay/v4
#  &dateType=day
#  &dateRange=2025-04-11|2025-04-11
#  &crowdType=all
#  &needCate=undefined"""
#
#
# Flow("thw=cn; wk_cookie2=1b76aa0113fd20e5edc5b5c1c9ae2156; wk_unb=UoH%2B4NPsNoWZlw%3D%3D; useNativeIM=false; xlly_s=1; t=218d274ebf8ab40b00a3a454d226715e; cookie2=1076d1d87978137db0e21e0dc538b143; _tb_token_=fe73773ee3584; _samesite_flag_=true; 3PcFlag=1744445720498; sgcookie=E100MYQUh5eO760V5pAbyciO7Rim8uJFmPnLpS81Oj6ycZe67T7domXP0NNYih5NpRcPisDias%2BB3M4ByI4M6GKTWSzMNR6LWFvDvKP9CqAZ8ka%2FTGbPrC2xcAmpNj3lLiSp; unb=2212373938588; sn=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; uc1=cookie21=U%2BGCWk%2F7oPIg&cookie14=UoYaj4zhXvYLVg%3D%3D; csg=fa6cb78b; _cc_=URm48syIZQ%3D%3D; cancelledSubSites=empty; skt=53358bd45c948dfa; _euacm_ac_l_uid_=2212373938588; 2212373938588_euacm_ac_c_uid_=2212375622312; 2212373938588_euacm_ac_rs_uid_=2212375622312; _portal_version_=new; cc_gray=1; XSRF-TOKEN=38bef1e9-ee67-4f66-a3da-bbfc07586974; mtop_partitioned_detect=1; _m_h5_tk=a29946d09806cae53627b7b545d8a6ea_1744454724125; _m_h5_tk_enc=0fedad765e74e21a98f7e51e6bdfc1b9; _euacm_ac_rs_sid_=551723820; JSESSIONID=2CBC9CC982A550662A539A0EE87ED583; tfstk=g0An73bTaGZjNgiOBC1InM23lIk9v61573FR2_IrQGS_9ynBJdby2hgSR6LPq3xOfLCR9WKMZh-9J7CdehjyAhs896QdUgxAfBIpyMQPUEK7weCpyy96DEPp9v18Z615amnxMjUBR_1rgTA3Ly1NPZ2EwTWz76_8_AOyBjLBRPz34qpZMumFqU6F43WFbF7AbkSzL3Wa_asaTaPFzGuGfG7z8JyE_57Rzgze4_uM7G_Paw-PLVYZ_voOvMSW_c_Pr0hDqYR1-9j28M8pJClOLJTOj7PysdX10jIga7RG-Fe9KZVEiGJpUBCwTcrR_E99YNfmZzbMnF5F-3GbO6827LWHZYUfVdYwHOv_J2_MtEAloOkz2gBD_BCBImVA0dTyZO8Im-_9UEdpEHn_aMpD7hXv6lFA_BxHTOfV4Nwa3cMYNNuJ_8w5LN_GDnSmQrHCNzRmSV2V-971853iS8GhLN_GDV0g3_6F5wPO.").shop_from__flow_from_build_day()


