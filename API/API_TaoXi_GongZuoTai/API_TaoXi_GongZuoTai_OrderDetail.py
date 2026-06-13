# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 09:17:59
- 最近修改：2026-06-12 14:24:30
- 文件用途：封装淘系商家工作台订单详情接口，负责查询并解析消费者视角优惠明细，同时显式返回原始 json_data。
- 业务范围：适用于商家工作台交易已卖出宝贝订单详情页的 orderDetailQianNiu 接口。
- 依赖入口：继承 API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Base.TaoXiGongZuoTaiBaseApi，使用 downloader.core.Downloader、extra.logger_、extra.extra_error 和 parser_order_discount_details。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、少量订单验证订单详情结构、优惠明细字段和异常日志。
- 注意事项：API 层不写业务表、不持有店铺列表和数据库配置；日志不得输出完整 Cookie、订单详情完整敏感响应或签名参数。
"""

import json

from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Base import (
    TaoXiGongZuoTaiBaseApi,
)
from API.API_TaoXi_GongZuoTai.parser_order_discount_details import (
    parse_order_discount_details,
)
from downloader.core import Downloader
from extra.extra_error import handle_request_error
from extra.logger_ import logger


class TaoXiGongZuoTaiOrderDetailApi(TaoXiGongZuoTaiBaseApi):
    """淘系商家工作台订单详情 API，负责查询消费者视角优惠明细。"""

    def order_discount_details(self, order_id):
        """查询订单详情里的消费者视角优惠明细。"""
        api = "https://trade.taobao.com/detail/orderDetailQianNiu.htm?"
        params = {
            "bizOrderId": order_id,
            "sifg": "0",  # noqa
            "isQnNew": "true",
            "isHideNick": "true",
        }
        headers = {
            "referer": f"https://qn.taobao.com/home.htm/trade-platform/tp/detail?spm=a21dvs.23580594.0.0.78bb645eKEvf97&bizOrderId={order_id}"
        }

        try:
            response = Downloader(
                api=api,
                cookie=self.cookie,
                params=params,
                headers=headers,
                context="商家工作台订单详情",
            ).download_web()
        except Exception as exc:
            handle_request_error(exc, context="商家工作台订单详情")
            raise

        if not response.ok:
            raise RuntimeError(f"商家工作台订单详情请求失败，status_code={response.status_code}")

        response_data = response.json()
        json_data = json.dumps(response_data, ensure_ascii=False)
        if response_data.get("needJumpOld"):
            return {
                "business_items": [{"备注": "无消费者视角优惠明细标签"}],
                "json_data": json_data,
            }

        parsed_data = parse_order_discount_details(response_data)
        if not parsed_data:
            logger.warning(
                f"商家工作台订单详情未解析到优惠明细字段，order_id={order_id}, "
                f"response_keys={list(response_data.keys())}"
            )
        else:
            logger.info("已解析消费者视角优惠明细")
        return {"business_items": [parsed_data], "json_data": json_data}
