from API.API_TaoXi_SYCM.ShengCanBase import ShengCanBaseApi
from extra.logger_ import logger
from extra.downloader.core import Downloader
from extra.excel_reader import excel_engine, read_excel_dataframe


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
            "belong": "all",
        }

        try:
            items = Downloader(api, cookie=self.cookie, params=params).download_excel(
                skiprows=5
            )
            return items
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
            "needCate": "undefined",
        }
        try:
            data = Downloader(
                api, cookie=self.cookie, params=params
            ).download_file_to_byte()
            all_sheets = read_excel_dataframe(
                data, sheet_name=None, skiprows=5
            )  # 读取所有的工作表
            items_dict = {}
            for sheet_name, df in all_sheets.items():
                if not df.empty:
                    items_dict[sheet_name] = df.to_dict("records")
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
            items = Downloader(api, cookie=self.cookie, params=params).download_excel(
                skiprows=5
            )
            return items
        except Exception as e:
            logger.error(
                f"获取商品流量数据失败: item_id={item_id}, day={day}, error={str(e)}"
            )
            return None

    def goods_from__listen_good_flow_day_new(self, item_id, day):
        # tb_sycm_流量_商品来源_商品来源流量_新版_202504 # NOQA

        api = "https://sycm.taobao.com/flow/excel.do?"
        params = {
            "_path_": "qzt/item/crowdtype/source/download",  # NOQA
            "dateType": "day",
            "dateRange": f"{day}|{day}",
            "crowdType": "all",
            "itemId": item_id,
            "order": "desc",
            "orderBy": "uv",
            "flowBizType": "classic",
        }

        try:
            data = Downloader(
                api, cookie=self.cookie, params=params
            ).download_file_to_byte()
            engine = excel_engine(data)
            data.seek(0)

            df = read_excel_dataframe(
                data, sheet_name="无线流量来源", skiprows=5, engine=engine
            )
            if df is None or df.empty:
                return None, None
            items = df.to_dict("records")

            try:
                data.seek(0)
                df2 = read_excel_dataframe(
                    data, sheet_name="经营优势来源渠道", skiprows=5, engine=engine
                )

                if df2 is not None:
                    df2 = df2.rename(columns={"渠道名称": "三级来源"})
                    df2["一级来源"] = "经营优势"
                    df2["二级来源"] = "经营优势"
                    items2 = df2.to_dict("records")
                    return items, items2
                else:
                    return items, None
            except Exception as e:
                logger.warning(
                    f"读取经营优势来源渠道工作表失败: item_id={item_id}, day={day}, error={str(e)}"
                )
                return items, None
        except Exception as e:
            logger.error(
                f"获取sheet1新版商品流量数据失败 - item_id: {item_id}, day: {day}, error: {str(e)}"
            )
            return None, None
