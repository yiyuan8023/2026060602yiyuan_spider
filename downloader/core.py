"""
开发说明：
- 作者：一元
- 创建时间：2026-06-08 10:39:40
- 最近修改：2026-06-10 22:08:17
- 文件用途：提供项目统一 HTTP 下载入口，封装网页请求、请求日志、文件下载、Excel/CSV/ZIP 解析和下载内容基础校验。
- 业务范围：适用于 API 模块和任务脚本中普通 HTTP 请求、平台导出文件下载及通用文件解析。
- 依赖入口：使用 requests、config.UA、extra.extra_reqlog.req_log、extra.logger_、downloader.encoding 和 downloader.parsers。
- 验收方式：修改后执行 py_compile；通过导入探针和最小 Response 样本验证请求日志参数与 Excel 响应校验逻辑。
- 注意事项：日志只记录安全 URL 主体，不输出 Cookie、签名 URL、授权参数或完整错误响应内容。
"""

import io
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode, urlsplit, urlunsplit

import requests

from config import UA
from extra.extra_reqlog import req_log
from extra.logger_ import logger

from .encoding import detect_text_encoding
from .parsers import read_csv_records, read_excel_records, read_zip_records


class Downloader:
    """项目统一下载入口，负责普通 HTTP 请求和导出文件解析。"""

    def __init__(
        self,
        api: str,
        method: str = "get",
        cookie: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict, str, bytes]] = None,
        json_data: Optional[Dict] = None,
        timeout: int = 30,
        context: Optional[str] = None,
        log_response: bool = True,
        raise_error: bool = False,
        log_success: bool = True,
    ):
        self.api = api
        self.method = method.lower()
        self.cookie = cookie
        self.params = params or {}
        self.headers = headers or {}
        self.url = self._build_url()
        self.default_headers = self._prepare_headers()
        self.timeout = timeout
        self.json_data = json_data
        self.data = data or {}
        self.context = context
        self.log_response = log_response
        self.raise_error = raise_error
        self.log_success = log_success

    def _build_url(self):
        """构造完整 URL。"""
        if self.params:
            separator = "&" if "?" in self.api else "?"
            return f"{self.api}{separator}{urlencode(self.params, doseq=True)}"
        return self.api

    def _prepare_headers(self):
        """合并默认请求头和调用方传入的请求头。"""
        default_headers = {"User-Agent": UA}
        # cookie 只有在调用方明确传入时才放入请求头，避免写入空 cookie。
        if self.cookie:
            default_headers["cookie"] = self.cookie
        if self.headers:
            default_headers.update(self.headers)
        return default_headers

    def _safe_url(self):
        """日志里只保留 URL 主体，避免 signed URL 或查询参数外泄。"""
        parts = urlsplit(self.url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    def _log_response(self, response: requests.Response, method: str):
        if self.log_response:
            req_log(
                response,
                context=self.context or f"Downloader {method}",
                raise_error=self.raise_error,
                log_success=self.log_success,
            )

    def _make_request_get(self) -> requests.Response:
        """发送 HTTP GET 请求。"""
        try:
            logger.info(f"GET请求URL: {self._safe_url()}")
            response = requests.get(
                self.url,
                headers=self.default_headers,
                timeout=self.timeout,
            )
            self._log_response(response, "GET")
            return response
        except requests.exceptions.RequestException as exc:
            logger.error(f"GET网络请求失败: {exc}")
            raise
        except Exception as exc:
            logger.error(f"发送GET请求时发生未知错误: {exc}")
            raise

    def _make_request_post(self) -> requests.Response:
        """发送 HTTP POST 请求。"""
        try:
            logger.info(f"POST请求URL: {self._safe_url()}")
            # json_data 和 data 二选一，避免调用方在业务层重复封装 POST 分支。
            if self.json_data is not None:
                response = requests.post(
                    self.url,
                    json=self.json_data,
                    headers=self.default_headers,
                    timeout=self.timeout,
                )
            else:
                response = requests.post(
                    self.url,
                    data=self.data,
                    headers=self.default_headers,
                    timeout=self.timeout,
                )
            self._log_response(response, "POST")
            return response
        except requests.exceptions.RequestException as exc:
            logger.error(f"POST网络请求失败: {exc}")
            raise
        except Exception as exc:
            logger.error(f"发送POST请求时发生未知错误: {exc}")
            raise

    def download_web(self):
        """下载网页内容并返回 Response。"""
        if self.method == "post":
            return self._make_request_post()
        if self.method == "get":
            return self._make_request_get()
        raise ValueError(f"不支持的请求方式: {self.method}")

    @staticmethod
    def _looks_like_excel(content: bytes):
        """用文件头识别常见 xlsx/xls，避免把 JSON/HTML 错误页交给 Excel 解析。"""
        return content.startswith(b"PK\x03\x04") or content.startswith(b"\xd0\xcf\x11\xe0")

    @staticmethod
    def _safe_content_preview(content: bytes, limit=200):
        preview = content[:limit].decode("utf-8", errors="replace")
        return " ".join(preview.split())

    def _validate_excel_response(self, response: requests.Response):
        content = response.content or b""
        content_type = response.headers.get("Content-Type", "").lower()
        content_disposition = response.headers.get("Content-Disposition", "").lower()
        sample = content[:64].lstrip().lower()
        header_indicates_excel = (
            "excel" in content_type
            or "spreadsheet" in content_type
            or "application/octet-stream" in content_type
            or ".xls" in content_disposition
        )

        if sample.startswith((b"{", b"[")):
            raise ValueError(
                f"下载结果不是Excel，疑似JSON错误响应: {self._safe_content_preview(content)}"
            )
        if sample.startswith(b"<") and not header_indicates_excel:
            raise ValueError(
                f"下载结果不是Excel，疑似HTML错误页: {self._safe_content_preview(content)}"
            )
        if not content:
            raise ValueError("下载结果为空，无法解析为Excel")
        if not self._looks_like_excel(content) and not header_indicates_excel:
            raise ValueError(
                f"下载结果不是可识别Excel，content_type={content_type or 'unknown'}"
            )

    def download_file_to_byte(self, validate_excel=False):
        """下载文件并返回 BytesIO 对象。"""
        try:
            response = self.download_web()
            if validate_excel:
                self._validate_excel_response(response)
            # 统一返回内存文件对象，供 Excel/CSV/ZIP 解析函数复用。
            return io.BytesIO(response.content)
        except requests.exceptions.RequestException as exc:
            logger.error(f"下载文件失败: {exc}")
            raise
        except Exception as exc:
            logger.error(f"处理下载文件时发生未知错误: {exc}")
            raise

    def download_excel(  # NOQA
        self,
        sheet_name=0,
        skiprows=0,
        engine=None,
        validate_excel=False,
        **read_kwargs,
    ):
        """下载 Excel 并解析为字典列表。"""
        try:
            data = self.download_file_to_byte(validate_excel=validate_excel)
            # dtype 等读取细节留给调用方传入，但下载和解析入口仍统一在 downloader。
            return read_excel_records(
                data,
                sheet_name=sheet_name,
                skiprows=skiprows,
                engine=engine,
                **read_kwargs,
            )
        except Exception as exc:
            logger.error(f"处理Excel文件时发生未知错误: {exc}")
            raise

    def download_csv(self):
        """下载 CSV 并解析为字典列表。"""
        try:
            return read_csv_records(self.download_file_to_byte())
        except Exception as exc:
            logger.error(f"处理CSV文件时发生未知错误: {exc}")
            raise

    @staticmethod
    def file_encoding(file_content):
        """检测文件内容编码。"""
        return detect_text_encoding(file_content)

    def download_zip(self, file_type="csv"):
        """下载 ZIP 并读取其中第一个 CSV 或 Excel 文件。"""
        try:
            response = self.download_web()
            return read_zip_records(response.content, file_type=file_type)
        except Exception as exc:
            logger.error(f"处理ZIP文件时发生未知错误: {exc}")
            raise
