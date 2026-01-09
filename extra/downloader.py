"""
_build_url:构造完整的URL，包括查询参数
_prepare_Headers:准备HTTP请求头，合并默认和自定义头部
_make_request_get:发送HTTP GET请求
_make_request_post:发送HTTP POST请求
download_web:：下载网页内容并返回响应对象
download_file_to_byte:下载Excel文件并返回BytesIO对象
download_excel:下载Excel文件并解析为字典列表
download_csv:下载CSV文件并解析为字典列表
download_zip:下载ZIP文件并解压读取其中的内容,解析为字典列表,目前只读取第一个文件
file_encoding：检测文件内容的字符编码格式
_df_to_dict:df转换为字典列表
"""

import io
import zipfile
import chardet
import warnings
import requests
import pandas as pd
import fnmatch
from urllib.parse import urlencode
from typing import Optional, Dict, Any, Union

from extra.extra_reqlog import req_log
from extra.logger_ import logger
from extra.settings import UA

# 忽略openpyxl的样式警告
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')


class Downloader:
    # 通用的文件下载器

    def __init__(self,
                 api: str,  # 请求的URL
                 method: str = "get",  # 请求方式，支持get和post
                 cookie: Optional[str] = None,  # cookie
                 params: Optional[Dict[str, Any]] = None,  # GET请求的查询参数
                 headers: Optional[Dict[str, str]] = None,  # 请求头
                 data: Optional[Union[Dict, str, bytes]] = None,  # POST请求的表单,data={"name": "value", "age": 25}
                 json_data: Optional[Dict] = None,  # POST请求的JSON格式,json_data={"user": {"name": "value", "age": 25}}
                 timeout: int = 30):  # 请求超时时间（秒）
        self.api = api
        self.method = method
        self.cookie = cookie
        self.params = params or {}
        self.headers = headers or {}
        self.url = self._build_url()
        self.default_headers = self._prepare_headers()
        self.timeout = timeout
        self.json_data = json_data
        self.data = data or {}

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

    def _make_request_get(self) -> requests.Response:
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

    def _make_request_post(self) -> requests.Response:
        """
        发送HTTP POST请求的通用方法
        Returns: requests.Response: HTTP响应对象
        """
        try:
            logger.info(f"POST请求URL: {self.url}")
            # 根据参数类型选择发送方式
            if self.json_data is not None:
                response = requests.post(
                    self.url,
                    json=self.json_data,
                    headers=self.default_headers,
                    timeout=self.timeout
                )
            else:
                # 发送表单数据或其他数据
                response = requests.post(
                    self.url,
                    data=self.data,
                    headers=self.default_headers,
                    timeout=self.timeout
                )
            req_log(response)
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"POST网络请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"发送POST请求时发生未知错误: {e}")
            raise

    def download_web(self):
        """
        下载网页内容并返回响应对象
        Returns: requests.Response: HTTP响应对象
        """
        try:
            if self.method == "post":
                res = self._make_request_post()
            else:
                res = self._make_request_get()  # 发送请求
            return res

        except requests.exceptions.RequestException as e:
            # 处理请求相关的异常（如连接错误、超时等）
            logger.error(f"网络请求失败: {e}")
            raise

        except Exception as e:
            # 处理其他未预期的异常
            logger.error(f"下载网页时发生未知错误: {e}")
            raise

    def download_excel(self, sheet_name=0, skiprows=0, engine=None):  # NOQA
        """
        下载Excel文件，解析数据，返回items 字典格式的数据
        sheet_name: str,  # 工作表名称，支持通配符
        """
        try:
            data = self.download_file_to_byte()
            # 检查sheet_name是否包含通配符
            if isinstance(sheet_name, str) and ('*' in sheet_name or '?' in sheet_name):
                # 读取所有工作表名称

                xl_file = pd.ExcelFile(data)
                all_sheet_names = xl_file.sheet_names

                # 根据通配符模式找到匹配的工作表
                matched_sheets = [name for name in all_sheet_names if fnmatch.fnmatch(name, sheet_name)]

                if not matched_sheets:
                    raise ValueError(f"找不到匹配模式 '{sheet_name}' 的工作表")

                # 读取所有匹配的工作表并合并
                dfs = []
                for sheet in matched_sheets:
                    df_temp = pd.read_excel(data, sheet_name=sheet, skiprows=skiprows, engine=engine)
                    df_temp['__SheetName__'] = sheet  # 添加工作表名称列
                    dfs.append(df_temp)
                # 合并所有匹配的工作表
                df_excel = pd.concat(dfs, ignore_index=True)
            else:
                # 如果不使用通配符，按正常方式读取
                df_excel = pd.read_excel(data, sheet_name=sheet_name, skiprows=skiprows, engine=engine)

            items = self._df_to_dict(df_excel)
            return items

        except Exception as e:
            logger.error(f"处理Excel文件时发生未知错误: {e}")
            raise  # 重新抛出异常，让调用方处理

    @staticmethod
    def _df_to_dict(df):

        # 所有的NaN值（缺失值）替换为None
        # df_excel.replace({np.nan: None}, inplace=True) # 替代方案
        df_filled = df.fillna("")

        # df.empty 是 pandas DataFrame 的属性， 用于检查 DataFrame 是否为空（没有任何行数据）
        if df_filled.empty:
            return {}
        else:
            items = df_filled.to_dict('records')  # to_dict('records')，将 DataFrame 转换为字典格式
            return items

    def download_file_to_byte(self):
        """
        下载Excel文件并返回BytesIO对象
        Returns: io.BytesIO: 包含Excel数据的BytesIO对象
        """
        try:
            res = self.download_web()
            data = io.BytesIO(res.content)  # 将HTTP响应的二进制内容转换为内存中的文件对象(BytesIO对象)
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"下载Excel/csv文件失败: {e}")
            raise  # 重新抛出异常，让调用方处理

        except Exception as e:
            logger.error(f"处理Excel/csv文件时发生未知错误: {e}")
            raise  # 重新抛出异常，让调用方处理

    def download_csv(self):
        # 发送 HTTP 请求下载 csv 文件,返回BytesIO对象
        try:
            data = self.download_file_to_byte()  # 将HTTP响应的二进制内容转换为内存中的文件对象(BytesIO对象)
            df_csv = pd.read_csv(data)
            items = self._df_to_dict(df_csv)
            return items

        except Exception as e:
            logger.error(f"处理csv文件时发生未知错误: {e}")
            raise  # 重新抛出异常，让调用方处理

    @staticmethod
    def file_encoding(file_content):
        # 是检测文件内容的字符编码格式。
        result = chardet.detect(file_content)
        return result["encoding"]

    def download_zip(self, file_type='csv'):
        """
        从指定 URL 下载 ZIP 文件并在内存中读取其中的 CSV 数据。
        参数:
        - csv_filename (str): ZIP 文件中目标 CSV 文件的名称。
        Returns:- pd.DataFrame: 包含 CSV 数据的 Pandas DataFrame。
        """
        try:
            # 发送 HTTP 请求下载 ZIP 文件
            res = self.download_web()  # 发送请求
            # print(res.content)

            # 将 ZIP 文件加载到内存中
            with zipfile.ZipFile(io.BytesIO(res.content)) as zip_file:
                logger.info(f"文件名称: {zip_file.namelist()}")
                # 打开目标 CSV 文件并读取内容
                with zip_file.open(zip_file.namelist()[0]) as file:  # 第一个文件
                    # 使用 Pandas 读取数据
                    file_content = file.read()
                    if file_type == 'csv':
                        de_encoding = self.file_encoding(file_content)
                        logger.info(f"检测到的编码: {de_encoding}")
                        df_data = pd.read_csv(io.BytesIO(file_content), encoding=de_encoding)
                    elif file_type == 'excel':
                        df_data = pd.read_excel(io.BytesIO(file_content))
                    else:
                        logger.error(f"不支持的文件类型: {file_type}")
                        df_data = None
                df_filled = df_data.fillna("")
                if df_filled.empty:
                    return {}
                else:
                    items = df_filled.to_dict('records')
                    return items
        except Exception as e:
            print(f"发生错误: {e}")
            return None
