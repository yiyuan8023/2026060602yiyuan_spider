# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 18:21:46
- 最近修改：2026-06-12 18:21:46
- 文件用途：封装千牛商家工作台价保管理接口，负责价保记录分页查询和价保明细导出 URL 获取。
- 业务范围：适用于 https://qn.taobao.com/home.htm/price-center-manager 页面下的价保记录查询与下载明细能力。
- 依赖入口：继承 TaoXiGongZuoTaiBaseApi，使用 downloader.core.Downloader 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、单日期验证列表状态码、分页总数、字段解析和下载 URL 返回。
- 注意事项：接口依赖 Cookie 中的 _tb_token_；API 层不写库、不保存 Cookie；日志不得输出完整 Cookie、签名 URL 或敏感请求参数。
"""

import json
import re
from urllib.parse import quote, urlsplit, urlunsplit

from API.API_TaoXi_GongZuoTai.API_TaoXi_GongZuoTai_Base import (
    TaoXiGongZuoTaiBaseApi,
)
from API.API_TaoXi_GongZuoTai.parser_price_protection import (
    build_price_protection_export_records,
)
from API.API_TaoXi_GongZuoTai.price_protection_cookie_cache import (
    merge_cookie_texts,
    warmup_price_center_cookie,
)
from downloader.core import Downloader
from extra.extra_error import handle_request_error
from extra.logger_ import logger


class TaoXiGongZuoTaiPriceProtectionApi(TaoXiGongZuoTaiBaseApi):
    """千牛价保管理 API，负责价保赔付记录查询和导出。"""

    PRICE_CENTER_REFERER = "https://qn.taobao.com/home.htm/price-center-manager"
    BASE_API = "https://mk.ju.taobao.com"
    RECORD_LIST_API = "/priceprotection/record_list.do"
    DATA_EXPORT_API = "/priceprotection/data_export.do"
    DEFAULT_PAGE_SIZE = 100
    EXPORT_URL_KEYS = ("model", "downloadUrl", "filePath", "url")

    def __init__(self, cookie, shop_name=None, extra_cookie=None):
        merged_cookie = merge_cookie_texts(cookie, extra_cookie)
        super().__init__(merged_cookie or cookie)
        self.shop_name = shop_name
        self.source_cookie = cookie or ""
        self.extra_cookie = extra_cookie or ""

    def _get_tb_token(self):
        match = re.search(r"(?:^|;\s*)_tb_token_=([^;]+)", self.cookie or "")
        if not match:
            raise RuntimeError("千牛价保接口缺少 _tb_token_ Cookie")
        return match.group(1)

    @staticmethod
    def _clean_params(params):
        return {
            key: value
            for key, value in (params or {}).items()
            if value not in (None, "")
        }

    @staticmethod
    def _safe_response_preview(text, limit=200):
        compact_text = " ".join((text or "").split())

        def _strip_url_query(match):
            raw_url = match.group(0)
            parts = urlsplit(raw_url)
            if not parts.scheme or not parts.netloc:
                return raw_url[:limit]
            return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

        compact_text = re.sub(r"https?://[^\s'\"<>]+", _strip_url_query, compact_text)
        return compact_text[:limit]

    @staticmethod
    def _parse_json_body(response_text):
        text = (response_text or "").strip()
        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        jsonp_match = re.search(r"[\w$]+\((.*)\)\s*;?\s*$", text, re.S)
        if not jsonp_match:
            return None

        try:
            return json.loads(jsonp_match.group(1))
        except json.JSONDecodeError:
            return None

    @classmethod
    def _extract_download_url_from_body(cls, response_text):
        response_json = cls._parse_json_body(response_text)
        if isinstance(response_json, dict):
            result_code = str(response_json.get("resultCode") or "")
            legacy_code = str(response_json.get("code") or "")
            success_flag = response_json.get("success")
            if result_code and result_code != "200":
                raise RuntimeError(
                    f"千牛价保接口返回异常: {response_json.get('msg') or result_code or 'unknown'}"
                )
            if legacy_code and legacy_code not in ("200", "0"):
                raise RuntimeError(
                    f"千牛价保接口返回异常: {response_json.get('message') or response_json.get('msg') or legacy_code}"
                )
            if success_flag is False:
                raise RuntimeError(
                    f"千牛价保接口返回异常: {response_json.get('message') or response_json.get('msg') or 'success=false'}"
                )

            for key in cls.EXPORT_URL_KEYS:
                value = response_json.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
                if isinstance(value, dict):
                    for nested_key in cls.EXPORT_URL_KEYS:
                        nested_value = value.get(nested_key)
                        if isinstance(nested_value, str) and nested_value.strip():
                            return nested_value.strip()
            return None

        text = (response_text or "").strip()
        if not text:
            return None

        quoted_match = re.search(r"""['"]\s*(https?://[^'"]+)\s*['"]""", text)
        if quoted_match:
            return quoted_match.group(1).strip()

        direct_url_match = re.search(r"https?://[^\s'\"<>]+", text)
        if direct_url_match:
            return direct_url_match.group(0).strip()

        if text.startswith(("http://", "https://")):
            return text.splitlines()[0].strip()
        return None

    @staticmethod
    def _should_retry_with_fresh_cookie(error):
        error_text = str(error)
        return "请您登陆之后再访问" in error_text or "缺少 _tb_token_" in error_text

    @staticmethod
    def _is_blocked_download_url(download_url):
        parts = urlsplit(download_url or "")
        return (
            parts.netloc.lower() in {"login.taobao.com", "error.taobao.com", "err.taobao.com"}
            or "logout" in parts.path.lower()
        )

    def ensure_runtime_cookie(self, force_refresh=False):
        """优先使用本地缓存 Cookie，失效后再用数据库 Cookie 打开价保页补齐会话。"""
        self.cookie = warmup_price_center_cookie(
            shop_name=self.shop_name or "price_protection_default",
            source_cookie=self.source_cookie,
            extra_cookie=self.extra_cookie,
            price_center_url=self.PRICE_CENTER_REFERER,
            user_agent=self.ua,
            force_refresh=force_refresh,
        )
        return self.cookie

    def price_protection_request(self, api_path, params=None, log_success=True):
        """请求 mk.ju.taobao.com 价保接口，自动补 _tb_token_。"""
        self.ensure_runtime_cookie()
        request_params = self._clean_params(params)
        request_params["_tb_token_"] = self._get_tb_token()
        response = Downloader(
            api=f"{self.BASE_API}{api_path}",
            cookie=self.cookie,
            params=request_params,
            headers={"referer": self.PRICE_CENTER_REFERER},
            timeout=30,
            context=f"千牛价保:{api_path}",
            raise_error=True,
            log_success=log_success,
        ).download_web()

        response_json = response.json()
        result_code = str(response_json.get("resultCode") or "")
        if result_code != "200":
            raise RuntimeError(
                f"千牛价保接口返回异常: {response_json.get('msg') or result_code or 'unknown'}"
            )
        return response_json

    @staticmethod
    def _build_record_params(
        page_index=1,
        page_size=DEFAULT_PAGE_SIZE,
        tab=4,
        apply_min_time=None,
        apply_max_time=None,
        main_order_id=None,
        order_id=None,
        item_id=None,
        sku_id=None,
        user_nick=None,
        item_title=None,
        min_refund_fee=None,
        max_refund_fee=None,
    ):
        params = {
            "tab": tab,
            "pageIndex": page_index,
            "pageSize": page_size,
            "applyMinTime": apply_min_time,
            "applyMaxTime": apply_max_time,
            "mainOrderId": main_order_id,
            "orderId": order_id,
            "itemId": item_id,
            "skuId": sku_id,
            "userNick": quote(user_nick) if user_nick else None,
            "itemTitle": quote(item_title) if item_title else None,
            "minRefundFee": min_refund_fee,
            "maxRefundFee": max_refund_fee,
        }
        return TaoXiGongZuoTaiPriceProtectionApi._clean_params(params)

    def list_price_protection_records(
        self,
        page_index=1,
        page_size=DEFAULT_PAGE_SIZE,
        tab=4,
        apply_min_time=None,
        apply_max_time=None,
        main_order_id=None,
        order_id=None,
        item_id=None,
        sku_id=None,
        user_nick=None,
        item_title=None,
        min_refund_fee=None,
        max_refund_fee=None,
        log_success=True,
    ):
        """查询价保记录单页原始数据，tab=4 为全部状态，tab=2 为价保成功。"""
        params = self._build_record_params(
            page_index=page_index,
            page_size=page_size,
            tab=tab,
            apply_min_time=apply_min_time,
            apply_max_time=apply_max_time,
            main_order_id=main_order_id,
            order_id=order_id,
            item_id=item_id,
            sku_id=sku_id,
            user_nick=user_nick,
            item_title=item_title,
            min_refund_fee=min_refund_fee,
            max_refund_fee=max_refund_fee,
        )
        return self.price_protection_request(
            self.RECORD_LIST_API,
            params,
            log_success=log_success,
        )

    def list_all_price_protection_records(
        self,
        page_size=DEFAULT_PAGE_SIZE,
        max_pages=None,
        **filters,
    ):
        """按筛选条件分页拉取全部价保记录原始数据。"""
        all_records = []
        page_index = 1
        total_num = None
        while True:
            response_json = self.list_price_protection_records(
                page_index=page_index,
                page_size=page_size,
                log_success=page_index == 1,
                **filters,
            )
            records = response_json.get("model") or []
            total_num = response_json.get("totalNum") if total_num is None else total_num
            all_records.extend(records)
            logger.info(
                f"千牛价保记录分页完成 page={page_index}, page_size={page_size}, "
                f"本页={len(records)}, 累计={len(all_records)}, total={total_num}"
            )

            if max_pages and page_index >= max_pages:
                break
            if not records or len(records) < page_size:
                break
            if total_num is not None and page_index * page_size >= int(total_num):
                break
            page_index += 1
        return all_records

    def export_price_protection_records(self, **filters):
        """获取平台“下载明细”的导出文件 URL，调用前应传入至少一个筛选条件。"""
        params = self._build_record_params(**filters)
        for attempt_index in range(2):
            try:
                self.ensure_runtime_cookie(force_refresh=attempt_index == 1)
                request_params = self._clean_params(params)
                request_params["_tb_token_"] = self._get_tb_token()
                response = Downloader(
                    api=f"{self.BASE_API}{self.DATA_EXPORT_API}",
                    cookie=self.cookie,
                    params=request_params,
                    headers={"referer": self.PRICE_CENTER_REFERER},
                    timeout=30,
                    context=f"千牛价保:{self.DATA_EXPORT_API}",
                    raise_error=True,
                ).download_web()
                download_url = self._extract_download_url_from_body(response.text)
                if download_url:
                    if self._is_blocked_download_url(download_url):
                        raise RuntimeError(f"千牛价保明细导出返回异常下载地址: {download_url}")
                    logger.info("千牛价保明细导出已获取下载地址")
                    return download_url

                logger.warning(
                    f"千牛价保明细导出返回未识别格式: {self._safe_response_preview(response.text)}"
                )
                return None
            except Exception as exc:
                if attempt_index == 0 and self._should_retry_with_fresh_cookie(exc):
                    logger.warning(f"{self.shop_name} 价保导出首次失败，尝试强制刷新页面 Cookie 后重试")
                    continue
                return handle_request_error(exc, context="千牛价保明细导出") or None
        return None

    def download_export_price_protection_records(self, **filters):
        """下载并解析价保订单赔付详情导出 Excel。"""
        download_url = self.export_price_protection_records(**filters)
        if not download_url:
            logger.warning("千牛价保明细导出未返回下载地址")
            return []

        try:
            self.ensure_runtime_cookie()
            excel_content = Downloader(
                api=download_url,
                cookie=self.cookie,
                timeout=60,
                context="千牛价保明细下载",
            ).download_file_to_byte(validate_excel=True)
            return build_price_protection_export_records(excel_content)
        except Exception as exc:
            return handle_request_error(exc, context="千牛价保明细下载") or []
