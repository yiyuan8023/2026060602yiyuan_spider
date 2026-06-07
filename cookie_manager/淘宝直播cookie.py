import json

from cookie_manager.cookie_collector import cookie_collector
from cookie_manager.web_cookie_manager import WebCookieManager
from database import DBManager
from extra.logger_ import logger

if __name__ == "__main__":

    # shop_name_list = ['林内官方旗舰店', '林内厨电旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    shop_name_list = ["林内官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    # shop_name_list = []
    table_name = "get_cookie"
    site = "生意参谋"
    target_site = "淘系_直播中控台"
    first_url = f"https://login.taobao.com/havanaone/login/login.htm"
    target_url = f"https://liveplatform.taobao.com/restful/index/live/overview"

    shop_cookies = cookie_collector(site, shop_name_list)
    # print(shop_cookies)

    for i in shop_cookies:
        items = {}
        cookie = i[2]
        shop_name = i[0]
        cookieObj = WebCookieManager(first_url, cookie, target_url)
        result = cookieObj.main()

        if result.get("status") == 1:

            items["店铺名称"] = shop_name
            items["站点"] = target_site
            items["key"] = f"{target_site}|{shop_name}"

            # 构建 cookie_json, 将 cookie 转换为 JSON 字符串
            items["cookie"] = json.dumps(
                {"url": target_url, "cookies": result.get("content")},
                ensure_ascii=False,
            )

            # 构建 cookie 字符串
            items["cookie_str"] = "; ".join(
                [
                    f"{cookie['name']}={cookie['value']}"
                    for cookie in result.get("content")
                ]
            )

            items["cookie_dict"] = json.dumps(
                {item["name"]: item["value"] for item in result.get("content")}
            )

            items_list = [items]
            # print(items_list)
            DBManager().update_insert_data(items_list, table_name, primary_key="key")
            logger.info(f"{shop_name}获取cookie成功")
        else:
            logger.info(f"{shop_name}获取cookie失败")
