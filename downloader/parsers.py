import fnmatch
import io
import zipfile
from typing import Optional

import pandas as pd

from excel_tool.reader import get_xlsx_sheet_names_xml, read_excel_dataframe
from extra.logger_ import logger

from .encoding import detect_text_encoding


def _reset_position(data, position=0):
    if hasattr(data, "seek"):
        data.seek(position)


def dataframe_to_records(df: pd.DataFrame):
    """DataFrame 转字典列表，空表返回空字典。"""
    df_filled = df.fillna("")
    if df_filled.empty:
        return {}
    return df_filled.to_dict("records")


def _read_excel_sheet(data, sheet_name=0, skiprows=0, engine=None, **read_kwargs):
    read_kwargs = {
        "sheet_name": sheet_name,
        "skiprows": skiprows,
        **read_kwargs,
    }
    if engine:
        read_kwargs["engine"] = engine
    return read_excel_dataframe(data, **read_kwargs)


def get_excel_sheet_names(data, engine=None):
    """读取 Excel 工作表名称，供业务脚本做固定 Sheet 校验。"""
    start_position = data.tell() if hasattr(data, "tell") else 0
    try:
        _reset_position(data, start_position)
        return get_xlsx_sheet_names_xml(data)
    except (KeyError, OSError, ValueError, zipfile.BadZipFile):
        _reset_position(data, start_position)

    excel_kwargs = {}
    if engine:
        excel_kwargs["engine"] = engine

    _reset_position(data, start_position)
    xl_file = pd.ExcelFile(data, **excel_kwargs)
    try:
        return list(xl_file.sheet_names)
    finally:
        xl_file.close()
        _reset_position(data, start_position)


def validate_excel_sheet_name(data, sheet_name, engine=None, context="Excel文件"):
    """固定 Sheet 名称；名称被改动时直接抛错，避免误入库。"""
    if not isinstance(sheet_name, str) or "*" in sheet_name or "?" in sheet_name:
        return

    sheet_names = get_excel_sheet_names(data, engine=engine)
    if sheet_name not in sheet_names:
        raise ValueError(f"{context} Sheet名称不匹配: expected={sheet_name}, actual={sheet_names}")


def read_excel_records(data, sheet_name=0, skiprows=0, engine=None, **read_kwargs):
    """读取 Excel 内容，支持 sheet_name 通配符。"""
    start_position = data.tell() if hasattr(data, "tell") else 0

    if isinstance(sheet_name, str) and ("*" in sheet_name or "?" in sheet_name):
        # 平台导出可能按店铺或渠道拆多个 sheet，通配符用于合并匹配工作表。
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
                **read_kwargs,
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
        **read_kwargs,
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

        # 当前平台导出约定读取压缩包内第一个业务文件；多文件 ZIP 后续再扩展。
        with zip_file.open(file_names[0]) as file:
            file_content = file.read()

    if file_type == "csv":
        return read_csv_records(io.BytesIO(file_content))
    if file_type == "excel":
        return read_excel_records(io.BytesIO(file_content))

    raise ValueError(f"不支持的文件类型: {file_type}")
