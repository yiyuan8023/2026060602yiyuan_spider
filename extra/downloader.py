import io
import zipfile
from typing import Optional, Dict, Any

import pandas as pd
import requests
from urllib.parse import urlencode
import chardet

from extra.extra_reqlog import req_log
from extra.logger_ import logger
from extra.settings import UA
import warnings

# 忽略openpyxl的样式警告
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')


class Downloader:
    # 通用的文件下载器

    def __init__(self,
                 api: str,
                 cookie: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None):
        self.api = api
        self.cookie = cookie
        self.params = params or {}
        self.headers = headers or {}
        self.url = self._build_url()
        self.default_headers = self._prepare_headers()

    def _build_url(self):
        """
        构造完整的URL
        """
        if self.params:
            separator = '&' if '?' in self.api else '?'
            return f"{self.api}{separator}{urlencode(self.params)}"
        return self.api

    def _prepare_headers(self):
        # 合并请求头,设置默认请求头

        default_headers = {
            "User-Agent": UA,
            "cookie": self.cookie
        }
        # 合并自定义请求头
        if self.headers:
            default_headers.update(self.headers)
        return default_headers

    def _log_request(self, status_code):
        """
        记录请求日志
        Args:
            self.url(str): 请求URL
            status_code (int): 响应状态码
        """
        if logger:
            logger.info(f"请求URL: {self.url}")
            logger.info(f"响应状态码: {status_code}")

    def make_request_get(self) -> requests.Response:
        """
        发送HTTP GET请求的通用方法
        Returns: requests.Response: HTTP响应对象
        """
        try:
            logger.info(self.url)
            res = requests.get(self.url, headers=self.default_headers)
            req_log(res)
            return res
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"发送请求时发生未知错误: {e}")
            raise

    def download_excel(self):
        """
        下载Excel文件并返回BytesIO对象
        Returns: io.BytesIO: 包含Excel数据的BytesIO对象
        """
        try:
            res = self.make_request_get()  # 发送请求
            return io.BytesIO(res.content)  # 将HTTP响应的二进制内容转换为内存中的文件对象(BytesIO对象)

        except requests.exceptions.RequestException as e:
            logger.error(f"下载Excel文件失败: {e}")
            raise  # 重新抛出异常，让调用方处理

        except Exception as e:
            logger.error(f"处理Excel文件时发生未知错误: {e}")
            raise  # 重新抛出异常，让调用方处理

    def download_web(self):
        """
        下载网页内容并返回响应对象
        Returns: requests.Response: HTTP响应对象
        """
        try:
            res = self.make_request_get()  # 发送请求
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

    def download_zip(self):

        """
        从指定 URL 下载 ZIP 文件并在内存中读取其中的 CSV 数据。
        参数:
        - csv_filename (str): ZIP 文件中目标 CSV 文件的名称。
        Returns:- pd.DataFrame: 包含 CSV 数据的 Pandas DataFrame。
        """
        try:
            # 发送 HTTP 请求下载 ZIP 文件
            res = self.make_request_get()  # 发送请求

            # 将 ZIP 文件加载到内存中
            with zipfile.ZipFile(io.BytesIO(res.content)) as zip_file:

                # print(zip_file.namelist())
                # 打开目标 CSV 文件并读取内容
                with zip_file.open(zip_file.namelist()[0]) as csv_file:
                    # 使用 Pandas 读取 CSV 数据
                    file_content = csv_file.read()
                    de_encoding = self.detect_encoding(file_content)
                    logger.info(f"检测到的编码: {de_encoding}")
                    df_data = pd.read_csv(io.BytesIO(file_content), encoding=de_encoding)
            return df_data

        except Exception as e:
            print(f"发生错误: {e}")
            return None

    def download_csv(self):
        # 发送 HTTP 请求下载 csv 文件
        data = self.download_excel()
        return data


if __name__ == '__main__':
    url = (f"https://trade.taobao.com/trade/itemlist/export_by_tfs.do?"
           f"f_p=oss%2Ftradeorderexport%2ForderExportData%2F24723487011.ossprivate.xlsx"  # NOQA
           f"-8c91c21d9cb8b176fbb706e0c08c1726-items&amp;apply_time=2025-08-08+09%3A31%3A02&amp;"
           f"start_time=2025-08-05+00%3A00%3A00&amp;end_time=2025-08-08+00%3A00%3A00&amp;"
           f"order_status=%C8%AB%B2%BF&amp;export_id=24723487011")

    print("开始下载Excel文件...")
    downloader = Downloader(api=url)
    excel_data = downloader.download_excel()

    print(f"文件下载完成，大小: {excel_data.getbuffer().nbytes} 字节")

    # 重置文件指针到开始位置
    excel_data.seek(0)

    # 尝试使用openpyxl读取
    df = pd.read_excel(excel_data, engine='openpyxl')
    print(f"成功读取Excel文件:")
    print(f"  数据形状: {df.shape}")
    print(f"  列名: {list(df.columns)}")
    print("\n前5行数据:")
    print(df.head())
