# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 20:24:44
- 最近修改：2026-06-10 21:05:00
- 文件用途：封装淘宝直播中控台直播概览每日分析接口，负责请求参数、签名调用和 JSONP 返回解析，向任务层返回平台原始 result。
- 业务范围：适用于淘系直播中控台直播概览页面，按开始日期和结束日期查询每日分析概览指标。
- 依赖入口：继承 API.API_TaoXi_ZhiBo.API_TaoXi_ZhiBo_Base.TaoXiZhiBoBaseApi，使用 requests、date_utils.get_millisecond_timestamp、extra.extra_reqlog.req_log 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、单日期验证状态码、返回结构、字段映射和异常日志。
- 注意事项：API 层不写业务表、不持有店铺列表和数据库配置；日志不得输出完整 Cookie、签名 URL 或敏感请求参数。
"""

import json
import re
from urllib.parse import urlencode

import requests

from API.API_TaoXi_ZhiBo.API_TaoXi_ZhiBo_Base import APP_KEY, TaoXiZhiBoBaseApi
from date_utils import get_millisecond_timestamp
from extra.extra_reqlog import req_log
from extra.logger_ import logger


LIVE_OVERVIEW_FIELD_COLUMNS = (
    "post_content_cnt_nd",
    "post_time_nd",
    "look_uv_nd",
    "look_pv_nd",
    "atn_uv_nd",
    "atn_uv_rate_nd",
    "fans_return_rate_nd",
    "expo_uv_itm_nd",
    "expo_pv_itm_nd",
    "ipv_uv_nd",
    "ipv_nd",
    "pay_byr_cnt_nd",
    "cvr_nd",
    "pay_itm_qty_nd",
    "pay_ord_cnt_nd",
    "pay_amt_nd",
    "confirm_byr_cnt_nd",
    "confirm_itm_qty_nd",
    "confirm_ord_cnt_nd",
    "confirm_amt_nd",
    "pay_byr_cnt_nd_new",
    "pay_amt_nd_new",
    "atv_nd",
    "aov_nd",
    "aiv_nd",
    "rfd_byr_cnt_nd_filter",
    "rfd_itm_qty_nd_filter",
    "rfd_ord_cnt_nd_filter",
    "rfd_amt_nd_filter",
    "cart_uv_nd",
    "cart_pv_nd",
    "cart_itm_qty_nd",
    "cart_amt_nd",
    "look_time_nd",
    "look_time_pu_nd",
    "look_time_pt_nd",
    "fvr_uv_nd",
    "fvr_pv_nd",
    "cmt_uv_nd",
    "cmt_pv_nd",
    "shr_uv_nd",
    "shr_pv_nd",
    "sns_uv_nd",
    "sns_pv_nd",
    "sns_pv_pu_nd",
    "pay_amt_nd_self_rate",
    "mbr_cnt_incr_nd",
    "pay_byr_cnt_nd_mbr",
    "pay_amt_nd_mbr",
    "pay_amt_nd_slr",
    "pay_amt_nd_slr_rate",
    "pay_itm_qty_nd_mbr",
    "pay_ord_cnt_nd_mbr",
    "pay_amt_nd_self",
)


class TaoXiZhiBoLiveOverviewApi(TaoXiZhiBoBaseApi):
    """淘系直播概览接口，负责刷新 mtop token 并请求每日分析数据。"""

    @staticmethod
    def _normalize_day(day):
        return str(day).replace("-", "")

    @staticmethod
    def _extract_cookie_token(cookie):
        token_match = re.search(r"(?:^|;\s*)_m_h5_tk=([^;]+)", cookie or "")
        if not token_match:
            return None

        m_h5_tk = token_match.group(1)
        token = m_h5_tk.split("_")[0]
        enc_match = re.search(r"(?:^|;\s*)_m_h5_tk_enc=([^;]+)", cookie or "")
        return {
            "token": token,
            "_m_h5_tk": m_h5_tk,
            "_m_h5_tk_enc": enc_match.group(1) if enc_match else None,
        }

    def _build_live_overview_data(self, begin_date, end_date):
        query_param = {
            "startDate": self._normalize_day(begin_date),
            "endDate": self._normalize_day(end_date),
            "fieldColumns": ",".join(LIVE_OVERVIEW_FIELD_COLUMNS),
            "start": "0",
            "hit": "30",
            "orderColumn": "ds",
            "orderType": "desc",
            "summary": "false",
        }
        data = {
            "dataApi": "zkt_zbgl_all_data_all",
            "param": json.dumps(query_param, ensure_ascii=False, separators=(",", ":")),
        }
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    def live_overview(self, begin_date, end_date):
        """查询直播概览每日分析数据。"""
        api = "https://h5api.m.taobao.com/h5/mtop.dreamweb.query.general.generalquery/1.0/"
        cookie_token = self.get_cookie_token(self.cookie)
        if not cookie_token or not cookie_token.get("token"):
            cookie_token = self._extract_cookie_token(self.cookie)
            if cookie_token and cookie_token.get("token"):
                logger.warning("淘宝直播概览接口未刷新 mtop token，使用现有 Cookie token 继续请求")
            else:
                logger.error("淘宝直播概览接口获取 mtop token 失败")
                return None

        token = cookie_token["token"]
        new_cookie = self.get_new_cookie(
            self.cookie,
            cookie_token.get("_m_h5_tk"),
            cookie_token.get("_m_h5_tk_enc"),
            filter_=["tfstk"],
        )
        timestamp = get_millisecond_timestamp()
        data = self._build_live_overview_data(begin_date, end_date)
        sign = self.get_sign(token, timestamp, data)
        params = {
            "jsv": "2.7.4",
            "appKey": APP_KEY,
            "t": timestamp,
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
        response = requests.get(url=url, headers=headers, timeout=30)
        if not req_log(response):
            return None

        json_match = re.findall(r"mtopjsonp\d+\((.*?)\)", response.text)
        if not json_match:
            logger.error("淘宝直播概览接口未返回有效 JSONP 数据")
            return None

        response_data = json.loads(json_match[0])
        ret = response_data.get("ret") or []
        if ret and str(ret[0]).startswith("SUCCESS"):
            logger.info("淘宝直播概览接口请求成功")
        else:
            logger.warning(f"淘宝直播概览接口返回异常: {ret}")
        return response_data

    def live_overview_items(self, begin_date, end_date):
        """查询直播概览每日分析数据，并返回平台原始 result 列表。"""
        response_data = self.live_overview(begin_date, end_date)
        ret = response_data.get("ret") if response_data else []
        if not ret or not str(ret[0]).startswith("SUCCESS"):
            return []
        return response_data.get("data", {}).get("result") or []
