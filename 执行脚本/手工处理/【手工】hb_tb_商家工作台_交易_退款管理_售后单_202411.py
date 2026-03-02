from excel.excel_to_db import FileToItems
from extra.db_manager import DBManager
from extra.logger_ import logger

if __name__ == "__main__":
    db_config = "hb"  # noqa
    # db_config = None

    logger.info(f"\n{'*' * 120}")
    file_path_ = r"E:\1\2026-01-13 (4).xls"  # NOQA
    table_name = "hb_tb_商家工作台_交易_退款管理_售后单_202411"  # noqa
    shop_name = "HollandBarrett保健品海外旗舰店"

    # 创建实例
    items_ = FileToItems(
        file_path_,
    ).read_file()

    for item in items_:
        item.update(
            {
                "店铺名称": shop_name,
                # "计划类型": "全部推广类型"
            }
        )
        # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
    # print(items)

    DBManager(db_config=db_config).update_insert_data(
        items_, table_name, primary_key="退款编号"
    )
    # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
