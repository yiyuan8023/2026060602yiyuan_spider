from excel.excel_to_db import FileToItems
from extra.db_manager import DBManager
from extra.logger_ import logger

if __name__ == '__main__':
    db_config = 'bc'  # noqa
    # db_config = None
    # password = 'b632b4'
    logger.info(f"\n{'*' * 120}")
    file_path_ = r'E:\1\7551232835630432554_58jvKe3Sv4_1758158709\1758158683_28ffddd0b60016349a1e353a15039666SpFNBUDN.csv'  # NOQA
    table_name = 'dy_抖店_订单_订单管理_自定义报表_订单维度_202505'  # noqa
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

    DBManager(db_config=db_config).update_insert_date(items_, table_name, primary_key='子订单编号')
    # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
