from excel_tool.excel_to_db import FileToItems
from database import DBManager
from extra.logger_ import logger

if __name__ == "__main__":
    db_config = "rinnai"  # noqa
    # db_config = None

    logger.info(f"\n{'*' * 120}")

    # file_path_ = r'E:\1\854orders_export2025-12-12-09-16-06.csv'  # NOQA
    file_path_ = r"E:\1\d92bcb6e9b59aad05f06a9246f20a62aorders_export2026-05-29-08-38-33.csv"  # NOQA
    table_name = "rinnai_pdd_订单查询_订单明细_202411"  # noqa
    # shop_name = '林内官方旗舰店'
    shop_name = "林内八八专卖店"

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
        items_, table_name, primary_key="订单号"
    )
    # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
