from excel_tool.excel_to_db import FileToItems
from database import DBManager
from extra.logger_ import logger

if __name__ == "__main__":

    logger.info(f"\n{'*' * 120}")

    table_name = "rinnai_tb_商家工作台_交易_已卖出宝贝_宝贝报表明细_202411"  # noqa

    shops = [
        {
        "db_config": 'rinnai',  # noqa
        "shop_name": "林内官方旗舰店",
        "file_path": r"E:\1\ExportOrderList26334396597.xlsx"
         }, # noqa

        # {"db_config": 'rinnai', "shop_name": "林内热水器旗舰店", "file_path": r"E:\1\ExportOrderList25954471453.xlsx"}, # noqa
        #     {
        #         "db_config": "rinnai",  # noqa
        #         "shop_name": "林内厨电旗舰店",
        #         "file_path": r"E:\1\ExportOrderList25954993239.xlsx",
        #     },  # noqa
        #     {
        #         "db_config": "rinnai",  # noqa
        #         "shop_name": "林内品牌折扣店",
        #         "file_path": r"E:\1\ExportOrderList25955497160.xlsx",
        #     },  # noqa
        #     {
        #         "db_config": "rinnai",  # noqa
        #         "shop_name": "智慧家电直销店",
        #         "file_path": r"E:\1\ExportOrderList25954921258.xlsx",
        #     },  # noqa
        ]

    for shop in shops:
        file_path_ = shop["file_path"]
        shop_name = shop["shop_name"]
        db_config = shop["db_config"]

        # 创建实例
        items_ = FileToItems(
            file_path_,
        ).read_file()

        for item in items_:
            item.update(
                {
                    "店铺名称": shop_name,
                }
            )

        # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
        # print(items)

        DBManager(db_config=db_config).update_insert_data(
            items_, table_name, primary_key="子订单编号"
        )
        # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
        logger.info("-" * 100)
        logger.info(f"\n{'*' * 120}")
