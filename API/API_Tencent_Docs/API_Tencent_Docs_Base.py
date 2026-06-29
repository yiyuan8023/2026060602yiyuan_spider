# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-25 18:27:44
- 最近修改：2026-06-25 18:27:44
- 文件用途：封装腾讯文档 docs.qq.com 共享请求能力，统一 Cookie 会话、请求头、JSON 响应解析和安全日志上下文。
- 业务范围：适用于 API_Tencent_Docs 包内页面解析、导出任务创建、进度轮询等腾讯文档接口调用。
- 依赖入口：使用 requests、config.UA、extra.extra_reqlog.req_log。
- 验收方式：执行 py_compile，并通过腾讯文档深圳KA发货明细任务完成页面解析、导出和入库验证。
- 注意事项：不得在日志中输出完整 Cookie、Authorization、签名下载 URL 或敏感请求参数。
"""

import requests

from config import UA
from extra.extra_reqlog import req_log


class TencentDocsBaseApi:
    """Shared request wrapper for docs.qq.com APIs."""

    API_HOST = "https://docs.qq.com"
    DEFAULT_REFERER = "https://docs.qq.com/"

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
                "origin": self.API_HOST,
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
        """Call a Tencent Docs JSON endpoint and return decoded JSON."""
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
            raise RuntimeError(f"腾讯文档请求失败: {context or path}") from exc

        req_log(
            response,
            context=context or f"腾讯文档:{path}",
            raise_error=True,
            log_success=log_success,
        )
        try:
            return response.json()
        except ValueError as exc:
            preview = " ".join((response.text or "")[:200].split())
            raise RuntimeError(f"腾讯文档响应不是JSON: {context or path}: {preview}") from exc

    @classmethod
    def _build_url(cls, path):
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return cls.API_HOST + path
