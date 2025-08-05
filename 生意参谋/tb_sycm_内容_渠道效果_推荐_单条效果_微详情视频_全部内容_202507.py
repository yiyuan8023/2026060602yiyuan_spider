

from ShengCanApi.goods import Goods
from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager
from extra.logger_ import logger

if __name__ == '__main__':

    shop_name_list = ['林内官方旗舰店', '林内厨电旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺

    db_table_name = 'tb_sycm_内容_渠道效果_推荐_单条效果_微详情视频_全部内容_202507'  # noqa

    site = '生意参谋'
    shop_cookies, crawl_day_list = data_collector(db_table_name, site, shop_name_list, 1)

    for i in shop_cookies:

        cookie = i[1]
        shop_name = i[0]
        GoodObj = Goods(cookie)
        for day in crawl_day_list:
            start_date_ = end_data_ = day
            logger.info(f"正在采集{shop_name}，{day}的数据")

            items = GoodObj.recommend_analysis_single_excel(day)
            if items:
                for item in items:
                    item.update({
                        "店铺名称": shop_name,
                        "日期类型": "day",
                        "统计日期": start_date_,
                    })
                    item["key"] = f"{item['店铺名称']}_{item['统计日期']}_{item['日期类型']}_{item['视频id']}"
                DatabaseManager().upsert_data(items, db_table_name, primary_key="key")

# python tb_sycm_内容_渠道效果_推荐_单条效果_微详情视频_全部内容_202507.py --start-date=2025-04-17 --end-date=2025-07-16 # noqa
