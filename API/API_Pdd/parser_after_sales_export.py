# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-13 07:46:00
- 最近修改：2026-06-13 07:46:00
- 文件用途：规范化拼多多售后工作台导出 Excel 记录，补充店铺名称并保护售后编号、订单编号、商品ID、运单号等字符串语义。
- 业务范围：适用于 API_Pdd_AfterSalesExport 返回的原始 Excel 记录；不负责网络请求和数据库写入。
- 依赖入口：仅使用标准库，对外暴露 normalize_after_sales_export_records。
- 验收方式：修改后执行 py_compile；用真实售后导出 Excel 样本验证主键字段、金额字段和多行备注字段的清洗结果。
- 注意事项：不要在 parser 中发网络请求；保留平台原始中文字段名，避免下游表结构无谓漂移。
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List


STRING_LIKE_FIELDS = {
    "售后编号",
    "订单编号",
    "商品ID",
    "发货运单号",
    "退货运单号",
}
STRING_LIKE_KEYWORDS = (
    "编号",
    "单号",
    "ID",
    "id",
)


def normalize_after_sales_export_records(
    raw_items: Iterable[Dict[str, Any]],
    *,
    shop_name: str,
) -> List[Dict[str, Any]]:
    """清洗售后导出记录并补充店铺名称。"""
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
