# 创建新文件: utils/excel_downloader.py

import io
import requests
from urllib.parse import urlencode

from settings import UA


class ExcelDownloader:
    """
    通用的Excel文件下载器
    """

    def __init__(self, cookie):
        self.cookie = cookie

    def download_excel(self, api, params, headers=None):
        """
        下载Excel文件并返回BytesIO对象

        Args:
            api (str): API基础URL
            params (dict): 请求参数
            headers (dict, optional): 额外的请求头

        Returns:
            io.BytesIO: 包含Excel数据的BytesIO对象
        """
        # 构造完整URL
        url = api + urlencode(params)

        # 设置默认请求头
        default_headers = {
            "User-Agent": UA,
            "cookie": self.cookie
        }

        # 合并自定义请求头
        if headers:
            default_headers.update(headers)

        # 发送请求
        res = requests.get(url, headers=default_headers)

        # 检查响应状态
        res.raise_for_status()

        # 将响应内容转换为BytesIO对象
        return io.BytesIO(res.content)

    def download_excel_with_logging(self, api, params, logger=None):
        """
        下载Excel文件并记录日志

        Args:
            api (str): API基础URL
            params (dict): 请求参数
            logger (Logger, optional): 日志记录器

        Returns:
            io.BytesIO: 包含Excel数据的BytesIO对象
        """
        url = api + urlencode(params)

        headers = {
            "User-Agent": UA,
            "cookie": self.cookie
        }

        res = requests.get(url, headers=headers)

        # 记录请求日志
        if logger:
            logger.info(f"请求URL: {url}")
            logger.info(f"响应状态码: {res.status_code}")

        res.raise_for_status()
        return io.BytesIO(res.content)
