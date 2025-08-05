
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
        # tb_sycm_流量_店铺来源_流量来源构成_整体_无线端_202504  # NOQA

        api = "https://sycm.taobao.com/flow/gray/excel.do?"
        params = {
            "_path_": "v4/excel/shop/source/v3",
            "device": 2,
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "belong": "all"
        }

        try:
            data = Downloader(api, self.cookie, params).download_excel()
            df = pd.read_excel(data, skiprows=5)
            if df.empty:
                return {}
            else:
                return df.to_dict('records')
        except Exception as e:
            logger.error(f"店铺来源_流量来源构成: day={day}, error={str(e)}")
            return None

    def shop_from__flow_from_build__shop_flow_day(self, day):
        # 'tb_sycm_流量_店铺来源_流量来源构成_全店来源_新版' # NOQA

        api = "https://sycm.taobao.com/flow/gray/excel.do?"
        params = {
            "_path_": "v4/excel/shop/source/summay/v4",  # NOQA
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "crowdType": "all",
            "needCate": "undefined"
        }
        try:
            data = Downloader(api, self.cookie, params).download_excel()
            all_sheets = pd.read_excel(data, sheet_name=None, skiprows=5)
            items_dict = {}
            for sheet_name, df in all_sheets.items():
                if not df.empty:
                    items_dict[sheet_name] = df.to_dict('records')
            return items_dict
        except Exception as e:
            logger.error(f"获取店铺来源流量数据失败: day={day}, error={str(e)}")
            return []

    def goods_from__listen_good_flow_day(self, item_id, day):
        #  tb_sycm_流量_商品来源_商品来源流量_旧版_202504  # NOQA

        api = "https://sycm.taobao.com/flow/excel.do?"
        params = {
            "_path_": "v6/excel/item/crowdtype/source/v3",  # NOQA
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
            data = Downloader(api, self.cookie, params).download_excel()
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

    def goods_from__listen_good_flow_day_new(self, item_id, day):
        # tb_sycm_流量_商品来源_商品来源流量_新版_202504 # NOQA

        api = "https://sycm.taobao.com/flow/excel.do?"
        params = {
            "_path_": "qzt/item/crowdtype/source/download", # NOQA
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "crowdType": "all",
            "itemId": item_id,
            "order": "desc",
            "orderBy": "uv",
            "flowBizType": "classic"
        }

        try:
            data = Downloader(api, self.cookie, params).download_excel()
            engine = excel_engine(data)
            data.seek(0)

            df = pd.read_excel(data, sheet_name="无线流量来源", skiprows=5, engine=engine)
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
