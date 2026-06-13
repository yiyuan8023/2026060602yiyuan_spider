# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 23:40:00
- 最近修改：2026-06-12 23:40:00
- 文件用途：规范化拼多多订单导出 CSV 记录，补充店铺名称并尽量保护订单号、商品 ID、编码类字段的字符串语义。
- 业务范围：适用于 API_Pdd_OrderListExport 返回的原始 CSV 记录；不负责网络请求和数据库写入。
- 依赖入口：仅使用标准库，对外暴露 normalize_order_export_records。
- 验收方式：修改后执行 py_compile；用真实导出 CSV 记录探针验证订单号、商品id、样式ID、编码字段和值为空时的清洗结果。
- 注意事项：不要在 parser 中发网络请求；保留平台原始字段名，避免下游表结构无谓漂移。
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List


STRING_LIKE_FIELDS = {
    "订单号",
    "商品id",
    "赠品id",
    "样式ID",
    "团ID",
    "赠品订单号",
    "快递单号",
    "支付ID",
    "海淘清关订单号",
    "用户购买手机号",
    "配送员手机号",
    "充值号码",
}
STRING_LIKE_KEYWORDS = (
    "编码",
    "ID",
    "id",
)


def normalize_order_export_records(
    raw_items: Iterable[Dict[str, Any]],
    *,
    shop_name: str,
) -> List[Dict[str, Any]]:
    """清洗导出记录并补充店铺名称。"""
    normalized_items: List[Dict[str, Any]] = []
    for raw_item in raw_items:
        normalized_item: Dict[str, Any] = {}
        for field_name, raw_value in raw_item.items():
            normalized_item[field_name] = _normalize_field_value(field_name, raw_value)
        normalized_item["店铺名称"] = shop_name
        normalized_items.append(normalized_item)
    return normalized_items


def _normalize_field_value(field_name: str, raw_value: Any) -> Any:
    if raw_value is None:
        return ""

    if isinstance(raw_value, float) and math.isnan(raw_value):
        return ""

    if _is_string_like_field(field_name):
        return _stringify_identifier(raw_value)

    if isinstance(raw_value, str):
        cleaned = raw_value.replace("\ufeff", "").strip()
        if cleaned == "\t":
            return ""
        return cleaned

    return raw_value


def _is_string_like_field(field_name: str) -> bool:
    if field_name in STRING_LIKE_FIELDS:
        return True
    return any(keyword in field_name for keyword in STRING_LIKE_KEYWORDS)


def _stringify_identifier(raw_value: Any) -> str:
    if raw_value is None:
        return ""
    if isinstance(raw_value, str):
        return raw_value.replace("\ufeff", "").strip()
    if isinstance(raw_value, bool):
        return str(raw_value)
    if isinstance(raw_value, int):
        return str(raw_value)
    if isinstance(raw_value, float):
        if math.isnan(raw_value):
            return ""
        if raw_value.is_integer():
            return str(int(raw_value))
        return format(raw_value, "f").rstrip("0").rstrip(".")
    return str(raw_value).strip()
