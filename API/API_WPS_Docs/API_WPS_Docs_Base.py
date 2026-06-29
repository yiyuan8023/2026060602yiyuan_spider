# -*- coding: utf-8 -*-
"""WPS/KDocs base API helpers."""

import requests

from config import UA
from extra.extra_reqlog import req_log


class WpsDocsBaseApi:
    """Shared request wrapper for KDocs document APIs."""

    API_HOST = "https://www.kdocs.cn"
    DEFAULT_REFERER = "https://www.kdocs.cn/"

    def __init__(self, cookie, referer=None):
        self.cookie = cookie
        self.referer = referer or self.DEFAULT_REFERER
        self.session = requests.Session()
        self.session.headers.update(
            {
                "user-agent": UA,
                "cookie": cookie,
                "referer": self.referer,
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
        """Call a KDocs JSON endpoint and return decoded JSON."""
        url = self._build_url(path)
        try:
            if method.lower() == "post":
                response = self.session.post(
                    url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=headers,
                    timeout=timeout,
                )
            else:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                )
        except requests.RequestException as exc:
            raise RuntimeError(f"WPS文档请求失败: {context or path}") from exc

        req_log(
            response,
            context=context or f"WPS文档:{path}",
            raise_error=True,
            log_success=log_success,
        )
        try:
            return response.json()
        except ValueError as exc:
            preview = " ".join((response.text or "")[:200].split())
            raise RuntimeError(f"WPS文档响应不是JSON: {context or path}: {preview}") from exc

    @classmethod
    def _build_url(cls, path):
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return cls.API_HOST + path
