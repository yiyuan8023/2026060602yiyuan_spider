import random
from time import sleep

from API.API_TiaoMaoMySeller.MysellerTrade import MySellerTradeAPI
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager

from extra.logger_ import logger

if __name__ == '__main__':
    db_config = 'rinnai_py'  # NOQA

    # shop_name_list = ['林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    shop_name_list = ['林内官方旗舰店', '林内热水器旗舰店', '林内品牌折扣店', '智慧家电直销店',
                      '林内厨电旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺

    table_name = "tb_商家工作台_交易_已卖出宝贝_订单详情_消费者视角优惠明细_202601"
    site = '生意参谋'
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]

        sql = f"select `订单编号` from `py_tb_消费者视角优惠明细_新增` where 店铺名称='{shop_name}'"  # noqa
        db_obj = DBManager(db_config=db_config)
        order_list = db_obj.execute_sql(sql, fetch=True)
        # print(order_list)

        Obj = MySellerTradeAPI(cookie)  # 创建对象
        for order_id in order_list:
            items = Obj.taobao_order_discount_details(order_id[0])
            # print(order_id[0])
            for item in items:
                item.update({
                    "店铺名称": shop_name,
                    "主订单编号": order_id[0]
                })

            db_obj.update_insert_data(items, table_name, primary_key='主订单编号')
            # sleep(0.1)
            sleep(random.uniform(1, 5))
        logger.info("-" * 100)
    logger.info("*" * 100)
