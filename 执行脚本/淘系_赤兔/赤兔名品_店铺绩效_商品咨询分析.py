from API.API_ChiTu import ChiTuShopPerformanceAPI
from API.API_ChiTu import ChituCookies
from extra_cookie import cookiejar_to_cookie_str

from extra.select_shop_date import select_shop_date
from extra_time import get_date
from extra.logger_ import logger


def chitu_shop_performance():
    """
    店铺绩效
    """
    # 店铺绩效
    for days in crawl_day_list:
        logger.info(f"正在采集{shop_name}，{get_date(days)}的数据")
        from_ = to_ = get_date(days)
        product_consultation_analysis(from_, to_)


def product_consultation_analysis(from_, to_):
    """
    商品咨询分析
    :param from_:
    :param to_:
    :return:
    """
    data = ChiTuObj.product_consultation_analysis(from_, to_)
    items = []
    if data:
        for i in data:
            if i["商品编号"] == "汇总" or i["商品编号"] == "均值":
                pass
            else:
                i["店铺名称"] = shop_name
                i["统计日期"] = from_
                i["key"] = f'{i["店铺名称"]}{i["商品编号"]}{i["统计日期"]}'
                items.append(i)
        # print(items[0].keys())

        db_obj.do_insert(items, "tb_赤兔名品_店铺绩效_商品咨询分析_202504")


if __name__ == '__main__':
    CHITU_PASSWORD = {"小吉旗舰店": "xiaoji123"}

    shop_name_list = ['林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_sycm_流量_店铺来源_流量来源构成_整体_无线端_202504"  # NOQA
    site = '淘系_生意参谋'
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 10)

    crawl_day_list = crawl_day_list[7:]

    table_name = "tb_赤兔名品_店铺绩效_商品咨询分析_202504"
    for i in shop_cookies:
        shop_name = i[0]
        ChituCookies_obj = ChituCookies(shop_name, f'{i[1]}')
        cookie_res = ChituCookies_obj.main()

        if cookie_res["status"] == 1:
            cookie_str = cookiejar_to_cookie_str(cookie_res["content"])
            # 一目了然，初始化
            ChiTuObj = ChiTuShopPerformanceAPI(cookie_str, CHITU_PASSWORD[shop_name])

            chitu_shop_performance()


        else:
            logger.error("赤兔的cookie生成失败")

# python 赤兔名品_店铺绩效_商品咨询分析.py --start-date=2025-05-01 --end-date=2025-06-25
