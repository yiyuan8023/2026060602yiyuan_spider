from API.API_ShengCan import Home
from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.logger_ import logger
from extra.extra_date import get_format_timestamp

change_view__all_index_mapping = {
    "支付金额": "payAmt",
    "店铺客户数": "shopCustomer",
    "平均停留时长": "stayTime",
    "支付买家数": "payByrCnt",
    "支付转化率": "payRate",
    "客单价": "payPct",
    "老客复购率": "hasPurchaseUbyCntRate",
    "老客复购人数": "payOldByrCnt",
    "老客复购金额": "olderPayAmt",
    "支付子订单数": "payOrdCnt",
    "支付件数": "payItmCnt",
    "访客数": "uv",
    "浏览量": "pv",
    "成功退款金额": "rfdSucAmt",
    "净支付金额": "netPaymentAmount",
    "加购件数": "cartCnt",
    "加购人数": "cartByrCnt",
    "商品收藏人数": "cltItmCnt",
    "咨询率": "consultRate",
    "旺旺人工响应时长(秒)": "wwReplyManualAvgTimeLen",
    "24小时揽收及时率": "gotInTime24hRate",
    "物流到货时长(小时)": "avgSignTimeHh",
    "退款处理时长(天)": "rfdFinshDur",
    "成功退款率": "sucRefundRate",
    "平台判责率": "slrRespRate",
    "关键词推广花费": "p4pExpendAmt",
    "精准人群推广花费": "cubeAmt",
    "智能场景花费": "adStrategyAmt",
    "淘宝客佣金": "tkExpendAmt",
    "统计日期": "statDate",
    "全站推广花费": "admCostFamtQzt",  # NOQA
    "总支付金额": "subPayOrdAmt",
    "总支付子订单数": "subPayOrdSubCnt",
}
if __name__ == "__main__":

    shop_name_list = ["林内官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_sycm_首页_数据概览_图表_新版_202504"  # NOQA
    site = "淘系_生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 3)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        HomeObj = Home(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集{shop_name},{day}的数据")
            new_overview_res = HomeObj.fetch_data_overview(day)
            self_ = new_overview_res["content"]["data"]["self"]
            item = {}

            for k, v in change_view__all_index_mapping.items():
                field_value = self_.get(
                    v
                )  # 获取健是v(英文字段的值)，返回的还是一个dic,如果找不到value 返回None
                item[k] = (
                    field_value.get("value")
                    if isinstance(field_value, dict)
                    else field_value
                )

            time_str = get_format_timestamp(item["统计日期"])
            item.update(
                {
                    "店铺名称": shop_name,
                    "key": f"{shop_name}_{time_str}",
                    "统计日期": time_str,
                }
            )
            # print(item)
            DBManager().update_insert_data([item], table_name, primary_key="key")
            logger.info("-" * 100)
            logger.info(f"{shop_name},{day}的数据已入库")
    logger.info(f"\n{'*' * 120}")

# python tb_sycm_首页_数据概览_图表_新版_202504.py --start-date=2025-03-27 --end-date=2025-04-18 # NOQA
