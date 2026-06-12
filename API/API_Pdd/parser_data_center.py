# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:40:00
- 最近修改：2026-06-10 21:40:00
- 文件用途：解析拼多多数据中心原始响应，完成字体解密、中文字段映射、raw_json_data 原始响应留存、店铺维度和唯一 key 生成。
- 业务范围：适用于拼多多数据中心商品明细、商品概况、商品概况实时数据、交易总览、售后数据和流量看板总览。
- 依赖入口：使用 extra.logger_，由 jobs/拼多多 下任务脚本调用 build_*_items 系列函数。
- 验收方式：修改后执行 py_compile 和导入探针；真实采集时用单店铺单日期验证响应结构、解析行数、raw_json_data 和入库 key。
- 注意事项：不得丢弃平台新增字段；0、0.0、False 不得转成 None；id/key/code/date 类字段按文本保留。
"""

import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from extra.logger_ import logger


RawField = Union[str, Sequence[str]]

TEXT_FIELD_TOKENS = ("id", "key", "code", "编号", "编码", "单号", "账号")
DATE_FIELD_NAMES = {"statDate", "stateDate", "queryDate", "ds", "统计日期", "日期"}
RAW_JSON_FIELD = "raw_json_data"

GOODS_DETAIL_MAPPING: Dict[str, RawField] = {
    "统计日期": "statDate",
    "商品id": "goodsId",
    "商品标题": "goodsName",
    "商品收藏用户数": "goodsFavCnt",
    "商品访客数": "goodsUv",
    "商品浏览量": "goodsPv",
    "成交件数": "payOrdrCnt",
    "成交转化率": "goodsVcr",
    "下单率": "ordrVstrRto",
    "成交订单数": "payOrdrGoodsQty",
    "成交买家数": "payOrdrUsrCnt",
    "成交金额": "payOrdrAmt",
    "流量损失指数": "imprUsrCnt",
}

GOODS_GENERAL_MAPPING: Dict[str, RawField] = {
    "成交金额": "payOrdrAmt",
    "成交订单数": "payOrdrCnt",
    "成交转化率": "payUvRto",
    "商品浏览量": "gpv",
    "商品访客数": "guv",
    "被访问商品数": "vstGoodsCnt",
    "成交买家数": "payOrdrUsrCnt",
    "商品收藏用户数": "goodsFavCnt",
    "统计日期": "statDate",
}

GOODS_REALTIME_MAPPING: Dict[str, RawField] = {
    "成交金额": "payOrdrAmt",
    "成交订单数": "payOrdrCnt",
    "成交转化率": "payUvRto",
    "商品浏览量": "gpv",
    "商品访客数": "guv",
    "被访问商品数": "vstGoodsCnt",
    "成交买家数": "payOrdrUsrCnt",
    "商品收藏用户数": "goodsFavCnt",
    "统计时间": "statHr",
}

TRADE_OVERVIEW_MAPPING: Dict[str, RawField] = {
    "统计日期": ("stateDate", "statDate"),
    "成交金额": "payOrdrAmt",
    "成交订单数": "payOrdrCnt",
    "成交买家数": "payOrdrUsrCnt",
    "客单价": "payOrdrAup",
    "成交转化率": "payUvRto",
    "成交老买家占比": ("rpayUsrRtoDth", "rpayOrdrUsrRto"),
    "店铺关注用户数": "mallFavCnt",
    "退款金额": "sucRfOrdrAmt1d",
    "退款单数": "sucRfOrdrCnt1d",
    "平均访客价值": "uvCfmVal",
}

AFTER_SALES_MAPPING: Dict[str, RawField] = {
    "统计日期": "statDate",
    "纠纷退款数": "dsptRfSucOrdrCnt1m",
    "纠纷退款数类目均值": "stplDsptRfSucOrdrCnt1m",
    "纠纷退款率": "dsptRfSucRto1m",
    "纠纷退款率类目均值": "stplDsptRfSucRto1m",
    "平台介入率": "pltInvlOrdrRto1m",
    "平台介入率类目均值": "stplPltInvlOrdrRto1m",
    "成功退款率": "rfSucRto1m",
    "成功退款率类目均值": "stplRfSucRto1m",
    "平均退款时长": "avgSucRfProcTime1m",
    "同行同层平均退款速度均值": "passSsslAvgSucRfProcTime1m",
    "同行同层平均退款速度优秀值": "bestSsslAvgSucRfProcTime1m",
    "平均退款时长类目均值": "stplAvgSucRfProcTime1m",
    "品质退款率": "qurfOrdRto1m",
    "品质退款率类目均值": "stplQurfOrdRto1m",
    "成功退款金额": "sucRfOrdrAmt1d",
    "成功退款订单数": "sucRfOrdrCnt1d",
    "介入订单数": "pltInvlOrdrCnt1m",
    "退货退款自主完结时长": "avgSlfSucRfProcTime1mMgr",
    "仅退款自主完结时长": "avgSlfSucRfProcTime1mMr",
}

FLOW_OVERVIEW_MAPPING: Dict[str, RawField] = {
    "成交买家数": "cfmOrdrUsrCnt",
    "成交订单数": "cfmOrdrCnt",
    "成交金额": "cfmOrdrAmt",
    "客单价": "cfmOrdrAup",
    "店铺访客数": "uv",
    "店铺浏览量": "pv",
    "商品访客数": "guv",
    "商品浏览量": "gpv",
    "成交转化率": "cfmUvRto",
    "成交UV价值": "uvCfmVal",
}


def decrypt_unicode_string(value: Any, font_mapping: Optional[Mapping[str, str]]) -> Any:
    """按字体映射解密拼多多混淆字符。"""
    if not isinstance(value, str) or not font_mapping:
        return value

    char_to_digit = {}
    for unicode_escape, digit in font_mapping.items():
        try:
            actual_char = unicode_escape.encode().decode("unicode_escape")
            char_to_digit[actual_char] = digit
        except UnicodeDecodeError:
            continue

    return "".join(char_to_digit.get(char, char) for char in value)


def normalize_metric_value(value: Any, field_name: Optional[str] = None) -> Any:
    """把数字字符串转成数值，避免建表时把指标误判为文本或日期。"""
    if value is None:
        return None
    if value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

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


def _first_value(raw_item: Mapping[str, Any], raw_fields: RawField) -> Any:
    if isinstance(raw_fields, str):
        return raw_item.get(raw_fields)
    for raw_field in raw_fields:
        if raw_field in raw_item:
            return raw_item.get(raw_field)
    return None


def _decrypt_raw_item(
    raw_item: Mapping[str, Any],
    font_mapping: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    return {
        raw_field: decrypt_unicode_string(raw_value, font_mapping)
        for raw_field, raw_value in raw_item.items()
    }


def _parse_items(
    raw_items: Iterable[Mapping[str, Any]],
    mapping: Mapping[str, RawField],
    *,
    font_mapping: Optional[Mapping[str, str]] = None,
    context: str,
) -> List[Dict[str, Any]]:
    parsed_items = []
    for raw_item in raw_items:
        decrypted_item = _decrypt_raw_item(raw_item, font_mapping)
        item = {
            cn_field: normalize_metric_value(_first_value(decrypted_item, raw_fields), cn_field)
            for cn_field, raw_fields in mapping.items()
        }

        item[RAW_JSON_FIELD] = json.dumps(decrypted_item, ensure_ascii=False, separators=(",", ":"))

        parsed_items.append(item)

    logger.info(f"{context} 解析得到 {len(parsed_items)} 条数据")
    return parsed_items


def _is_session_expired(response_json: Optional[Mapping[str, Any]]) -> bool:
    if not response_json:
        return False
    return response_json.get("error_msg") == "会话已过期"


def _response_issue(response_json: Optional[Mapping[str, Any]]) -> Optional[str]:
    """区分请求失败、Cookie 过期、平台错误和响应结构异常。"""
    if response_json is None:
        return "请求失败或响应为空"
    if not isinstance(response_json, Mapping):
        return "响应不是 JSON 对象"
    error_msg = response_json.get("error_msg") or response_json.get("errorMsg")
    if error_msg:
        return f"平台错误：{error_msg}"
    if response_json.get("success") is False:
        return "平台返回 success=false"
    return None


def _log_response_issue(response_json: Optional[Mapping[str, Any]], shop_name: str, context: str) -> bool:
    issue = _response_issue(response_json)
    if not issue:
        return False
    if _is_session_expired(response_json):
        logger.error(f"{shop_name} 拼多多 Cookie 已失效，{context} 跳过")
    else:
        logger.warning(f"{shop_name} {context} 响应异常，{issue}")
    return True


def _result_list(
    response_json: Optional[Mapping[str, Any]],
    path: Tuple[str, ...],
    context: str,
) -> List[dict]:
    current_value: Any = response_json or {}
    for key in path:
        if not isinstance(current_value, Mapping):
            logger.warning(f"{context} 响应结构异常，路径 {'/'.join(path)} 中断")
            return []
        current_value = current_value.get(key, [])
    if not isinstance(current_value, list):
        logger.warning(f"{context} 响应结构异常，路径 {'/'.join(path)} 不是列表")
        return []
    return current_value


def _result_dict(
    response_json: Optional[Mapping[str, Any]],
    path: Tuple[str, ...],
    context: str,
) -> Dict[str, Any]:
    current_value: Any = response_json or {}
    for key in path:
        if not isinstance(current_value, Mapping):
            logger.warning(f"{context} 响应结构异常，路径 {'/'.join(path)} 中断")
            return {}
        current_value = current_value.get(key, {})
    if not isinstance(current_value, dict):
        logger.warning(f"{context} 响应结构异常，路径 {'/'.join(path)} 不是对象")
        return {}
    return current_value


def build_goods_detail_items(
    response_json: Optional[Mapping[str, Any]],
    font_mapping: Optional[Mapping[str, str]],
    shop_name: str,
    stat_day: str,
) -> List[Dict[str, Any]]:
    """生成商品明细效果入库数据。"""
    context = "拼多多商品明细效果"
    if _log_response_issue(response_json, shop_name, context):
        return []

    raw_items = _result_list(response_json, ("result", "goodsDetailList"), context)
    items = []
    for item in _parse_items(raw_items, GOODS_DETAIL_MAPPING, font_mapping=font_mapping, context=context):
        item_stat_day = str(item.get("统计日期") or stat_day)
        goods_id = str(item.get("商品id") or "")
        item.update({"店铺名称": shop_name, "统计日期": item_stat_day})
        item["key"] = f"{shop_name}_{goods_id}_{item_stat_day}"
        items.append(item)
    return items


def build_goods_general_items(
    response_json: Optional[Mapping[str, Any]],
    font_mapping: Optional[Mapping[str, str]],
    shop_name: str,
    default_stat_day: str,
) -> List[Dict[str, Any]]:
    """生成商品概况入库数据。"""
    context = "拼多多商品概况"
    if _log_response_issue(response_json, shop_name, context):
        return []

    raw_items = _result_list(response_json, ("result",), context)
    items = []
    for item in _parse_items(raw_items, GOODS_GENERAL_MAPPING, font_mapping=font_mapping, context=context):
        item_stat_day = str(item.get("统计日期") or default_stat_day)
        item.update({"店铺名称": shop_name, "统计日期": item_stat_day})
        item["key"] = f"{shop_name}_{item_stat_day}"
        items.append(item)
    return items


def build_goods_realtime_items(
    response_json: Optional[Mapping[str, Any]],
    shop_name: str,
    stat_day: str,
) -> List[Dict[str, Any]]:
    """生成商品概况实时数据入库数据。"""
    context = "拼多多商品概况实时数据"
    if _log_response_issue(response_json, shop_name, context):
        return []

    raw_items = _result_list(response_json, ("result", "todayList"), context)
    items = []
    for item in _parse_items(raw_items, GOODS_REALTIME_MAPPING, context=context):
        stat_hour = str(item.get("统计时间") or "")
        item.update({"店铺名称": shop_name, "统计日期": stat_day})
        item["key"] = f"{shop_name}_{stat_day}_{stat_hour}"
        items.append(item)
    return items


def build_trade_overview_items(
    response_json: Optional[Mapping[str, Any]],
    font_mapping: Optional[Mapping[str, str]],
    shop_name: str,
) -> List[Dict[str, Any]]:
    """生成交易数据总览入库数据。"""
    context = "拼多多交易数据总览"
    if _log_response_issue(response_json, shop_name, context):
        return []

    raw_items = _result_list(response_json, ("result", "dayList"), context)
    items = []
    for item in _parse_items(raw_items, TRADE_OVERVIEW_MAPPING, font_mapping=font_mapping, context=context):
        item_stat_day = str(item.get("统计日期") or "")
        if not item_stat_day:
            continue
        item.update({"店铺名称": shop_name, "统计日期": item_stat_day})
        item["key"] = f"{shop_name}_{item_stat_day}"
        items.append(item)
    return items


def build_after_sales_items(
    response_json: Optional[Mapping[str, Any]],
    shop_name: str,
    stat_day: str,
) -> List[Dict[str, Any]]:
    """生成售后数据入库数据。"""
    context = "拼多多服务售后数据"
    if _log_response_issue(response_json, shop_name, context):
        return []

    raw_item = _result_dict(response_json, ("result",), context)
    if not raw_item:
        logger.warning(f"{context} 原始结果为空")
        return []

    item = _parse_items([raw_item], AFTER_SALES_MAPPING, context=context)[0]
    item_stat_day = str(item.get("统计日期") or stat_day)
    item.update({"店铺名称": shop_name, "统计日期": item_stat_day})
    item["key"] = f"{shop_name}_{item_stat_day}"
    return [item]


def build_flow_overview_items(
    response_json: Optional[Mapping[str, Any]],
    shop_name: str,
    stat_day: str,
) -> List[Dict[str, Any]]:
    """生成流量看板数据总览入库数据。"""
    context = "拼多多流量看板数据总览"
    if _log_response_issue(response_json, shop_name, context):
        return []

    raw_item = _result_dict(response_json, ("result",), context)
    if not raw_item:
        logger.warning(f"{context} 原始结果为空")
        return []

    item = _parse_items([raw_item], FLOW_OVERVIEW_MAPPING, context=context)[0]
    item.update({"店铺名称": shop_name, "统计日期": stat_day})
    item["key"] = f"{shop_name}_{stat_day}"
    return [item]
