from excel.excel_to_db import FileToItems
from extra.db_manager import DBManager
from extra.logger_ import logger

if __name__ == "__main__":
    db_config = "rinnai"  # noqa
    # db_config = None
    password = "b93899"
    logger.info(f"\n{'*' * 120}")
    file_path_ = r"E:\1\快手小店批量导出-2026-01-26+13_44.xlsx"  # NOQA
    table_name = "rinnai_ks_快手小店_订单查询_订单列表_202501"  # noqa
    shop_name = "林内官方旗舰店"

    # 创建实例
    items_ = FileToItems(file_path_, password=password).read_file()
    # print(items_)

    for item in items_:
        # print(item)
        item.update(
            {
                "店铺名称": shop_name,
                # "计划类型": "全部推广类型"
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
