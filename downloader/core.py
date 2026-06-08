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

    def _make_request_get(self) -> requests.Response:
        """发送 HTTP GET 请求。"""
        try:
            logger.info(f"GET请求URL: {self._safe_url()}")
            response = requests.get(
                self.url,
                headers=self.default_headers,
                timeout=self.timeout,
            )
            req_log(response, context="Downloader GET")
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
            req_log(response, context="Downloader POST")
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

    def download_file_to_byte(self):
        """下载文件并返回 BytesIO 对象。"""
        try:
            response = self.download_web()
            # 统一返回内存文件对象，供 Excel/CSV/ZIP 解析函数复用。
            return io.BytesIO(response.content)
        except requests.exceptions.RequestException as exc:
            logger.error(f"下载文件失败: {exc}")
            raise
        except Exception as exc:
            logger.error(f"处理下载文件时发生未知错误: {exc}")
            raise

    def download_excel(self, sheet_name=0, skiprows=0, engine=None):  # NOQA
        """下载 Excel 并解析为字典列表。"""
        try:
            data = self.download_file_to_byte()
            return read_excel_records(
                data,
                sheet_name=sheet_name,
                skiprows=skiprows,
                engine=engine,
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
