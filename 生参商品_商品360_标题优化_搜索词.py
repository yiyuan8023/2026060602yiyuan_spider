# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-05-13
# Time: 08:54
# Project: jide
# File: 生参商品_商品360_标题优化_搜索词
from ShengCanApi.goods import Goods
from db import DB
from extra_parser import parser_main
from extra_time import get_date, calculate_days_diff_with_range
from logger_ import logger
def analyzing_res(res_json):
    if res_json:
        data = res_json["data"]
        items = []
        for i in data:
            item = {}
            for k, v in i.items():
                item[k] = v["value"]
            items.append(item)
    else:
        return None


if __name__ == "__main__":
    items_id = ["642099861838", "903063784358", "730041207065", "714503017797", "675798939621",
                "718096971652", "637233481572", "887346116879", "624265120354", "625997280765", "593255510794",
                "775408759170", "742262865690", "684120356054", "675755495225", "897925854137", "731454769461",
                "549872388632", "734667779345", "838390284669", "900319204611"]
    logger.info("*" * 100)
    logger.info("开始采集：tb_sycm_商品_商品360_标题优化_搜索词")
    start_date, end_data = parser_main()
    if start_date and end_data:
        crawl_day_list=calculate_days_diff_with_range(start_date,end_data)
        logger.info(f"解析参数{start_date}-{end_data}，即采集列表{crawl_day_list}")
    else:
        crawl_day_list=[-1]

    cookies_ = DB().do_select_cookies("生意参谋")
    for i in cookies_:
        cookie = i[1]
        shop_name = i[0]
        GoodObj = Goods(cookie)
        for item_id in items_id:
            for days in crawl_day_list:
                start_date_=end_data_=get_date(days)
                logger.info(f"正在采集{shop_name}，item_id：{item_id}，{get_date(days)}的数据")
                dateRange = f"{start_date_}|{end_data_}"
                items = GoodObj.goods_360__title_drainage_excel(dateRange, item_id)
                if items:
                    for item in items:
                        item.update({
                            "店铺名称": shop_name,
                            "日期类型": "day",
                            "统计日期":start_date_,
                            "商品ID": item_id,

                        })
                        item["key"] = f"{item["统计日期"]}_{item["商品ID"]}_{item['日期类型']}_{item['店铺名称']}_{item['搜索词']}"
                    DB().do_insert(items, "tb_sycm_商品_商品360_标题优化_搜索词_202504")
            # analyzing_res(res_json)
"""
https://sycm.taobao.com/cc/item/title/word/excel.json?spm=a21ag.12100465.0.0.18e550a5aWB6l6&itemId=673717490518&device=0&kwType=se_keyword&dateType=day&dateRange=2025-05-12|2025-05-12"""
# python 生参商品_商品360_标题优化_搜索词.py --start-date=2025-05-01 --end-date=2025-05-11
