from excel_tool.excel_to_db import FileToItems
from database import DBManager
from extra.logger_ import logger

if __name__ == "__main__":
    # 林内优品赠品的发放，需要剔除样机后，再统计
    db_config = "rinnai"  # noqa
    logger.info(f"\n{'*' * 120}")
    file_path_ = r"E:\1\FY23优品样机拍样&核销_拍样明细数据：_1767766881560.xlsx"  # NOQA
    table_name = "hjy_黄金眼_零售运营_样机数据_排样明细数据_202601"  # noqa
    shop_name = "林内优品"

    # 创建实例
    items_ = FileToItems(
        file_path_,
    ).read_file()
    # print(items_)

    for item in items_:
        # print(item)
        item.update({"店铺名称": shop_name, "来源": "黄金眼"})
        item["key"] = f"{item['日期']}_{item['门店ID']}_{item['商品ID']}"
    # print(items)

    DBManager(db_config=db_config).update_insert_data(
        items_, table_name, primary_key="key"
    )
    # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
