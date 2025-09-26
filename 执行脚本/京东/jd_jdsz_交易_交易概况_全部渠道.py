from API.API_JingDong.API_Jdsz_Product import JdSzProductAPI
from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager
from extra.en_to_cn import en_to_cn
from extra.logger_ import logger

# noqa: E501
dict_str = {
    'UV': "访客数",
    'OrdAmt': "成交金额",
    'CancelSaleQty': "取消及售后退款件数",
    'PV': "浏览量",
    'OrdNum': "成交单量",
    'CancelOrdAmt': "取消及售后退款金额",
    'AvgStayTime': "平均停留时长（秒)",
    'CancelOrdQty': "取消及售后退款单量",
    'CustPriceAvg': "客单价",
    'OrdProNum': "成交商品件数",
    'AvgDepth': "人均浏览量",
    'ToOrderRate': "下单转化率",
    'OrderAmt': "下单金额",
    'OrderNum': "下单单量",
    'ToOrdRate': "成交转化率",
    'OrderCustNum': "下单客户数",
    'SkipOut': "跳失率",
    'UnitPriceAvg': "件单价",
    'OrdCustNum': "成交客户数",
    'OrderProNum': "下单商品件数",
    'DealToOrderRate': "下单成交转化率"
}

if __name__ == '__main__':
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ['BMW官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "jd_jdsz_客户_品牌会员_会员概况_开卡会员_202509"
    site = '京东商智'
    shop_cookies, crawl_day_list = data_collector(table_name, site, shop_name_list, 7)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        data_list = []
        Obj = JdSzProductAPI(cookie)
        for date in crawl_day_list:
            data = {}
            res = Obj.fetch_trade_summary(date)

            content = res.get("content", {})
            for K, V in content.items():
                data[K] = V.get("value", None)
            data_list.append(data)  # 因为en_to_cn的第一参数是列表，所以这里不能用字典，做一个转换
            data_list = en_to_cn(data_list, dict_str)
            # print(data_list)

            items = []
            for item in data_list:
                item.update({
                    "店铺名称": shop_name,
                    "统计日期": date,
                    "日期类型": "day"

                })
                item["key"] = f"{item['店铺名称']}_{item['统计日期']}_{item['日期类型']}"
                items.append(item)

            DatabaseManager(db_config=db_config).upsert_data(items, table_name, primary_key="key")
            logger.info(f"{shop_name}_{date}数据已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
