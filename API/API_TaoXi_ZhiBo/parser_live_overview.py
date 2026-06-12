# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:05:00
- 最近修改：2026-06-10 21:05:00
- 文件用途：解析淘系直播概览每日分析原始数据，生成中文业务字段、raw_ 原始字段、业务维度和唯一 key。
- 业务范围：适用于直播概览接口 live_overview 返回的 result 明细，字段策略为映射字段加全量原始字段留存。
- 依赖入口：使用 API.API_TaoXi_ZhiBo.cn_en_mapping 和 extra.logger_。
- 验收方式：修改后执行 py_compile 和导入探针；用单店铺、单日期验证新增 raw_ 字段可自动补列入库。
- 注意事项：不得丢弃平台新增字段；纯数字指标转数值，id/key/code/date 等标识字段按文本保留。
"""

from typing import List

from API.API_TaoXi_ZhiBo.API_TaoXi_ZhiBo_Base import cn_en_mapping
from extra.logger_ import logger


TEXT_FIELD_TOKENS = ("id", "key", "code", "编号", "编码", "单号", "账号")
DATE_FIELD_NAMES = {"ds", "统计日期", "日期"}


def normalize_metric_value(value, field_name=None):
    """把直播接口返回的数字字符串转成数值，避免建表时被误判成日期。"""
    if value in {None, ""}:
        return None

    field_text = str(field_name or "").lower()
    if field_name in DATE_FIELD_NAMES or any(token in field_text for token in TEXT_FIELD_TOKENS):
        return str(value)

    if isinstance(value, str):
        stripped_value = value.replace(",", "").strip()
        if stripped_value.endswith("%"):
            percent_value = stripped_value[:-1]
            if percent_value.replace(".", "", 1).isdigit():
                return float(percent_value) / 100
        if stripped_value.replace(".", "", 1).isdigit():
            return float(stripped_value) if "." in stripped_value else int(stripped_value)
    return value


def parse_live_overview_items(raw_items: List[dict]) -> List[dict]:
    """生成中文业务字段，并把平台返回的全部原始字段以 raw_ 前缀留存。"""
    mapping = cn_en_mapping["live_overview"]
    parsed_items = []
    for raw_item in raw_items:
        item = {
            cn_field: normalize_metric_value(raw_item.get(raw_field), cn_field)
            for cn_field, raw_field in mapping.items()
        }

        for raw_field, raw_value in raw_item.items():
            item[f"raw_{raw_field}"] = normalize_metric_value(raw_value, raw_field)

        missing_fields = [raw_field for raw_field in mapping.values() if raw_field not in raw_item]
        if missing_fields:
            logger.info(f"直播概览返回缺少 {len(missing_fields)} 个映射字段，已按空值处理")

        parsed_items.append(item)

    logger.info(f"直播概览接口解析得到 {len(parsed_items)} 条数据")
    return parsed_items


def build_live_overview_items(
    raw_items: List[dict],
    item_shop_name: str,
    stat_day: str,
    item_date_type: str,
) -> List[dict]:
    """补充店铺、日期类型和唯一 key，生成最终入库数据。"""
    items = []
    for item in parse_live_overview_items(raw_items):
        item_stat_day = str(item.get("统计日期") or stat_day).strip()
        if not item_stat_day:
            continue

        item.update(
            {
                "店铺名称": item_shop_name,
                "统计日期": item_stat_day,
                "日期类型": item_date_type,
            }
        )
        item["key"] = f"{item_shop_name}_{item_stat_day}_{item_date_type}"
        items.append(item)
    return items
