import io
import logging
import sys
import warnings
from typing import Literal, Optional

import pandas as pd

from extra.logger_ import logger


ExcelEngine = Literal["xlrd", "openpyxl", "odf", "pyxlsb", "calamine"]
OPENPYXL_DEFAULT_STYLE_WARNING = "Workbook contains no default style"


def _reset_position(data, position=0):
    if hasattr(data, "seek"):
        data.seek(position)


def _emit_warning_notes(warning_records):
    """保留原始 warning 输出，再补充平台导出 Excel 的业务说明。"""
    for warning_record in warning_records:
        warnings.showwarning(
            warning_record.message,
            warning_record.category,
            warning_record.filename,
            warning_record.lineno,
            warning_record.file,
            warning_record.line,
        )
        sys.stderr.flush()
        if OPENPYXL_DEFAULT_STYLE_WARNING in str(warning_record.message):
            logger.info(
                "openpyxl 提示工作簿缺少默认样式，可忽略；平台导出 Excel 常见，不影响数据读取。"
            )


def read_excel_dataframe(data, **kwargs):
    """读取 Excel 为 DataFrame，保留原始警告并补充业务备注。"""
    with warnings.catch_warnings(record=True) as warning_records:
        warnings.simplefilter("always")
        df = pd.read_excel(data, **kwargs)

    _emit_warning_notes(warning_records)
    return df


def read_excel_to_dict(excel_content, **kwargs):
    """读取 Excel 二进制内容并转成字典列表。"""
    data = io.BytesIO(excel_content) if isinstance(excel_content, bytes) else excel_content
    read_kwargs = dict(kwargs)

    if "engine" in read_kwargs:
        df = read_excel_dataframe(data, **read_kwargs)
    else:
        # 默认先试 openpyxl，失败后回退 xlrd，兼顾新 xlsx 和历史 xls 导出。
        start_position = data.tell() if hasattr(data, "tell") else 0
        try:
            df = read_excel_dataframe(data, engine="openpyxl", **read_kwargs)
        except Exception as openpyxl_error:
            logging.debug(f"openpyxl 读取 Excel 失败: {openpyxl_error}")
            _reset_position(data, start_position)
            df = read_excel_dataframe(data, engine="xlrd", **read_kwargs)

    return df.fillna("").to_dict("records")


def excel_engine(data, sheet_name=None) -> Optional[ExcelEngine]:
    """
    自动确定 Excel 文件的读取引擎。

    Args:
        data: BytesIO 对象或文件路径。
        sheet_name: 工作表名称，可选。

    Returns:
        推荐的 engine 名称，无法判断时返回 None。
    """
    engines: list[ExcelEngine] = ["openpyxl", "xlrd"]
    current_position = data.tell() if hasattr(data, "tell") else 0

    for engine in engines:
        try:
            _reset_position(data, current_position)
            if sheet_name:
                pd.read_excel(data, nrows=1, sheet_name=sheet_name, engine=engine)
            else:
                pd.read_excel(data, nrows=1, engine=engine)
            return engine
        except Exception as exc:
            logging.debug(f"尝试使用引擎 '{engine}' 读取 Excel 文件失败: {exc}")
            continue

    _reset_position(data, current_position)
    return None
