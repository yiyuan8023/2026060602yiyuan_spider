from excel.excel_to_db import FileToItems
from extra.db_manager import DBManager
from extra.logger_ import logger
from extra.extra_file import list_file_path

if __name__ == '__main__':
    # 林内优品赠品的发放，需要剔除样机后，再统计
    db_config = 'rinnai'  # noqa
    logger.info(f"\n{'*' * 120}")

    table_name = 'tb_天猫优品_返利管理_价保补差_202601'  # noqa
    shop_name = '林内优品'
    # list_file_path = list_file_path(r"C:\Users\admin\Desktop\bb", file_pattern="S202*", file_extension="xlsx")
    list_file_path = [r'C:\Users\admin\Desktop\价保补差.xlsx']

    # print(list_file_path)
    for file_path in list_file_path:
        print(file_path)
        # 创建实例
        items_ = FileToItems(file_path, ).read_file()
        # print(items_)

        # for item in items_:
        #     item.update({
        #         "店铺名称": shop_name,
        #         # "来源": "黄金眼"
        #     })
        #     # item["key"] = f"{item['日期']}_{item['门店ID']}_{item['商品ID']}"


        DBManager(db_config=db_config).update_insert_date(items_, table_name, primary_key='计费流水号')
        # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
