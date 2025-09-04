"""
注：
步骤：生成任务-获取任务列表-在任务列表中寻找目标ID

1、cps订单，可以指定区间下载，只需要获取下载的开始日期和结束日期即可
2、创建任务后，会生成任务列表，需要从任务列表中找到对于的任务id，根据ID再获取报表
3、创建任务重，如果历史已经创建，会生成直白，直接从任务列表中获取即可
TODO:原打算先删除全部任务，然后再创建，但是在测试过程中，无法通过，所以放弃

"""

import requests

from TaoBaoLianMengApi.TaoKeBaseApi import TaoKeBaseApi
from extra.extra_date import get_millisecond_timestamp
from extra.extra_reqlog import req_log
from extra.logger_ import logger

from cookie_manager.extra_cookie import get_cookie_value


class TaoKeCpsApi(TaoKeBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def tb_tk_cps_settlement_report(self, start_time, end_time):
        """
        tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505
        创建任务
        """
        url = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/shopkeeper.rpt.taskstart.json"
        params = {
            "t": get_millisecond_timestamp(),
            "_tb_token_": get_cookie_value(self.cookie, '_tb_token_'),
            "startTime": f"{start_time} 00:00:00",
            "endTime": f"{end_time} 23:59:59",
            "bizType": 1,
            "status": 3,

        }
        # data = json.dumps(data, separators=(',', ':'))
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": self.cookie,
            "user-agent": self.ua,
            "referer": "https://ad.alimama.com/report/overview/orders.htm",
            "origin": "https://ad.alimama.com",
            'Host': 'ad.alimama.com',  # noqa
        }
        res = requests.get(url=url, headers=headers, params=params)
        if req_log(res):
            logger.success(f'成功！！！创建任务日期:{start_time}')
            return res.json()
        else:
            logger.error(f'失败！！！创建任务日期:{start_time}')
            return None

    def delete_report(self, id_list):

        """
        删除已创建id
        """

        api = "https://ad.alimama.com/openapi/param2/1/gateway.unionadv/shopkeeper.rpt.taskdel.json"
        params = {
            "t": get_millisecond_timestamp(),
            # "_tb_token_": get_cookie_value(self.cookie, '_tb_token_'),
            "_tb_token_": "efe0ee3eee3d7",

        }
        print(get_cookie_value(self.cookie, '_tb_token_'))
        print(get_millisecond_timestamp())
        data = {
            "bizType": "1",
            # "ids": f'["{id_list}"]'
            "ids": f'["1220600123"]'
        }

        headers = {
            "referer": "https://ad.alimama.com/report/overview/orders.htm",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "user-agent": self.ua,
            "cookie": self.cookie,
            "_m_h5_c": get_cookie_value(self.cookie, '_m_h5_c'),
            "accept-encoding": "gzip, deflate, br, zstd",
            "priority": "u=1, i",
            "bx-v": "2.5.11",
        }

        logger.info(f"删除已生成报表")
        res = requests.post(api, params=params, data=data, headers=headers)
        req_log(res)


if __name__ == '__main__':
    cookie = "t_alimama=cb1e46ae4ef98c49cfdb98274d3705e9;cookie2_alimama=1ca808f6dba367e5d4f89808d645e47d;v_alimama=0;cna=Pac+IfEs1RsCAXrgmQIyIqAV;rurl=aHR0cHM6Ly9hZC5hbGltYW1hLmNvbS9pbmRleC5odG0%2FZm9yd2FyZD1odHRwcyUzQSUyRiUyRmFkLmFsaW1hbWEuY29tJTJGcG9ydGFsJTJGdjIlMkZkYXNoYm9hcmQuaHRt;xlly_s=1;JSESSIONID=2A66D1638D8D1B2170286B93D8C5AE7B;dnk=;uc1=cookie14=UoYbzWq0mduvIw%3D%3D&cookie21=VFC%2FuZ9aj3yE;lid=%E6%9E%97%E5%86%85%E7%83%AD%E6%B0%B4%E5%99%A8%E6%97%97%E8%88%B0%E5%BA%97%3A%E6%95%B0%E6%8D%AE%E5%88%86%E6%9E%90;unb=2212197195313;lgc=;cookie2=1212ba258ddbd84af0a5b4a92a526ff1;_nk_=;sgcookie=E100eET%2BurAYEUtADJ4T1xyE1imiNRpAF5DnGHh6yFse0Zg0gq4dyVr%2BcnJCNhfHMX%2F%2BM336beYRjWAnq4s7A0%2FHq5hvpRQ8fY5R%2FdMkbUNZWxeSW%2FNDzMyrURxUXtIOfImY;cancelledSubSites=empty;t=5be9c659072f8dde1ee848f9878ec401;csg=8baf14b4;sn=%E6%9E%97%E5%86%85%E7%83%AD%E6%B0%B4%E5%99%A8%E6%97%97%E8%88%B0%E5%BA%97%3A%E6%95%B0%E6%8D%AE%E5%88%86%E6%9E%90;_tb_token_=7e1630078eef1;_m_h5_c=e2af257f0f88c2ab68c9797d05333dd7_1756881112958%3B60744622b8165a250434d4a5b5f5859c;tfstk=gUAxANgjm0mcXMZ4khDosIorsIgoHYY2en8QsGj0C3KJjH6suhvD61KkXOOciExJ53Tgsq-GGR65VHg4iCDwX1L9AOtGjE42UHYQiIDVs5CV_1inxXc33E5N19Js04S2PU7srZTqGk21_1inq8V13XCwcua7mtw5Pg7O5ls6fTZ5ogZ_ChsfFu_d81s6fhZ5NwQL1l_bGzgR7gs111t6P4QGVG111hTS_HmOVrsg6KOspx5UUaP_1QQAFYYfV5QkwZBAAEOY15aFktIBlgofUy1hFFW9_PPOEE9ebwtbcmC6ywLhHInLiG-26OdleAzhzdTWLd6-ljTRMiBManGn4sp60CB2HPuePstyLMWjU07JiBXOYTEScUYRc9p9m0P1mpLW29AuqWfWRLCR48dH94uQxMQgh438QRWfzyPgH2ex7BLFyM0x6RyNU47Rx438QRWfzaInkmeaQTuP."
    A = TaoKeCpsApi(cookie)
    b = A.delete_report("241406068")
    print(b)
