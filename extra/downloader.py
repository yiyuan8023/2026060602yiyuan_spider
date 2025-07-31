import io
import zipfile

import pandas as pd
import requests
from urllib.parse import urlencode

from requests.compat import chardet

from extra.extra_reqlog import req_log
from extra.logger_ import logger
from extra.settings import UA


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
        Returns:
            requests.Response: HTTP响应对象
        """
        try:
            url = self._build_url(url, params)    # 构造完整URL
            logger.info(url)  # 构造完整URL

            request_headers = self._prepare_headers(headers)   # 设置请求头
            res = requests.get(url, headers=request_headers)    # 发送请求
            req_log(res)
            return res

        except requests.exceptions.RequestException as e:
            # 处理请求相关的异常（如连接错误、超时等）
            logger.error(f"网络请求失败: {e}")
            raise

        except Exception as e:
            # 处理其他未预期的异常
            logger.error(f"下载网页时发生未知错误: {e}")
            raise

    @staticmethod
    def detect_encoding(file_content):
        result = chardet.detect(file_content)
        return result["encoding"]

    def download_zip(self,url,params=None, headers=None):

        """
        从指定 URL 下载 ZIP 文件并在内存中读取其中的 CSV 数据。
        参数:
        - url (str): ZIP 文件的下载 URL。
        - csv_filename (str): ZIP 文件中目标 CSV 文件的名称。

        返回:
        - pd.DataFrame: 包含 CSV 数据的 Pandas DataFrame。
        """
        try:
            url = self._build_url(url, params)    # 构造完整URL
            logger.info(url)  # 构造完整URL
            request_headers = self._prepare_headers(headers)  # 设置请求头
            # 发送 HTTP 请求下载 ZIP 文件
            res = requests.get(url, headers=request_headers)  # 发送请求
            req_log(res)

            # 将 ZIP 文件加载到内存中
            with zipfile.ZipFile(io.BytesIO(res.content)) as zip_file:

                # print(zip_file.namelist())
                # 打开目标 CSV 文件并读取内容
                with zip_file.open(zip_file.namelist()[0]) as csv_file:
                    # 使用 Pandas 读取 CSV 数据
                    file_content = csv_file.read()
                    de_encoding = self.detect_encoding(file_content)
                    print(f"检测到的编码: {de_encoding}")
                    df = pd.read_csv(io.BytesIO(file_content), encoding=de_encoding)
            return df

        except Exception as e:
            print(f"发生错误: {e}")
            return None


