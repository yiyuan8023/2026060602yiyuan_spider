import fnmatch
import io
import zipfile
from typing import Optional

import pandas as pd

from extra.excel_reader import read_excel_dataframe
from extra.logger_ import logger

from .encoding import detect_text_encoding


def _reset_position(data, position=0):
    if hasattr(data, "seek"):
        data.seek(position)


def dataframe_to_records(df: pd.DataFrame):
    """DataFrame 转字典列表，空表沿用项目旧约定返回空字典。"""
    df_filled = df.fillna("")
    if df_filled.empty:
        return {}
    return df_filled.to_dict("records")


def _read_excel_sheet(data, sheet_name=0, skiprows=0, engine=None):
    read_kwargs = {
        "sheet_name": sheet_name,
        "skiprows": skiprows,
    }
    if engine:
        read_kwargs["engine"] = engine
    return read_excel_dataframe(data, **read_kwargs)


def read_excel_records(data, sheet_name=0, skiprows=0, engine=None):
    """读取 Excel 内容，支持 sheet_name 通配符。"""
    start_position = data.tell() if hasattr(data, "tell") else 0

    if isinstance(sheet_name, str) and ("*" in sheet_name or "?" in sheet_name):
        excel_kwargs = {}
        if engine:
            excel_kwargs["engine"] = engine

        _reset_position(data, start_position)
        xl_file = pd.ExcelFile(data, **excel_kwargs)
        matched_sheets = [
            name for name in xl_file.sheet_names if fnmatch.fnmatch(name, sheet_name)
        ]

        if not matched_sheets:
            raise ValueError(f"找不到匹配模式 '{sheet_name}' 的工作表")

        dfs = []
        for sheet in matched_sheets:
            _reset_position(data, start_position)
            df_temp = _read_excel_sheet(
                data,
                sheet_name=sheet,
                skiprows=skiprows,
                engine=engine,
            )
            df_temp["__SheetName__"] = sheet
            dfs.append(df_temp)
        return dataframe_to_records(pd.concat(dfs, ignore_index=True))

    _reset_position(data, start_position)
    df_excel = _read_excel_sheet(
        data,
        sheet_name=sheet_name,
        skiprows=skiprows,
        engine=engine,
    )
    return dataframe_to_records(df_excel)


def read_csv_records(data):
    """读取 CSV 内容，优先检测平台导出文件编码。"""
    file_content = data.getvalue() if hasattr(data, "getvalue") else data.read()
    encoding = detect_text_encoding(file_content)
    if encoding:
        logger.info(f"检测到的编码: {encoding}")
    df_csv = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
    return dataframe_to_records(df_csv)


def read_zip_records(zip_content: bytes, file_type: str = "csv"):
    """读取 ZIP 中的第一个文件，支持 CSV 和 Excel。"""
    with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
        file_names = zip_file.namelist()
        logger.info(f"文件名称: {file_names}")
        if not file_names:
            raise ValueError("ZIP 文件为空")

        with zip_file.open(file_names[0]) as file:
            file_content = file.read()

    if file_type == "csv":
        return read_csv_records(io.BytesIO(file_content))
    if file_type == "excel":
        return read_excel_records(io.BytesIO(file_content))

    raise ValueError(f"不支持的文件类型: {file_type}")
