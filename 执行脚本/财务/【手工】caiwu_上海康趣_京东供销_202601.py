from excel.excel_to_db import FileToItems
from database import DBManager
from extra.logger_ import logger
from extra.extra_file import list_file_path

if __name__ == "__main__":
    # 林内优品赠品的发放，需要剔除样机后，再统计
    # 手动统计
    db_config = "caiwu_hzbc"  # noqa
    logger.info(f"\n{'*' * 120}")

    table_name = "caiwu_上海康趣_京东供销_202601"  # noqa

    # list_file_path = list_file_path(r"C:\Users\admin\Desktop\财务20260119\核对数据", file_pattern="2*", file_extension="xlsx")
    list_file_path = [
        r"C:\Users\admin\Desktop\20-25年品牌采购数据\京东供销_美的上海旗舰店_2023-2025.xlsx"
    ]
    # print(list_file_path)
    for file_path in list_file_path:
        print(file_path)
        # 创建实例
        items_ = FileToItems(
            file_path,
        ).read_file()
        # print(items_)

        for item in items_:
            # print(item)
            item.update(
                {
                    "文件名称": file_path,
                }
            )

        #     # item["key"] = f"{item['日期']}_{item['门店ID']}_{item['商品ID']}"
        # print(items)
        delete_sql = f"delete from {table_name} where `文件名称`='{file_path}'"  # NOQA
        db = DBManager(db_config=db_config)
        db.update_insert_data(items_[:2], table_name)
        # db.update_insert_data(items_, table_name)
        db.execute_sql(delete_sql)
        db.update_insert_data(items_, table_name)
        # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
