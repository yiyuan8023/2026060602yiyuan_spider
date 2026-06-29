import io
import sys
import warnings
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Literal, Optional

import pandas as pd

from extra.logger_ import logger


ExcelEngine = Literal["xlrd", "openpyxl", "odf", "pyxlsb", "calamine"]
OPENPYXL_DEFAULT_STYLE_WARNING = "Workbook contains no default style"
XLSX_NAMESPACE = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "officeRel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
BUILTIN_DATE_NUM_FORMATS = {
    14, 15, 16, 17, 18, 19, 20, 21, 22,
    27, 28, 29, 30, 31, 32, 33, 34, 35, 36,
    45, 46, 47,
    50, 51, 52, 53, 54, 55, 56, 57, 58,
}


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
            logger.warning(
                "openpyxl 提示工作簿缺少默认样式，可忽略；平台导出 Excel 常见，不影响数据读取。"
            )


def read_excel_dataframe(data, **kwargs):
    """读取 Excel 为 DataFrame，保留原始警告并补充业务备注。"""
    start_position = data.tell() if hasattr(data, "tell") else 0
    try:
        with warnings.catch_warnings(record=True) as warning_records:
            warnings.simplefilter("always")
            df = pd.read_excel(data, **kwargs)
    except TypeError as exc:
        if not _is_openpyxl_style_error(exc):
            raise
        _reset_position(data, start_position)
        logger.warning("openpyxl 解析工作簿样式失败，改用 xlsx XML 兜底读取。")
        return read_xlsx_dataframe_xml(data, **kwargs)

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
            logger.debug(f"openpyxl 读取 Excel 失败: {openpyxl_error}")
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
            logger.debug(f"尝试使用引擎 '{engine}' 读取 Excel 文件失败: {exc}")
            continue

    _reset_position(data, current_position)
    return None


def read_xlsx_dataframe_xml(data, sheet_name=0, skiprows=0, **kwargs):
    """Fallback reader for malformed xlsx styles that openpyxl refuses to load."""
    del kwargs
    file_content = _read_file_content(data)
    with zipfile.ZipFile(io.BytesIO(file_content)) as zip_file:
        shared_strings = _read_shared_strings(zip_file)
        date_style_indexes = _read_date_style_indexes(zip_file)
        sheet_map = _read_sheet_map(zip_file)
        selected_sheet = _select_sheet(sheet_map, sheet_name)
        rows = _read_sheet_rows(zip_file, selected_sheet["path"], shared_strings, date_style_indexes)

    data_rows = rows[skiprows:]
    if not data_rows:
        return pd.DataFrame()

    headers = [_normalize_header(value, index) for index, value in enumerate(data_rows[0])]
    body_rows = data_rows[1:]
    width = len(headers)
    normalized_rows = [
        (row + [""] * width)[:width]
        for row in body_rows
        if any(_normalize_cell(value) for value in row)
    ]
    return pd.DataFrame(normalized_rows, columns=headers)


def get_xlsx_sheet_names_xml(data):
    """Read xlsx sheet names from workbook XML without loading styles."""
    file_content = _read_file_content(data)
    with zipfile.ZipFile(io.BytesIO(file_content)) as zip_file:
        return [sheet["name"] for sheet in _read_sheet_map(zip_file)]


def _is_openpyxl_style_error(exc):
    message = str(exc)
    return (
        "openpyxl.styles.fills.Fill" in message
        or "Fill() takes no arguments" in message
    )


def _read_file_content(data):
    if isinstance(data, bytes):
        return data
    if hasattr(data, "read"):
        return data.read()
    with open(data, "rb") as file:
        return file.read()


def _read_shared_strings(zip_file):
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return []
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    values = []
    for string_item in root.findall("main:si", XLSX_NAMESPACE):
        texts = [
            text_node.text or ""
            for text_node in string_item.findall(".//main:t", XLSX_NAMESPACE)
        ]
        values.append("".join(texts))
    return values


