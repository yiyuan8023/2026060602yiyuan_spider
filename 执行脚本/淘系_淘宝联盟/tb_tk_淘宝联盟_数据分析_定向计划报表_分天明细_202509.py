# File: 淘宝联盟_商品分析
from API.API_TaoKe.API_Taoke_DingXiang import TaoKeDingXiangApi
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager

from extra.extra_date import get_date_min_max

from extra.logger_ import logger

if __name__ == "__main__":
    db_config = "rinnai_py"  # noqa
    shop_name_list = [
        "林内热水器旗舰店",
        "林内官方旗舰店",
    ]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_tk_淘宝联盟_数据分析_定向计划报表_分天明细_202509"
    site = "淘宝联盟"
    shop_cookies, crawl_day_list = select_shop_date(
        table_name, site, shop_name_list, 30
    )
    min_time, max_time = get_date_min_max(crawl_day_list)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        Obj = TaoKeDingXiangApi(cookie)
        logger.info(f"正常采集第【{shop_name}】数据")
        items = Obj.get_campaign(min_time, max_time)

        # print(items)
        for item in items:
            item.update(
                {
                    "店铺名称": shop_name,
                }
            )
            item["key"] = f"{item['店铺名称']}_{item['任务id']}_{item['统计日期']}"
        # print(items)

        DBManager(db_config=db_config).update_insert_data(
            items, table_name, primary_key="key"
        )

        logger.info(f"{shop_name},{crawl_day_list}已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_tk_淘宝联盟_商品分析_202504.py --start-date=2025-03-27 --end-date=2025-04-18
