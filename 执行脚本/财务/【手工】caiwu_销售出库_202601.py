from excel_tool.excel_to_db import FileToItems
from database import DBManager
from extra.logger_ import logger
from extra.extra_file import list_file_path

if __name__ == "__main__":
    # 林内优品赠品的发放，需要剔除样机后，再统计
    # 手动统计
    db_config = "rinnai_py"  # noqa
    logger.info(f"\n{'*' * 120}")

    table_name = "caiwu_销售出库_202601"  # noqa
    shop_name = "林内优品"
    list_file_path = list_file_path(
        r"C:\Users\admin\Desktop\财务20260119\销售出库",
        file_pattern="202*",
        file_extension="xlsx",
    )
    # list_file_path = [r'E:\1\端到端结算订单补差导出 (2).xlsx']
    # print(list_file_path)
    for file_path in list_file_path:
        print(file_path)
        # 创建实例
        items_ = FileToItems(
            file_path,
        ).read_file()
        # print(items_)
        filtered_items = []
        for item in items_:
            if item.get("日期") != "合计":
                item.update(
                    {
                        "文件名称": file_path,
                    }
                )
                filtered_items.append(item)
        #     # item["key"] = f"{item['日期']}_{item['门店ID']}_{item['商品ID']}"
        # print(items)

        DBManager(db_config=db_config).update_insert_data(filtered_items, table_name)
        # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
