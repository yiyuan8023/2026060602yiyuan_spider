# File: pdd_数据中心_服务数据_售后数据


from API.API_Pdd.API_Pdd_Centre import PddDataCentre
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager
from extra.extra_date import get_date_min_max
from extra.logger_ import logger

# noqa: E501
dict_str = {
    "payOrdrAmt": "成交金额",
    # "payOrdrAmt1dPln": 139298.56,
    # "payOrdrAmt1dOst": 720698.58,
    "payOrdrCnt": "成交订单数",
    # "payOrdrCnt1dPln": 1785,
    # "payOrdrCnt1dOst": 29852,
    "payUvRto": "成交转化率",
    # "payUvRto1dPln": 94.75,
    # "payUvRto1dOst": 409.82854999999984,
    "gpv": "商品浏览量",
    # "gpv1dPln": 25018,
    # "gpv1dOst": 37618,
    "guv": "商品访客数",
    # "guv1dPln": 14182,
    # "guv1dOst": 25153,
    "vstGoodsCnt": "被访问商品数",
    # "vstGoodsCnt1dPln": 80,
    # "vstGoodsCnt1dOst": 194,
    "payOrdrUsrCnt": "成交买家数",
    # "payOrdrUsrCnt1dPln": 1364,
    # "payOrdrUsrCnt1dOst": 29781,
    # "cfmOrdrUsrCnt": 26,
    # "cfmOrdrUsrCnt1dPln": 1364,
    # "cfmOrdrUsrCnt1dOst": 29563,
    # "cfmOrdrCnt": 31,
    # "cfmOrdrCnt1dPln": 1713,
    # "cfmOrdrCnt1dOst": 29852,
    "goodsFavCnt": "商品收藏用户数",
    # "goodsFavCnt1dOst": 2788,
    # "goodsFavCnt1dPln": 2031,
    "statDate": "统计日期",
}

if __name__ == "__main__":
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ["林内官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "pdd_数据中心_商品数据_商品概况"
    site = "拼多多"
    shop_cookies, crawl_day_list = select_shop_date(
        table_name, site, shop_name_list, 30
    )
    min_time, max_time = get_date_min_max(crawl_day_list)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]

        Obj = PddDataCentre(cookie)
        res, A = Obj.goods_data__goods_general_situation(min_time, max_time)
        results = res.get("result", [])
        items = []
        for result in results:
            item = {}
            for k, v in dict_str.items():
                item[v] = result.get(k, "")

            item.update(
                {
                    "店铺名称": shop_name,
                }
            )
            item["key"] = f"{item['店铺名称']}_{item['统计日期']}"
            items.append(item)
        print(items)

        DBManager(db_config=db_config).update_insert_data(
            items, table_name, primary_key="key"
        )
        logger.info(f"{shop_name}_{min_time}-{max_time}数据已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
