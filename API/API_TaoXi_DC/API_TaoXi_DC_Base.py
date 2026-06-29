# -*- coding: utf-8 -*-
"""DChain supply-chain base API helpers."""

import json
import re

import requests

from config import UA
from extra.extra_reqlog import req_log


class TaoXiDCBaseApi:
    """Shared request wrapper for DChain order APIs."""

    API_HOST = "https://order.cbbs.tmall.com"
    PAGE_REFERER = "https://web.scm.tmall.com/pages/3c/indus_fulfillment_order_manage_config"

    def __init__(self, cookie, page_referer=None):
        self.cookie = cookie
        self.page_referer = page_referer or self.PAGE_REFERER
        self.session = requests.Session()
        self.session.headers.update(
            {
                "user-agent": UA,
                "cookie": cookie,
                "referer": self.page_referer,
                "accept": "application/json, text/plain, */*",
            }
        )

    def request_json(
        self,
        path,
        method="get",
        params=None,
        data=None,
        json_data=None,
        context=None,
        timeout=30,
        log_success=True,
        headers=None,
    ):
        """Call a DChain JSON endpoint and return the decoded response."""
        url = self._build_url(path)
        request_headers = headers or None
        try:
            if method.lower() == "post":
                response = self.session.post(
                    url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers,
                    timeout=timeout,
                )
            else:
                response = self.session.get(url, params=params, headers=request_headers, timeout=timeout)
        except requests.RequestException as exc:
            raise RuntimeError(f"DChain request failed: {context or path}") from exc

        req_log(
            response,
            context=context or f"DChain:{path}",
            raise_error=True,
            log_success=log_success,
        )
        response_json = self._decode_json_response(response, context or path)
        if response_json.get("success") is False:
            message = (
                response_json.get("errorMessage")
                or response_json.get("message")
                or response_json.get("errCode")
                or response_json.get("errorCode")
                or "unknown error"
            )
            raise RuntimeError(f"DChain API failed: {context or path}: {message}")
        return response_json

    @classmethod
    def _build_url(cls, path):
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return cls.API_HOST + path

    @staticmethod
    def _decode_json_response(response, context):
        try:
            return response.json()
        except ValueError as exc:
            preview = " ".join((response.text or "")[:200].split())
            raise RuntimeError(f"DChain response is not JSON: {context}: {preview}") from exc

    @staticmethod
    def compact_json(value):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    def get_scm_token(self):
        """Read the SCM token from the DChain page bootstrap script."""
        response = self.session.get(self.page_referer, timeout=30)
        req_log(response, context="DChain页面Token获取", raise_error=True, log_success=False)
        match = re.search(r"window\._scm_token_\s*=\s*'([^']+)'", response.text or "")
        if not match:
            raise RuntimeError("DChain页面未返回_scm_token_")
        return match.group(1)
