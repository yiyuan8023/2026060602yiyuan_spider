from API.API_YingDao import YingDaoApi
from excel.save_to_excel import SaveToExcel
from extra.db_manager import DBManager
from extra.logger_ import logger

if __name__ == '__main__':

    table_name = "影刀社区问答_202509"  # NOQA
    pages = range(1, 3)
    for i in pages:
        logger.info(f"正在采集影刀社区第【{i}】页的数据")
        items = YingDaoApi().get_yd_question()

        # item.update({
        #     "店铺名称": shop_name,
        #     "key": f"{shop_name}_{time_str}",
        #     "统计日期": time_str
        # })
        # print(item)
        DBManager().update_insert_date(items, table_name, primary_key='问题id')
        exporter = SaveToExcel(items, table_name)
        file_path = exporter.export_to_excel()
        logger.info("-" * 100)
        logger.info(f"影刀社区第【{i}】页的数据已入库")
    logger.info(f"\n{'*' * 120}")

    # python tb_sycm_首页_数据概览_图表_新版_202504.py --start-date=2025-03-27 --end-date=2025-04-18 # NOQA
