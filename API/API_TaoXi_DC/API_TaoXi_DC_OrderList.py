# -*- coding: utf-8 -*-
"""DChain order list API."""

from datetime import datetime

from API.API_TaoXi_DC.API_TaoXi_DC_Base import TaoXiDCBaseApi
from extra.logger_ import logger


class TaoXiDCOrderListApi(TaoXiDCBaseApi):
    """Read DChain order-list rows from the page API and parse visible tags."""

    ORDER_LIST_API = "/portal/v1/order/orders"
    DEFAULT_PAGE_SIZE = 100
    ORDER_FLAG_LABELS = {
        3: "分",
        8: "退货",
        9: "退款",
        43: "一盘货",
        57: "寄存",
        58: "到店",
        59: "统仓",
        63: "转",
        70: "零售",
        8002: "大店",
    }

    def query_order_list(self, payload, page=1, page_size=DEFAULT_PAGE_SIZE):
        params = dict(payload)
        params["pageIndex"] = page
        params["pageSize"] = page_size
        return self.request_json(
            self.ORDER_LIST_API,
            params=params,
            context="DChain订单列表查询",
            log_success=page == 1,
        )

    def fetch_order_records(self, payload, page_size=DEFAULT_PAGE_SIZE, max_pages=None):
        page = 1
        records = []
        while True:
            response_json = self.query_order_list(payload, page=page, page_size=page_size)
            row_items = self._extract_rows(response_json)
            if not row_items:
                break

            records.extend(self.parse_order_record(row_item) for row_item in row_items)
            total_count = int(response_json.get("totalCount") or len(records))
            logger.info(f"DChain订单列表已获取 {len(records)}/{total_count} 条")

            if len(records) >= total_count:
                break
            if max_pages and page >= max_pages:
                break
            page += 1
        return records

    @classmethod
    def build_order_list_payload(
        cls,
        start_time,
        end_time,
        warehouse="merchant",
        date_field="sysCreateTimeRange",
        order_code_type=2,
        biz_status=0,
        is_history=False,
    ):
        return {
            date_field: f"{start_time}/{end_time}",
            "bizStatus": biz_status,
            "isHistory": is_history,
            "orderCodeType": order_code_type,
            "warehouseDeliveryMode": cls._warehouse_delivery_mode(warehouse),
            "isMerchant": warehouse != "cn",
            "queryCode": "",
        }

    @classmethod
    def parse_order_record(cls, raw_order):
        base_info = raw_order.get("baseInfo") or {}
        unbox_info = raw_order.get("unBoxInfo") or {}
        feature_map = base_info.get("featureMap") or {}
        order_flags = unbox_info.get("orderDisplayFlags") or []
        return {
            "交易号": base_info.get("tradeId"),
            "履约单号": raw_order.get("orderCode") or base_info.get("orderCode"),
            "B2C分销单号": unbox_info.get("b2cTradeId") or base_info.get("fxTradeId") or feature_map.get("tc_order_id"),
            "订单标识": cls.parse_order_flag_text(order_flags, unbox_info, feature_map),
            "订单标识编码": ",".join(str(flag) for flag in order_flags),
            "下单时间": unbox_info.get("tradeCreateTimeString") or cls._format_timestamp(base_info.get("tradeCreateTime")),
            "系统创建时间": cls._format_timestamp(base_info.get("gmtCreate")),
        }

    @classmethod
    def parse_order_flag_text(cls, order_flags, unbox_info=None, feature_map=None):
        labels = []
        feature_map = feature_map or {}
        for flag in order_flags or []:
            label = cls.ORDER_FLAG_LABELS.get(cls._safe_int(flag))
            if label:
                cls._append_unique(labels, label)

        promotion_flag = cls._safe_int((unbox_info or {}).get("promotionFlag"))
        if promotion_flag in (1, 2):
            cls._append_unique(labels, "活动")

        if cls._safe_int(feature_map.get("presale_flag")) in (1, 2, 3):
            cls._append_unique(labels, "预")
        if str(feature_map.get("ypSample") or "") == "1":
            cls._append_unique(labels, "样机")
        if str(feature_map.get("ypCloudWare") or "") == "1":
            cls._append_unique(labels, "云仓")
        if str(feature_map.get("_F_zfbt_06") or "") == "1":
            cls._append_unique(labels, "国补")
        if feature_map.get("bizFlag") == "qygMkt_erp":
            cls._append_unique(labels, "政企购")
        return "、".join(labels)

    @staticmethod
    def _extract_rows(response_json):
        data = response_json.get("data") or []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("dataSource") or data.get("list") or data.get("rows") or []
        return []

    @staticmethod
    def _warehouse_delivery_mode(warehouse):
        if warehouse in ("cn", "cainiao", "rookie", 0):
            return 0
        if warehouse in ("merchant", "seller", "商家仓", 2):
            return 2
        raise ValueError(f"未知DChain仓库类型: {warehouse}")

    @staticmethod
    def _format_timestamp(value):
        if value in (None, ""):
            return ""
        try:
            timestamp = int(value)
        except (TypeError, ValueError):
            return str(value)
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _safe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _append_unique(items, value):
        if value and value not in items:
            items.append(value)
