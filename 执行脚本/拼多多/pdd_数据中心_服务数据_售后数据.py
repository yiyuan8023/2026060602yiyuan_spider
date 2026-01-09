# File: pdd_数据中心_服务数据_售后数据


from API.API_Pdd.API_Pdd_Centre import PddDataCentre
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager
from extra.logger_ import logger

# noqa: E501
dict_str = {
    "statDate": "统计日期",
    "dsptRfSucOrdrCnt1m": "纠纷退款数",  # noqa
    "stplDsptRfSucOrdrCnt1m": "类目均值",  # noqa
    "dsptRfSucRto1m": "纠纷退款率",  # noqa
    "stplDsptRfSucRto1m": "类目均值",  # noqa
    "pltInvlOrdrRto1m": "平台介入率",  # noqa
    "stplPltInvlOrdrRto1m": "类目均值",  # noqa
    "rfSucRto1m": "成功退款率",
    "stplRfSucRto1m": "类目均值",
    "avgSucRfProcTime1m": "平均退款时长",
    "passSsslAvgSucRfProcTime1m": "同行同层平均退款速度均值",  # noqa
    "bestSsslAvgSucRfProcTime1m": "同行同层平均退款速度优秀值",  # noqa
    "stplAvgSucRfProcTime1m": "类目均值",
    "qurfOrdRto1m": "品质退款率",  # noqa
    "stplQurfOrdRto1m": "类目均值",  # noqa
    "sucRfOrdrAmt1d": "成功退款金额",
    "sucRfOrdrCnt1d": "成功退款订单数",
    "pltInvlOrdrCnt1m": "介入订单数",  # noqa
    "avgSlfSucRfProcTime1mMgr": "退货退款自主完结时长",
    "avgSlfSucRfProcTime1mMr": "仅退款自主完结时长"
}

if __name__ == '__main__':
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ['林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "pdd_数据中心_服务数据_售后数据"
    site = '拼多多'
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 3)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]

        Obj = PddDataCentre(cookie)
        for date in crawl_day_list:
            res = Obj.pdd_service__after_sales_data(date)
            # print( res)
            items = []
            item = {}
            for k, v in dict_str.items():
                item[v] = res.get("result", {}).get(k, "")

            item.update({
                "店铺名称": shop_name,

            })
            item["key"] = f"{item['店铺名称']}_{item['统计日期']}"

            items.append(item)

            DBManager(db_config=db_config).update_insert_data(items, table_name, primary_key="key")
            logger.info(f"{shop_name}_{date}数据已入库")
            logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
