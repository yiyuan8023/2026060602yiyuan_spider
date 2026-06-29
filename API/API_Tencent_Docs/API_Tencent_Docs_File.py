# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-25 18:27:44
- 最近修改：2026-06-25 18:45:00
- 文件用途：解析腾讯文档在线表格页面元信息，创建 Excel 导出任务，轮询导出进度并下载导出文件。
- 业务范围：适用于 docs.qq.com/sheet 在线表格的 Cookie 鉴权导出，当前用于深圳KA壁挂炉发货明细。
- 依赖入口：使用 TencentDocsBaseApi、downloader.core.Downloader、downloader.parsers.read_excel_records、extra.extra_reqlog.req_log、extra.logger_。
- 验收方式：执行 py_compile；通过单文档导出探针验证 title、domain_id、pad_id、Sheet 表头和解析行数。
- 注意事项：导出 file_url 为签名地址，只在内存中传递，不得写入日志、代码、注释或提交内容。
"""

import base64
import io
import json
import re
import time
from http.cookies import SimpleCookie
from urllib.parse import urlparse

import requests

from API.API_Tencent_Docs.API_Tencent_Docs_Base import TencentDocsBaseApi
from downloader.core import Downloader
from downloader.parsers import read_excel_records, validate_excel_sheet_name
from extra.extra_reqlog import req_log
from extra.logger_ import logger


class TencentDocsFileApi(TencentDocsBaseApi):
    """Resolve Tencent Docs sheet pages and download exported Excel content."""

    CLIENT_VARS_PATTERN = re.compile(
        r"window\.basicClientVars\s*=\s*JSON\.parse\(decodeURIComponent\(escape\(atob\('([^']+)'\)\)\)\)"
    )

    def resolve_document_info(self, document_url):
        """Open the shared sheet page and extract export-ready document metadata."""
        try:
            response = self.session.get(
                document_url,
                headers={"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError("腾讯文档页面打开失败") from exc

        req_log(response, context="腾讯文档页面打开", raise_error=True, log_success=True)
        response_text = response.text or ""
        client_vars = self._decode_basic_client_vars(response_text)
        doc_info = client_vars.get("docInfo") or {}
        pad_info = doc_info.get("padInfo") or {}
        auth_info = client_vars.get("authInfo") or {}
        user_info = client_vars.get("userInfo") or {}

        domain_id = str(pad_info.get("domainId") or "")
        pad_id = str(pad_info.get("padId") or "")
        if not domain_id or not pad_id:
            raise RuntimeError("腾讯文档页面未解析到 domainId/padId")

        attribute = auth_info.get("attribute") or {}
        if attribute and not attribute.get("canExport", False):
            raise RuntimeError("腾讯文档当前账号没有导出权限")

        file_info = {
            "domain_id": domain_id,
            "pad_id": pad_id,
            "local_pad_id": f"{domain_id}${pad_id}",
            "title": str(pad_info.get("padTitle") or ""),
            "pad_type": str(pad_info.get("padType") or ""),
            "share_link": str(doc_info.get("shareLink") or self._strip_query(document_url)),
            "uid": self._get_cookie_value("uid") or str(user_info.get("tinyId") or ""),
            "user_id": str(user_info.get("userId") or ""),
            "can_export": attribute.get("canExport"),
        }
        logger.info(
            f"腾讯文档页面解析成功，title={file_info['title']}，"
            f"domain_id={file_info['domain_id']}，pad_id={file_info['pad_id']}"
        )
        return file_info

    def download_excel_records(self, file_info, sheet_name=0):
        """Export the online sheet as Excel and parse the selected sheet."""
        content = self.download_file_bytes(file_info)
        validate_excel_sheet_name(
            io.BytesIO(content),
            sheet_name,
            engine="openpyxl",
            context="腾讯文档导出文件",
        )
        records = read_excel_records(
            io.BytesIO(content),
            sheet_name=sheet_name,
            engine="openpyxl",
            dtype=str,
        )
        return records if isinstance(records, list) else []

    def download_file_bytes(self, file_info):
        """Create an export task, poll until ready, and download Excel bytes."""
        user_index = file_info.get("uid") or self._get_cookie_value("uid")
        local_pad_id = file_info.get("local_pad_id")
        if not user_index or not local_pad_id:
            raise RuntimeError("腾讯文档导出缺少 uid 或 local_pad_id")

        operation_id = self.create_export_task(user_index, local_pad_id)
        file_url = self.query_export_file_url(user_index, operation_id)
        content = Downloader(
            api=file_url,
            headers={
                "user-agent": self.session.headers.get("user-agent", ""),
                "referer": self.referer,
            },
            timeout=60,
            context="腾讯文档导出文件下载",
            raise_error=True,
        ).download_file_bytes(validate_excel=True)
        logger.info(
            f"腾讯文档导出文件下载完成，title={file_info.get('title')}，bytes={len(content)}"
        )
        return content

    def create_export_task(self, user_index, local_pad_id):
        """Create a Tencent Docs export task and return operationId."""
        response_json = self.request_json(
            "/v1/export/export_office",
            method="post",
            params={"u": user_index},
            data={
                "docId": local_pad_id,
                "version": "2",
                "exportSource": "client",
            },
            context="腾讯文档创建导出任务",
        )
        if response_json.get("ret") not in (0, "0", None):
            raise RuntimeError(f"腾讯文档创建导出任务失败: ret={response_json.get('ret')}")
        operation_id = response_json.get("operationId")
        if not operation_id:
            raise RuntimeError("腾讯文档创建导出任务未返回 operationId")
        logger.info("腾讯文档创建导出任务成功")
        return operation_id

    def query_export_file_url(self, user_index, operation_id, timeout=60, interval=1):
        """Poll export progress and return the signed file URL without logging it."""
        start_time = time.time()
        while time.time() - start_time <= timeout:
            response_json = self.request_json(
                "/v1/export/query_progress",
                params={"u": user_index, "operationId": operation_id},
                context="腾讯文档导出进度",
                log_success=False,
            )
            progress = response_json.get("progress")
            if progress == 100 and response_json.get("file_url"):
                logger.info("腾讯文档导出任务已完成")
                return response_json["file_url"]
            time.sleep(interval)
        raise TimeoutError("腾讯文档导出任务超时")

    def _decode_basic_client_vars(self, response_text):
        match = self.CLIENT_VARS_PATTERN.search(response_text)
        if not match:
            raise RuntimeError("腾讯文档页面未解析到 basicClientVars")
        try:
            decoded = base64.b64decode(match.group(1)).decode("utf-8")
            return json.loads(decoded)
        except (ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("腾讯文档 basicClientVars 解析失败") from exc

    def _get_cookie_value(self, name):
        cookies = SimpleCookie()
        cookies.load(self.cookie or "")
        morsel = cookies.get(name)
        return morsel.value if morsel else ""

    @staticmethod
    def _strip_query(document_url):
        parsed = urlparse(document_url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
