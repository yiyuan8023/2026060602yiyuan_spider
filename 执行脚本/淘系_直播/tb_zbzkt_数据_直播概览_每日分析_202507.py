from API.API_TianMaoMySeller import TbLiveDataAPI

from extra.select_shop_date import select_shop_date
from extra.logger_ import logger


def parse_res(res_json):
    logger.info("解析直播概览接口返回数据")
    ret = res_json["ret"][0]
    if ret == "SUCCESS::调用成功":
        result = res_json["data"]["result"]
        for i in result:
            cn_item_data = Obj.cn_to_en(i, "live_overview")
            logger.info(f"直播概览单条数据: {cn_item_data}")


if __name__ == "__main__":
    shop_name_list = ["林内官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    db_table_name = "tb_zbzkt_数据_直播概览_每日分析_202507"  # noqa
    site = "淘系_直播中控台"
    shop_cookies, crawl_day_list = select_shop_date(
        db_table_name, site, shop_name_list, 1
    )

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]

        Obj = TbLiveDataAPI(cookie)

        for day in crawl_day_list:
            logger.info(f"正在采集{day}，{day}的数据")
            res_json = Obj.live_overview(day, day)
            # parse_res(res_json)
        # if items:
        #     for item in items:
        #         item.update({
        #             "店铺名称": shop_name,
        #             "日期类型": "day",
        #             "统计日期": start_date_,
        #
        #         })
        #         item["key"] = f"{item['店铺名称']}_{item["统计日期"]}_{item['日期类型']}_{item['视频id']}"
        #     DB().do_insert(items, "tb_sycm_内容_渠道效果_推荐_单条效果_微详情视频_全部内容_202507")
