# -*- coding: utf-8 -*-
"""淘宝直播数据 API。"""

import json
import re
from urllib.parse import urlencode

import requests

from API.API_TianMaoMySeller.MySellerBase import MySellerBaseAPI
from date_utils import get_millisecond_timestamp
from extra.extra_reqlog import req_log
from extra.logger_ import logger


class TbLiveDataAPI(MySellerBaseAPI):
    """淘宝直播数据接口，负责刷新 mtop token 并请求直播概览。"""

    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def live_overview(self, begin_date, end_date):
        """查询直播概览每日分析数据。"""
        api = "https://h5api.m.taobao.com/h5/mtop.dreamweb.query.general.generalquery/1.0/"
        cookie_token = self.get_cookie_token(self.cookie)
        token = cookie_token["token"]

        # 刷新 mtop token 后重组 cookie；tfstk 易变且非签名必要字段，这里过滤掉。
        new_cookie = self.get_new_cookie(
            self.cookie,
            cookie_token["_m_h5_tk"],
            cookie_token["_m_h5_tk_enc"],
            filter_=["tfstk"],
        )
        t = get_millisecond_timestamp()

        # data 内层 JSON 是平台接口约定，fieldColumns 控制返回指标列。
        data = r'{"dataApi":"zkt_zbgl_all_data_all","param":"{\"startDate\":\"20250814\",\"endDate\":\"20250814\",\"fieldColumns\":\"post_content_cnt_nd,post_time_nd,look_uv_nd,look_pv_nd,atn_uv_nd,atn_uv_rate_nd,fans_return_rate_nd,expo_uv_itm_nd,expo_pv_itm_nd,ipv_uv_nd,ipv_nd,pay_byr_cnt_nd,cvr_nd,pay_itm_qty_nd,pay_ord_cnt_nd,pay_amt_nd,confirm_byr_cnt_nd,confirm_itm_qty_nd,confirm_ord_cnt_nd,confirm_amt_nd,pay_byr_cnt_nd_new,pay_amt_nd_new,atv_nd,aov_nd,aiv_nd,rfd_byr_cnt_nd_filter,rfd_itm_qty_nd_filter,rfd_ord_cnt_nd_filter,rfd_amt_nd_filter,cart_uv_nd,cart_pv_nd,cart_itm_qty_nd,cart_amt_nd,look_time_nd,look_time_pu_nd,look_time_pt_nd,fvr_uv_nd,fvr_pv_nd,cmt_uv_nd,cmt_pv_nd,shr_uv_nd,shr_pv_nd,sns_uv_nd,sns_pv_nd,sns_pv_pu_nd,pay_amt_nd_self_rate,mbr_cnt_incr_nd,pay_byr_cnt_nd_mbr,pay_amt_nd_mbr,pay_amt_nd_slr,pay_amt_nd_slr_rate,pay_itm_qty_nd_mbr,pay_ord_cnt_nd_mbr,pay_amt_nd_self\",\"start\":\"0\",\"hit\":\"30\",\"orderColumn\":\"ds\",\"orderType\":\"desc\",\"summary\":\"false\"}'
        sign = self.get_sign(token, t, data)
        params = {
            "jsv": "2.7.4",
            "appKey": "12574478",
            "t": t,
            "sign": sign,
            "api": "mtop.dreamweb.query.general.generalQuery",  # noqa
            "v": "1.0",
            "preventFallback": "true",
            "type": "jsonp",
            "dataType": "jsonp",
            "callback": "mtopjsonp71",  # noqa
            "data": data,
        }
        headers = {
            "referer": "https://liveplatform.taobao.com/restful/index/live/overview",
            "user-agent": self.ua,
            "cookie": new_cookie,
        }
        url = api + "?" + urlencode(params)
        res = requests.get(url=url, headers=headers)
        if req_log(res):
            json_str = re.findall(r"mtopjsonp\d+\((.*?)\)", res.text)
            res_json = json.loads(json_str[0])
            logger.info("淘宝直播概览接口请求成功")
            return res_json
        return None
