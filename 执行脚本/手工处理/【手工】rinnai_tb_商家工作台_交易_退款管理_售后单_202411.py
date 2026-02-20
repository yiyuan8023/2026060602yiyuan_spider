from excel.excel_to_db import FileToItems
from extra.db_manager import DBManager
from extra.logger_ import logger

if __name__ == '__main__':

    logger.info(f"\n{'*' * 120}")

    table_name = 'rinnai_tb_商家工作台_交易_退款管理_售后单_202601'  # noqa

    shops = [ # noqa
        {"db_config": 'rinnai', "shop_name": "林内官方旗舰店", "file_path": r"E:\1\1087143051_1770684525334_443.xlsx"}, # noqa
        # {"db_config": 'rinnai', "shop_name": "林内热水器旗舰店", "file_path": r"E:\1\2208107135654_1769733326322_927.xlsx"}, # noqa
        # {"db_config": 'rinnai', "shop_name": "林内厨电旗舰店", "file_path": r"E:\1\2212375622312_1769734184426_284.xlsx"}, # noqa
        # {"db_config": 'rinnai', "shop_name": "林内品牌折扣店", "file_path": r"E:\1\3830928885_1769734300644_518.xlsx"}, # noqa
        # {"db_config": 'rinnai', "shop_name": "智慧家电直销店", "file_path": r"E:\1\2218523687752_1769734335224_533.xlsx"}, # noqa
    ]

    for shop in shops:
        file_path_ = shop['file_path']
        shop_name = shop['shop_name']
        db_config = shop['db_config']

        # 创建实例
        items_ = FileToItems(file_path_, ).read_file()

        for item in items_:
            item.update({
                "店铺名称": shop_name,
            })

        # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
        # print(items)

        DBManager(db_config=db_config).update_insert_data(items_, table_name, primary_key='退款编号')
        # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
