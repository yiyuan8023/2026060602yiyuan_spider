from excel.excel_to_db import FileToItems
from extra.db_manager import DBManager
from extra.logger_ import logger

if __name__ == '__main__':
    db_config = 'rinnai'  # noqa
    # db_config = None

    logger.info(f"\n{'*' * 120}")

    file_path_ = r'E:\1\854orders_export2025-12-12-09-16-06.csv'  # NOQA
    file_path_ = r'E:\1\956145070orders_export2025-12-24-08-52-17.csv'  # NOQA
    table_name = 'rinnai_pdd_订单查询_订单明细_202411'  # noqa
    # shop_name = '林内官方旗舰店'
    shop_name = '八八电器专营店'


    # 创建实例
    items_ = FileToItems(file_path_, ).read_file()

    for item in items_:
        item.update({
            "店铺名称": shop_name,

        })
        # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
    # print(items)

    DBManager(db_config=db_config).update_insert_date(items_, table_name, primary_key='订单号')
    # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
