from excel_tool.excel_to_db import FileToItems
from database import DBManager
from extra.logger_ import logger

if __name__ == "__main__":

    logger.info(f"\n{'*' * 120}")

    # table_name = 'rinnai_tb_商家工作台_交易_退款管理_售后单_202601'  # noqa

    shops = [  # noqa
        {
            "db_config": "rinnai",
            "table_name": "rinnai_606优品买赠_通用买赠&加赠",
            "file_path": r"C:\Users\admin\Desktop\林内优品模型.xlsx",
            "sheet_name": "通用买赠&加赠",
        },  # noqa
        {
            "db_config": "rinnai",
            "table_name": "rinnai_606优品买赠_阶梯买赠",
            "file_path": r"C:\Users\admin\Desktop\林内优品模型.xlsx",
            "sheet_name": "阶梯买赠",
        },  # noqa
        {
            "db_config": "rinnai",
            "table_name": "rinnai_606优品买赠_满额买赠",
            "file_path": r"C:\Users\admin\Desktop\林内优品模型.xlsx",
            "sheet_name": "满额买赠",
        },  # noqa
    ]

    for shop in shops:
        file_path_ = shop.get("file_path")
        shop_name = shop.get("shop_name")
        db_config = shop.get("db_config")
        table_name = shop.get("table_name")
        sheet_name = shop.get("sheet_name")
        file_name = file_path_.split("\\")[-1]

        # 创建实例
        items_ = FileToItems(file_path_, sheet_name=sheet_name).read_file()

        for item in items_:
            item.update(
                {
                    "file_name": file_name,
                }
            )

        # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
        # print(items)

        DBManager(db_config=db_config).update_insert_data(items_, table_name)
        # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
