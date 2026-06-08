import os

from excel_tool.excel_to_db import FileToItems
from database import DBManager
from extra.logger_ import logger
from extra.extra_file import list_file_path

if __name__ == "__main__":
    # 林内优品赠品的发放，需要剔除样机后，再统计
    # 手动统计
    db_config = "caiwu_hzbc"  # noqa
    logger.info(f"\n{'*' * 120}")

    table_name = "caiwu_上海康趣_美云销_202601"  # noqa

    list_file_path = list_file_path(
        r"C:\Users\admin\Desktop\20260127上海康趣财务数据整合\20-25年品牌采购数据\20260130新增",
        file_extension="xlsx",
    )
    # list_file_path = [r'C:\Users\admin\Desktop\20-25年品牌采购数据\美云销\2025年10-12月美云销.xlsx']
    # list_file_path = [r'C:\Users\admin\Desktop\20-25年品牌采购数据\美云销\测试.xlsx']
    # print(list_file_path)
    for file_path in list_file_path:
        logger.info(file_path)
        file_name = os.path.basename(file_path)
        # print(file_path)
        # 创建实例
        items_ = FileToItems(
            file_path,
        ).read_file()
        # print(items_)
        logger.info(f"{file_path}开始入库")
        for item in items_:
            # print(item)
            item.update(
                {
                    "文件名称": file_name,
                }
            )

        #     # item["key"] = f"{item['日期']}_{item['门店ID']}_{item['商品ID']}"
        # print(items)
        delete_sql = f"delete from {table_name} where `文件名称`='{file_name}'"  # NOQA
        db = DBManager(db_config=db_config)
        db.insert_delete_insert_data(items_, table_name, delete_sql)
        # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
