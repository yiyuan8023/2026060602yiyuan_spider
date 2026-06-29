# -*- coding: utf-8 -*-
"""WPS/KDocs document file APIs."""

import io
import re

import requests

from API.API_WPS_Docs.API_WPS_Docs_Base import WpsDocsBaseApi
from downloader.core import Downloader
from downloader.parsers import read_excel_records, validate_excel_sheet_name
from extra.extra_reqlog import req_log
from extra.logger_ import logger


class WpsDocsFileApi(WpsDocsBaseApi):
    """Resolve KDocs shared links and download Excel document content."""

    FILE_ID_PATTERNS = (
        r'"root_file_id"\s*:\s*"([^"]+)"',
        r'"unique_id"\s*:\s*"([^"]+)"',
        r"fileid=([0-9]+)",
    )

    def resolve_file_id(self, document_url):
        """Open the shared document page and extract the real KDocs file id."""
        try:
            response = self.session.get(document_url, timeout=30)
        except requests.RequestException as exc:
            raise RuntimeError("WPS文档页面打开失败") from exc

        req_log(response, context="WPS文档页面打开", raise_error=True, log_success=True)
        for pattern in self.FILE_ID_PATTERNS:
            match = re.search(pattern, response.text or "")
            if match:
                file_id = match.group(1)
                logger.info(f"WPS文档短链解析成功，file_id={file_id}")
                return file_id

        raise RuntimeError("WPS文档页面未解析到 file_id")

    def get_file_info(self, file_id):
        """Read document metadata by file id."""
        response_json = self.request_json(
            f"/api/v3/office/file/{file_id}",
            context="WPS文档文件信息",
        )
        file_info = response_json.get("file") or {}
        if not file_info:
            raise RuntimeError(f"WPS文档文件信息为空，file_id={file_id}")
        return file_info

    def get_download_url(self, file_id):
        """Request a temporary signed file download URL."""
        response_json = self.request_json(
            f"/api/v3/office/file/{file_id}/download",
            context="WPS文档下载地址",
        )
        download_url = response_json.get("download_url") or ""
        if not download_url:
            raise RuntimeError(f"WPS文档未返回下载地址，file_id={file_id}")
        return download_url

    def download_file_bytes(self, file_id):
        """Download the file bytes through the temporary signed URL."""
        download_url = self.get_download_url(file_id)
        content = Downloader(
            api=download_url,
            headers={
                "user-agent": self.session.headers.get("user-agent", ""),
                "referer": self.DEFAULT_REFERER,
            },
            timeout=60,
            context="WPS文档文件下载",
            raise_error=True,
        ).download_file_bytes(validate_excel=True)
        logger.info(f"WPS文档文件下载完成，file_id={file_id}，bytes={len(content)}")
        return content

    def download_excel_records(self, file_id, sheet_name=0):
        """Download the document as Excel and parse the selected sheet."""
        content = self.download_file_bytes(file_id)
        validate_excel_sheet_name(
            io.BytesIO(content),
            sheet_name,
            engine="openpyxl",
            context="WPS文档文件",
        )
        records = read_excel_records(
            io.BytesIO(content),
            sheet_name=sheet_name,
            engine="openpyxl",
            dtype=str,
        )
        return records if isinstance(records, list) else []
