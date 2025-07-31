import io
import requests
from urllib.parse import urlencode

from extra_reqlog import req_log
from logger_ import logger
from settings import UA


class Downloader:
    """
    通用的文件下载器
    """

    def __init__(self, cookie):
        self.cookie = cookie

    @staticmethod
    def _build_url(api, params=None):
        """
        构造完整的URL
        Args:
            base_url (str): 基础URL
            params (dict, optional): URL参数
        Returns:
            str: 完整的URL
        """
        if params:
            url = api + urlencode(params)
        else:
            url = api
        return url

    def _prepare_headers(self, headers=None):
        """
        准备请求头
        Args:
            headers (dict, optional): 额外的请求头
        Returns:
            dict: 合并后的请求头
        """
        # 设置默认请求头
        default_headers = {
            "User-Agent": UA,
            "cookie": self.cookie
        }
        # 合并自定义请求头
        if headers:
            default_headers.update(headers)
        return default_headers

    @staticmethod
    def _log_request(url, status_code):
        """
        记录请求日志
        Args:
            url (str): 请求URL
            status_code (int): 响应状态码
        """
        if logger:
            logger.info(f"请求URL: {url}")
            logger.info(f"响应状态码: {status_code}")

    def download_excel(self, api, params=None, headers=None):
        """
        下载Excel文件并返回BytesIO对象
        Args:
            api (str): API基础URL
            params (dict): 请求参数
            headers (dict, optional): 额外的请求头
        Returns:
            io.BytesIO: 包含Excel数据的BytesIO对象
        """
        try:
            url = self._build_url(api, params)
            logger.info(url)# 构造完整URL
            request_headers = self._prepare_headers(headers) # 设置请求头
            res = requests.get(url, headers=request_headers) # 发送请求
            req_log(res)

            return io.BytesIO(res.content) # 将HTTP响应的二进制内容转换为内存中的文件对象(BytesIO对象)
        except requests.exceptions.RequestException as e:
            logger.error(f"下载Excel文件失败: {e}")
            raise  # 重新抛出异常，让调用方处理
        except Exception as e:
            logger.error(f"处理Excel文件时发生未知错误: {e}")
            raise  # 重新抛出异常，让调用方处理
    def download_web(self, url, params=None, headers=None):
        """
        下载网页内容并返回响应对象
        Args:
            url (str): 目标URL
            params (dict, optional): URL参数
            headers (dict, optional): 额外的请求头
            logger (Logger, optional): 日志记录器
        Returns:
            requests.Response: HTTP响应对象
        """

        full_url = self._build_url(url, params)    # 构造完整URL
        request_headers = self._prepare_headers(headers)   # 设置请求头
        res = requests.get(full_url, headers=request_headers)    # 发送请求
        res.raise_for_status() # 检查响应状态
        return res.json()



