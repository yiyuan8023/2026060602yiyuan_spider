import io
import warnings
import zipfile

import pandas as pd
import requests
import chardet
# 忽略 UserWarning
warnings.filterwarnings("ignore", category=UserWarning)
def read_excel_to_dict(excel_content):
    """
    读取excel 转成字典
    :param excel_content:
    :return:
    """
    # 将二进制数据包装成文件对象
    file_like_object = io.BytesIO(excel_content)
    try:
        df = pd.read_excel(file_like_object,engine='openpyxl')
    except:
        df = pd.read_excel(file_like_object,engine='xlrd')
    df_filled = df.fillna("")
    print(df.columns)
    items = df_filled.to_dict('records')
    return items


def detect_encoding(file_content):
    result = chardet.detect(file_content)
    return result["encoding"]

def read_download_zip(url):

    """
    从指定 URL 下载 ZIP 文件并在内存中读取其中的 CSV 数据。

    参数:
    - url (str): ZIP 文件的下载 URL。
    - csv_filename (str): ZIP 文件中目标 CSV 文件的名称。

    返回:
    - pd.DataFrame: 包含 CSV 数据的 Pandas DataFrame。
    """
    try:
        # 发送 HTTP 请求下载 ZIP 文件
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        # 将 ZIP 文件加载到内存中
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:

            # print(zip_file.namelist())
            # 打开目标 CSV 文件并读取内容
            with zip_file.open(zip_file.namelist()[0]) as csv_file:
                # 使用 Pandas 读取 CSV 数据
                file_content = csv_file.read()
                detected_encoding = detect_encoding(file_content)
                print(f"检测到的编码: {detected_encoding}")
                df = pd.read_csv(io.BytesIO(file_content), encoding=detected_encoding)
        return df

    except Exception as e:
        print(f"发生错误: {e}")
        return None
def read_download_csv(url):
    # 发送 HTTP 请求下载 ZIP 文件
    res = requests.get(url)
    res.raise_for_status()
    try:
        data = io.BytesIO(res.content)

        df = pd.read_csv(data)
        df_filled = df.fillna("")
        if df_filled.empty:
            return {}
        else:
            items = df_filled.to_dict('records')
            return items
    except Exception as e:
        print(f"{e.args}")
        raise e
    # 检查请求是否成功

if __name__ == '__main__':

    read_download_zip("https://ad-report-async-download-files.oss-accelerate.aliyuncs.com/universalBP/2001530108/2025/04/21/10568864/MAIN?Expires=1745206795&OSSAccessKeyId=TMP.3Kpm9fBsXurQ9ssWvZyqRVXgDXX4b5SEd84Jk2bmW5ccLWX9oYzxXCoBKhqfekjFZehbxuQ1eTgwfyM7drrX7N3QCQ7eXJ&Signature=AkcmnrAXdV6xwr2ZC0noKbRgXB0%3D")

    """
    
    https://union-file-center.oss-cn-zhangjiakou.aliyuncs.com/online_9a978f3d84edc2859934c0ea244ea43b?Expires=1745224126&OSSAccessKeyId=LTAI4FmnP9ZhkUeeAQpo4VPC&Signature=czKSOkleYjwScGso9scphE14bF0%3D&response-content-disposition=attachment%3B%20filename%3D2025-04-18%2000%253A00%253A00%257E2025-04-18%2023%253A59%253A59-%25E5%2595%2586%25E5%2593%2581%25E5%2588%2586%25E6%259E%2590.csv&response-content-type=text%2Fplain%3B%20charset%3DUTF-8
    
    """