def _read_date_style_indexes(zip_file):
    if "xl/styles.xml" not in zip_file.namelist():
        return set()
    root = ET.fromstring(zip_file.read("xl/styles.xml"))
    custom_formats = {}
    for num_format in root.findall("main:numFmts/main:numFmt", XLSX_NAMESPACE):
        num_format_id = int(num_format.attrib.get("numFmtId", 0))
        custom_formats[num_format_id] = num_format.attrib.get("formatCode", "")

    date_style_indexes = set()
    cell_formats = root.find("main:cellXfs", XLSX_NAMESPACE)
    if cell_formats is None:
        return date_style_indexes

    for index, cell_format in enumerate(cell_formats.findall("main:xf", XLSX_NAMESPACE)):
        num_format_id = int(cell_format.attrib.get("numFmtId", 0))
        format_code = custom_formats.get(num_format_id, "")
        if num_format_id in BUILTIN_DATE_NUM_FORMATS or _looks_like_date_format(format_code):
            date_style_indexes.add(index)
    return date_style_indexes


def _looks_like_date_format(format_code):
    if not format_code:
        return False
    lowered = format_code.lower()
    if any(token in lowered for token in ["yy", "mm", "dd", "hh", "ss", "年", "月", "日"]):
        return not any(token in lowered for token in ["0.00", "#,##0", "general"])
    return False


def _read_sheet_map(zip_file):
    workbook_root = ET.fromstring(zip_file.read("xl/workbook.xml"))
    rels_root = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
    rels = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels_root.findall("rel:Relationship", XLSX_NAMESPACE)
    }
    sheets = []
    for sheet in workbook_root.findall("main:sheets/main:sheet", XLSX_NAMESPACE):
        rel_id = sheet.attrib.get(f"{{{XLSX_NAMESPACE['officeRel']}}}id")
        target = rels.get(rel_id, "")
        path = target if target.startswith("xl/") else f"xl/{target.lstrip('/')}"
        path = path.replace("xl/worksheets/../", "xl/")
        sheets.append({"name": sheet.attrib["name"], "path": path})
    return sheets


def _select_sheet(sheet_map, sheet_name):
    if isinstance(sheet_name, int):
        try:
            return sheet_map[sheet_name]
        except IndexError as exc:
            raise ValueError(f"找不到索引为 {sheet_name} 的工作表") from exc
    for sheet in sheet_map:
        if sheet["name"] == sheet_name:
            return sheet
    raise ValueError(f"找不到工作表: {sheet_name}")


def _read_sheet_rows(zip_file, sheet_path, shared_strings, date_style_indexes):
    root = ET.fromstring(zip_file.read(sheet_path))
    rows = []
    for row_node in root.findall(".//main:sheetData/main:row", XLSX_NAMESPACE):
        values = {}
        for cell in row_node.findall("main:c", XLSX_NAMESPACE):
            col_index = _column_index(cell.attrib.get("r", ""))
            style_index = int(cell.attrib.get("s", 0))
            values[col_index] = _read_cell_value(cell, shared_strings, style_index in date_style_indexes)
        if values:
            max_col = max(values)
            row_values = [values.get(index, "") for index in range(1, max_col + 1)]
            rows.append(row_values)
    return rows


def _column_index(cell_ref):
    letters = "".join(char for char in cell_ref if char.isalpha())
    index = 0
    for char in letters:
        index = index * 26 + ord(char.upper()) - ord("A") + 1
    return index


def _read_cell_value(cell, shared_strings, is_date_style):
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(
            text_node.text or ""
            for text_node in cell.findall(".//main:t", XLSX_NAMESPACE)
        ).strip()

    value_node = cell.find("main:v", XLSX_NAMESPACE)
    if value_node is None or value_node.text is None:
        return ""

    raw_value = value_node.text
    if cell_type == "s":
        index = int(raw_value) if raw_value.isdigit() else -1
        return shared_strings[index].strip() if 0 <= index < len(shared_strings) else raw_value
    if is_date_style:
        return _excel_serial_to_text(raw_value)
    return raw_value.strip()


def _excel_serial_to_text(value):
    try:
        serial = float(value)
    except ValueError:
        return value
    dt = datetime(1899, 12, 30) + timedelta(days=serial)
    if abs(serial - int(serial)) < 0.000001:
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _normalize_header(value, index):
    header = _normalize_cell(value)
    return header or f"Unnamed: {index}"


def _normalize_cell(value):
    if value is None:
        return ""
    return str(value).strip()
