from cookie_manager.extra_cookie import get_cookie_value
from downloader.core import Downloader
from date_utils import get_millisecond_timestamp
from extra.logger_ import logger
from config import UA


class TaoKeDingXiangApi:
    # 检测cookie有没有失效
    def __init__(self, cookie=None):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua}

    def get_campaign(self, start_time, end_time):
        """
        获取影刀社区问题
        """

        api = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/data.event.taoke.campaign.json"
        t = get_millisecond_timestamp()
        params = {
            "t": t,
            "_tb_token_": get_cookie_value(self.cookie, "_tb_token_"),
            "itemId": "",
            "cStep": "0",
            "startDate": start_time,
            "endDate": end_time,
            "campaignTemplateId": "992",
            "advPageEnum": "adv_992",
            "pageNo": "1",
            "pageSize": "2000",
        }
        headers = {
            "Referer": f"https://ad.alimama.com/portal/v2/pages/plan/directed/report.htm?tabType=plan&campaignId=&startDate={start_time}&endDate={end_time}",
            "User-Agent": self.ua,
            # "priority": "u=1, i",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": self.cookie,
        }

        res = Downloader(
            api,
            params=params,
            headers=headers,
            context="淘宝客定向计划报表",
        ).download_web()

        items = []
        if res.ok:
            questions = res.json().get("data", {}).get("data", [])
            for question in questions:
                item = {
                    "统计日期": question.get("thedate"),
                    "任务信息": question.get("campaignTitle"),
                    "任务id": question.get("campaign_id"),
                    "点击数": question.get("uclk_pv_2959"),
                    # "点击数": question.get("new_enter_user_pv_2959"),
                    "点击转化率": question.get("union_cvr_2959"),
                    "付款笔数": question.get("pay_ord_num_2959"),
                    "付款金额": question.get("pay_ord_amt_2959"),
                    "付款佣金支出（元）": question.get("pay_ord_cfee_2959"),
                    "付款佣金率": question.get("sett_ord_cfee_rt_2959"),
                    "确认收货笔数": question.get("conf_ord_num_2959"),
                    "确认收货金额(元)": question.get("conf_ord_amt_2959"),
                    "结算金额(元)": question.get("sett_ord_amt_2959"),
                    "结算佣金支出(元)": question.get("sett_ord_cfee_2959"),
                    "结算佣金率": question.get("sett_ord_cfee_rt_2959"),
                }
                # print(item)
                items.append(item)
        # print( items)
        return items
