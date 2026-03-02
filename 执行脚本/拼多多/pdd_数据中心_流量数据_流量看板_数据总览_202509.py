# File: pdd_数据中心_服务数据_售后数据


from API.API_Pdd.API_Pdd_Centre import PddDataCentre
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager
from extra.logger_ import logger

# noqa: E501
dict_str = {
    "cfmOrdrUsrCnt": "成交买家数",
    "cfmOrdrCnt": "成交订单数",
    "cfmOrdrAmt": "成交金额",
    "cfmOrdrAup": "客单价",
    "uv": "店铺访客数",
    "pv": "店铺浏览量",
    "guv": "商品访客数",
    "gpv": "商品浏览量",
    "cfmUvRto": "成交转化率",
    "uvCfmVal": "成交UV价值",
}

if __name__ == "__main__":
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ["林内官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "pdd_数据中心_流量数据_流量看板_数据总览_202509"
    site = "拼多多"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 3)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        items = []
        Obj = PddDataCentre(cookie)
        for date in crawl_day_list:
            res = Obj.pdd_flow_data__flow_board(date, date)
            # print(res)
            item = {}
            for k, v in dict_str.items():
                item[v] = res.get("result", {}).get(k, "")
            item.update(
                {
                    "店铺名称": shop_name,
                    "统计日期": date,
                }
            )
            item["key"] = f"{item['店铺名称']}_{item['统计日期']}"

        items.append(item)

        DBManager(db_config=db_config).update_insert_data(
            items, table_name, primary_key="key"
        )
        logger.info(f"{shop_name}_{crawl_day_list}数据已入库")
        logger.info("-" * 100)
logger.info(f"\n{'*' * 120}")
