
# File: 淘宝直播_数据_每日分析_每日明细


from TiaoMaoMySellerApi.TbLiveDataAPI import TbLiveDataAPI
from TiaoMaoMySellerApi.login_ import ZBZKTCookies


from extra.data_collector import data_collector
from cookie_manager.extra_cookie import cookiejar_to_cookie_str
from extra.logger_ import logger


def parse_res(res_json):
    print(res_json)
    ret = res_json["ret"][0]
    if ret == "SUCCESS::调用成功":
        result = res_json["data"]["result"]
        for i in result:
            cn_item_data = Obj.cn_to_en(i, "live_overview")
            print(cn_item_data)


if __name__ == '__main__':
    shop_name_list = ['林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    db_table_name = "tb_zbzkt_数据_直播概览_每日分析_202507" # noqa
    site = '淘系_生意参谋'
    shop_cookies, crawl_day_list = data_collector(db_table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        ChituCookies_obj = ZBZKTCookies(shop_name, f'{cookie}')
        cookie_res = ChituCookies_obj.main()

        if cookie_res["status"] == 1:
            cookie_str = cookiejar_to_cookie_str(cookie_res["content"])
            # cookie_str='thw=cn; t=61f6d9516106249f280ae435a10c9a79; wk_cookie2=167378e44dd073cc15b504cc30abf9be; wk_unb=UUpgT7aDm3jPjxplCg%3D%3D; aui=2208167046031; cookie2=172757b142ff0859fda161355a9b6cfc; _tb_token_=7beb63e6ba3a3; _samesite_flag_=true; 3PcFlag=1753066317776; xlly_s=1; unb=2208167046031; sn=%E5%B0%8F%E5%90%89%E6%97%97%E8%88%B0%E5%BA%97%3Axj; uc1=cookie14=UoYbyGyaUk%2BUSw%3D%3D&cookie21=U%2BGCWk%2F7oPIg; csg=ca61860c; _cc_=VT5L2FSpdA%3D%3D; cancelledSubSites=empty; skt=193d9f9dfca649a4; sgcookie=E100bO%2B8BYDurlQfVmd14zwwku%2BnVgoM9Nk4jN7Il7TA1tjvWoddNntbySe1Kuks2wbJlgY3BDoVqYQikiVbkehoM26iYW7EJix2MYdM7tYlYBYO5gq6YAJzh74PAQak5y4R; mtop_partitioned_detect=1; _m_h5_tk=3588501ce6d9351dd17109219541ae20_1753077646279; _m_h5_tk_enc=a66c81d5029d12e8508fa1a929587e51; cna=lfD9IG0+9xICASeqbVqW8/Qp; tfstk=gncim19giAy6DexLpXN6ClUJVD9L15Nb5mCYDSE2LkrQMVUv5q8mD4kYX-3tKroxAET_6qrmmDEQkAETDtfqAkgTHnT1uDmIjtHT_5BViq0-WACtiv1mPqG95SL_1VNbg3KJwS0s5S6OaJ_Jv284lS4NED9HbVNbgHB28VPo5cg3UyM4geVUorbagRo4T9rQlrSau18H-kafQi5Vg25Urz_agSoq8e4bYPP4gmuEM_TaXci-Tn4fedS-5Vh3SRqr-L1ViX58Iuugxs-xtPx74Vrhgsro9RTS-VKGN2Fsg04-XB5iqquS3JccY3qjt2lZ32sM870npYeiKh50vfU0USyhusu3gAyx_7RPxyMEWxlsjZf45fh8nuwHuswYTberUcbXP2PaumwSM31_bquSNYFksgaiL4Vh4SWFURUFGy8xTt6bQya32SGZi6l9ZM5B-eXzhRzQ5BYH-t6bQya32eYhUVwaRPOh.; isg=BGxsuu1iKEJsaDx0dA502L0hPUqeJRDPrIJKeMateZe60Qzb7jXgXxJn9Znp30gn'
            Obj = TbLiveDataAPI(cookie_str)
            for day in crawl_day_list:
                logger.info(f"正在采集{day}，{day}的数据")
                res_json = Obj.live_overview(day,day)
                parse_res(res_json)
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
