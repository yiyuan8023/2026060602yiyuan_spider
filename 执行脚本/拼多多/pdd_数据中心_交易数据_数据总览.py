# File: pdd_数据中心_服务数据_售后数据


from API.API_Pdd.API_Pdd_Centre import PddDataCentre
from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.extra_date import get_date_min_max
from extra.logger_ import logger

# noqa: E501
dict_str = {
    "stateDate": "统计日期",
    # "hr": null,
    "payOrdrAmt": "成交金额",
    "payOrdrCnt": "成交订单数",
    "payOrdrUsrCnt": "成交买家数",
    "payOrdrAup": "客单价",
    "payUvRto": "成交转化率",
    "rpayUsrRtoDth": "成交老买家占比",  # NOQA
    "mallFavCnt": "店铺关注用户数",
    "sucRfOrdrAmt1d": "退款金额",
    "sucRfOrdrCnt1d": "退款单数",
    "uvCfmVal": "平均访客价值",
    # "payOrdrAmt1dPln": 104921.13,
    # "payOrdrAmt1dOst": 793105.28,
    # "payOrdrCnt1dPln": 2020,
    # "payOrdrCnt1dOst": 15608,
    # "payOrdrUsrCnt1dPln": 1126,
    # "payOrdrUsrCnt1dOst": 15501,
    # "payOrdrAup1dPln": 116697.74277999994,
    # "payOrdrAup1dOst": 280423.1583,
    # "payUvRto1dPln": 112.38567999999997,
    # "payUvRto1dOst": 261.2926600000001,
    # "rpayOrdrUsrRto1dPln": 0.47957999999999995,
    # "rpayOrdrUsrRto1dOst": 0.7896200000000001,
    # "mallFavCnt1dOst": 18,
    # "mallFavCnt1dPln": 18
}

if __name__ == "__main__":
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ["林内官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "pdd_数据中心_交易数据_数据总览"
    site = "拼多多"
    shop_cookies, crawl_day_list = select_shop_date(
        table_name, site, shop_name_list, 30
    )
    min_time, max_time = get_date_min_max(crawl_day_list)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]

        Obj = PddDataCentre(cookie)
        res, A = Obj.pdd_trade_data__data_overview(min_time, max_time)
        results = res.get("result", {}).get("dayList", [])
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
