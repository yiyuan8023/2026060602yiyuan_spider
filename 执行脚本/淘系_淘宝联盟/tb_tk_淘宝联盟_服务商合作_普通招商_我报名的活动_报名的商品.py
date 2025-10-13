# File: 淘宝联盟_商品分析
from API.API_TaoKe.API_TaoKe_MyProducts import TaoKeMyProductApi
from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager

from extra.logger_ import logger


def extract_items(res_dic):
    """
    从 body 列表中提取每个项目的相关信息，返回字典类型的 items 数据。
    """

    body = res_dic.get('data').get('result')
    items = []

    for loop_item in body:
        try:

            start_time = loop_item.get('startTime')  # 开始时间
            end_time = loop_item.get('endTime')  # 结束时间
            audit_time = loop_item.get('auditTime')  # 审核通过时间
            show_status_desc = loop_item.get('showStatusDesc')  # 提取状态信息

            # 提取团长信息
            campaign_creator_name = loop_item.get('campaignCreatorName')

            # 提取商品信息
            resource = loop_item.get('resource', [{}])[0]  # 获取第一个资源
            campaign_id = resource.get('campaignId')  # 推广计划ID
            sign_up_record = resource.get('signUpRecord')  # 报名记录

            itemInfoDTO = resource.get('itemInfoDTO')  # NOQA
            item_id = itemInfoDTO.get('itemId')
            title = itemInfoDTO.get('title')
            shop_title = itemInfoDTO.get('shopTitle')

            # 提取广告单元信息
            advertising_unit = loop_item.get('advertisingUnit', {})
            commission_rate = advertising_unit.get('commissionRate')  # 佣金率
            service_rate = advertising_unit.get('serviceRate')  # 服务费率

            # 构建 item 字典
            item_ = {
                '开始时间': start_time,
                '结束时间': end_time,
                '状态': show_status_desc,
                '审核通过时间': audit_time,
                '团长信息': campaign_creator_name,
                '商品id': item_id,
                '商品标题': title,
                'campaignId': campaign_id,
                'signUpRecord': sign_up_record,
                '佣金率': commission_rate,
                '服务费率': service_rate
            }

            items.append(item_)

        except Exception as e:
            print(f"处理数据时出错: {e}")
            continue

    return items


if __name__ == "__main__":
    db_config = "rinnai_py"  # noqa
    shop_name_list = ['林内热水器旗舰店', '林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_tk_淘宝联盟_服务商合作_普通招商_我报名的活动_报名的商品_202509"
    site = '淘宝联盟'
    shop_cookies, crawl_day_list = data_collector(table_name, site, shop_name_list, 1)
    pages = range(1, 2)  # 采集只和页码有关系和时间没有关系

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        Obj = TaoKeMyProductApi(cookie)

        for page in pages:
            logger.info(f"正常采集第{page}页数据")
            res = Obj.tb_tk_my_enrolled_products(page)
            # print( res)
            items = extract_items(res)
            print(items)
            for item in items:
                item.update({
                    "店铺名称": shop_name,

                })
                # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
            # print(items)

            DatabaseManager(db_config=db_config).upsert_data(items, table_name, primary_key="sign_up_record")

        # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_tk_淘宝联盟_商品分析_202504.py --start-date=2025-03-27 --end-date=2025-04-18
