import json
import re
from time import sleep

from defusedxml.xmlrpc import MAX_DATA
from tenacity import retry, stop_after_attempt, wait_fixed
from TiaoMaoMySellerApi.MysellerTrade import MySellerTradeAPI
from db import DB

from extra.data_collector import data_collector
from extra.extra_date import get_min_max_timestamps
from extra.extra_excel import read_excel_to_dict

from extra.logger_ import logger


def download_excel(apply_time):
    sleep(5 * 60)
    exportlist_text = Obj.trade_order_exportlist()
    json_str = re.findall(r'mtopjsonp\d+\((.*?)\)', exportlist_text)
    exportlist_json = json.loads(json_str[0])
    data = exportlist_json['data']
    detailList = data['detailList']
    for i in detailList:
        if i["applyTime"] == apply_time:
            f_p = i["itemEncrypterStr"]
            apply_time = i["applyTime"]
            startTimeStr = i["startTimeStr"]
            endTimeStr = i["endTimeStr"]
            orderStatus = i["orderStatus"]
            exportId = i["exportId"]
            excel_content = Obj.export_by_tfs(f_p, apply_time, startTimeStr, endTimeStr, orderStatus,
                                              exportId)
            items = read_excel_to_dict(excel_content)
            return items
    return None


@retry(stop=stop_after_attempt(1), wait=wait_fixed(6 * 60))
def main(shop_name):
    """
       主函数：执行商家工作台已卖出宝贝报表的下载和处理流程
     """
    # 调用API创建报表导出任务，传入时间范围的时间戳
    list_export_order = Obj.taobao_list_export_order(start_timestamp, end_timestamp)
    # 记录API返回的日志信息
    logger.info(list_export_order)
    # list_export_order = {'code': 1, 'message': '新导出任务,返回的是新的', 'data': ['报表申请时间： 2025-04-28 14:45:01']}

    if list_export_order['data'] and len(list_export_order['data']) == 1 and list_export_order['code'] == 1:
        apply_time = re.findall("报表申请时间： (.*)", list_export_order['data'][0])[0]
        # print(apply_time)
        items = download_excel(apply_time)
        # print(len(items))
        for item in items:
            item["店铺名称"] = shop_name
        DB().do_insert(items, "tb_商家工作台_交易_已卖出宝贝_宝贝报表明细_202504")
    else:
        raise 1


if __name__ == '__main__':

    shop_name_list = ['林内热水器旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_商家工作台_交易_已卖出宝贝_宝贝报表明细_202504"
    site = '生意参谋'
    shop_cookies, crawl_day_list = data_collector(table_name, site, shop_name_list, 1)
    start_timestamp, end_timestamp = get_min_max_timestamps(crawl_day_list)

    for i in shop_cookies:
        cookie = i[1]
        # cookie='DI_T_=7VjQ9AVLnHHfjQL11bW5CjgGv695uHvHVmgRFez5ucq9jz6LtpC; thw=cn; wk_cookie2=1de33e37072f0ef696f0385c1905c161; wk_unb=UoH%2B4NPsNoWZlw%3D%3D; t=61f6d9516106249f280ae435a10c9a79; xlly_s=1; _tb_token_=ZTk2aitNmJH7zYnA3pv3; _samesite_flag_=true; 3PcFlag=1745808222868; cookie2=1d9ef8b653f7e70f0e513052d06ebe5d; sgcookie=E100No44G57IeIwbXVVenzgjGdrZCV%2F9%2FoGtI8k%2BT8Y5jTExK4vlNq%2FKIl7JqarY0MJx2PppLXNWV9ZJELlx8Lxp966sehI9XW497QoW%2FfEjlbv7rh7z7Azqmq3nSgGaRmYU; unb=2212373938588; sn=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; uc1=cookie21=W5iHLLyFfoaZ&cookie14=UoYajl1ZHctHNg%3D%3D; csg=ad998634; _cc_=UIHiLt3xSw%3D%3D; cancelledSubSites=empty; skt=7d859714774fdbb9; mtop_partitioned_detect=1; _m_h5_tk=82005775194ac46e35098c2db75d35b8_1745817954167; _m_h5_tk_enc=22cdfa43d9b8aa4f748f5e6ba79381ae; cna=0dmRIK+V4jICASeqbVoaDv9q; tfstk=gNxn790hqe7B0LlOWhsIoppWXegTOMs5dQERwgCr7151JJCKdYDkMLQz22sdrgAN6HCppMykZCdczQCJpCXyEQxJJpS-EgvXM6BJpMWyU1J59ghWqFZkhLtKdgHCAps54jhxDgvBdg_ggb7HqGJNetn88gSPAG58olTxDmpBLJBEHdov2eOhk1Uz4Q7F_dWC_JrU8Q7abT1aYTrFU5kG11WUTTrP_cWCFyryagkMQ16P49RP8AvZNaHF9BOvbfOW62O25VTlKwf2L6JpdhlV9yO5s1C6X9xRjpz74u-GKwxS4DZgYwLyhZtp30q1vKYNbTxS3zfloU-dbHlZ0N_ybCWw9YU5IUvycMs0UDJGx6b2qCyYDIJMUEQMXxofxM5eyM98nXpMxBpBjLez7MjpSZxh0mNFwFpDqTxSNcADUKTPS3Vh4J4auwBaVOkJbza58O6GMscDZHGNoDexIA4VPwW1dcDiIza58O6GMADgup_FC9iG.'
        shop_name = i[0]
        Obj = MySellerTradeAPI(cookie)  # 创建对象
        main(shop_name)
