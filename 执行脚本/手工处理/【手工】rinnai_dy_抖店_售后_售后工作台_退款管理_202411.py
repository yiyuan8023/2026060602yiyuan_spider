from excel.excel_to_db import FileToItems
from extra.database_manager import DatabaseManager
from extra.logger_ import logger

if __name__ == '__main__':
    db_config = 'rinnai'  # noqa
    # db_config = None
    # password = 'b632b4'
    logger.info(f"\n{'*' * 120}")
    file_path_ = r'E:\1\售后单-2025-09-18 09_21_34.xlsx'  # NOQA
    table_name = 'rinnai_dy_抖店_售后_售后工作台_退款管理_202411'  # noqa
    shop_name = '林内热水器旗舰店'
    # shop_name = '林内智能家居旗舰店'

    # 创建实例
    items_ = FileToItems(file_path_, ).read_file()
    # print(items_)

    for item in items_:
        # print(item)
        item.update({
            "店铺名称": shop_name,
            # "计划类型": "全部推广类型"
        })
        # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
    # print(items)

    DatabaseManager(db_config=db_config).upsert_data(items_, table_name, primary_key='售后单号')
    # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
