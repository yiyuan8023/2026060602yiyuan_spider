# -*- coding: utf-8 -*-
"""
Development notes:
- Author: Yiyuan
- Created: 2026-06-26 12:20:00
- Purpose: Resolve and read WeCom Docs smartsheet data through the opendoc protocol.
- Scope: doc.weixin.qq.com/smartsheet pages that expose compressed smartsheet data.
- Validation: py_compile and read-only replay against the new retail customer-follow sheet.
- Safety: Log only metadata and row counts; do not log Cookie or sensitive row contents.
"""

import base64
import json
import re
import time
import zlib
from datetime import datetime
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlencode, urlparse

from API.API_WeCom_Docs.API_WeCom_Docs_Base import WeComDocsBaseApi
from extra.logger_ import logger


class WeComDocsFileApi(WeComDocsBaseApi):
    """Resolve WeCom smartsheet metadata and decode visible table records."""

    DOC_ID_PATTERN = re.compile(r"/smartsheet/([^/?#]+)")

    def resolve_document_info(self, document_url):
        """Resolve the document page and file metadata needed for opendoc."""
        document_parts = self._parse_document_url(document_url)
        response_json = self.request_json(
            "/wedoc/getfileinfobyurl",
            params={"url": document_url},
            context="企微文档解析文件信息",
        )
        head = response_json.get("head") or {}
        if head.get("ret") not in (0, "0", None):
            raise RuntimeError(f"企微文档解析文件信息失败: ret={head.get('ret')}, msg={head.get('msg')}")

        body = response_json.get("body") or {}
        title = str(body.get("filename") or "")
        file_info = {
            "id": document_parts["pad_id"],
            "local_pad_id": document_parts["pad_id"],
            "pad_id": document_parts["pad_id"],
            "table_id": document_parts["table_id"],
            "view_id": document_parts["view_id"],
            "scode": document_parts["scode"],
            "title": title,
            "drive_file_id": str(body.get("fileid") or ""),
            "space_id": str(body.get("spaceid") or ""),
            "entry_type": str(body.get("entry_type") or ""),
            "share_link": self._strip_query(document_url),
        }
        logger.info(
            f"企微文档文件信息解析成功，title={file_info['title']}，"
            f"pad_id={file_info['pad_id']}，table_id={file_info['table_id']}"
        )
        return file_info

    def read_smartsheet_records(self, file_info, *, sheet_name, startrow=0, endrow=2000):
        """Read and decode smartsheet records from the opendoc compressed payload."""
        response_json = self._request_opendoc(file_info, startrow=startrow, endrow=endrow)
        client_vars = response_json.get("clientVars") or {}
        if client_vars.get("localPadId") and client_vars.get("localPadId") != file_info.get("pad_id"):
            raise RuntimeError(
                f"企微文档文件ID不匹配: expected={file_info.get('pad_id')}, actual={client_vars.get('localPadId')}"
            )
        if client_vars.get("padTitle") and client_vars.get("padTitle") != file_info.get("title"):
            file_info["title"] = str(client_vars.get("padTitle") or "")

        records = self._decode_opendoc_records(response_json, file_info, sheet_name)
        logger.info(
            f"企微文档表格读取完成，title={file_info.get('title')}，"
            f"sheet={sheet_name}，rows={len(records)}"
        )
        return records

    def _request_opendoc(self, file_info, *, startrow, endrow):
        tok = self._get_cookie_value("TOK")
        if not tok:
            raise RuntimeError("企微文档 Cookie 缺少 TOK，无法请求 opendoc")

        params = {
            "scode": file_info.get("scode") or "",
            "tab": file_info.get("table_id") or "",
            "viewId": file_info.get("view_id") or "",
            "id": file_info.get("pad_id") or "",
            "outformat": "1",
            "supportOptimizedVer": "2",
            "chunkCellSize": "300000",
            "enableChunkRank": "1",
            "enablePermOpt": "0",
            "normal": "1",
            "startrow": str(startrow),
            "endrow": str(endrow),
            "wb": "1",
            "nowb": "0",
            "noEscape": "1",
            "enableSmartsheetSplit": "1",
            "t": str(int(time.time() * 1000)),
            "xsrf": tok,
            "shortcut_id": "",
            "req_from": "1",
        }
        return self.request_json(
            "/dop-api/opendoc",
            params=params,
            context="企微文档读取在线表格",
            timeout=60,
        )

    def _decode_opendoc_records(self, response_json, file_info, sheet_name):
        collab_vars = ((response_json.get("clientVars") or {}).get("collab_client_vars") or {})
        initial_text = collab_vars.get("initialAttributedText") or {}
        text_chunks = initial_text.get("text") or []
        if not text_chunks:
            raise RuntimeError("企微文档 opendoc 未返回 smartsheet 初始数据")

        target_chunk = None
        for chunk in text_chunks:
            if str(chunk.get("start_row_index", "")) == "0" or chunk.get("smartsheet"):
                target_chunk = chunk
                break
        target_chunk = target_chunk or text_chunks[0]

        workbook = self._loads_json_list(target_chunk.get("workbook"), "企微文档工作簿信息")
        sheet_meta = self._select_sheet(workbook, file_info.get("table_id"), sheet_name)
        if sheet_meta.get("name") != sheet_name:
            raise RuntimeError(f"企微文档 Sheet 名称不匹配: expected={sheet_name}, actual={sheet_meta.get('name')}")
        if sheet_meta.get("id") != file_info.get("table_id"):
            raise RuntimeError(f"企微文档 Sheet ID 不匹配: expected={file_info.get('table_id')}, actual={sheet_meta.get('id')}")

        operations = self._decode_smartsheet_operations(target_chunk.get("smartsheet"))
        schema_op = self._find_operation(operations, 3005)
        data_op = self._find_operation(operations, 3028)
        table_schema = (((schema_op.get("c") or {}).get("k3")) or {})
        fields = table_schema.get("k3") or {}
        views = table_schema.get("k4") or []
        record_bundle = (((data_op.get("c") or {}).get("k2")) or {})
        records = record_bundle.get("k1") or {}
        record_metadata = record_bundle.get("k2") or {}

        view_config = self._select_view(views, file_info.get("view_id"))
        field_order = (((view_config.get("k1") or {}).get("k2")) or list(fields.keys()))
        if len(field_order) != target_chunk.get("max_col"):
            logger.warning(
                f"企微文档字段数量与页面 max_col 不一致，field_order={len(field_order)}，max_col={target_chunk.get('max_col')}"
            )

        context = self._build_decode_context(fields, table_schema)
        decoded_records = []
        for record_id, record_data in records.items():
            cells = (record_data or {}).get("k1") or {}
            row = {}
            for field_id in field_order:
                field_info = fields.get(field_id) or {}
                header = str(field_info.get("k30") or field_id)
                cell = cells.get(field_id)
                if cell is None and field_info.get("k31") == 12:
                    # Type 12 is WeCom smartsheet's record-created/register time and lives on record metadata.
                    cell = {"k12": (record_metadata.get(record_id) or {}).get("k1")}
                row[header] = self._decode_cell(field_id, field_info, cell, context)
            row["__record_id"] = record_id
            if any(str(value).strip() for key, value in row.items() if key != "__record_id"):
                decoded_records.append(row)
        return decoded_records

    @staticmethod
    def _decode_smartsheet_operations(value):
        if not value:
            raise RuntimeError("企微文档 smartsheet 数据为空")
        content = value.encode("utf-8")
        content += b"=" * ((4 - len(content) % 4) % 4)
        try:
            decoded = zlib.decompress(base64.b64decode(content)).decode("utf-8")
            parsed = json.loads(decoded)
        except (ValueError, zlib.error, json.JSONDecodeError) as exc:
            raise RuntimeError("企微文档 smartsheet 数据解压失败") from exc
        if not parsed or not isinstance(parsed[0], list):
            raise RuntimeError("企微文档 smartsheet 数据结构异常")
        return parsed[0]

    @staticmethod
    def _find_operation(operations, operation_type):
        for operation in operations:
            if operation.get("t") == operation_type:
                return operation
        raise RuntimeError(f"企微文档 smartsheet 缺少操作类型: {operation_type}")

    @staticmethod
    def _select_sheet(workbook, table_id, sheet_name):
        for sheet in workbook:
            if sheet.get("id") == table_id:
                return sheet
        for sheet in workbook:
            if sheet.get("name") == sheet_name:
                return sheet
        raise RuntimeError(f"企微文档工作簿缺少目标 Sheet: {sheet_name}")

    @staticmethod
    def _select_view(views, view_id):
        for view in views:
            if view.get("k30") == view_id:
                return view
        raise RuntimeError(f"企微文档缺少目标视图: {view_id}")

    @staticmethod
    def _build_decode_context(fields, table_schema):
        option_maps = {}
        for field_id, field_info in fields.items():
            field_options = {}
            for option_key in ("k17", "k9"):
                option_config = field_info.get(option_key)
                if not isinstance(option_config, dict):
                    continue
                for option in option_config.get("k3") or []:
                    option_id = str(option.get("k1") or "")
                    option_name = str(option.get("k2") or "")
                    if option_id:
                        field_options[option_id] = option_name
            if field_options:
                option_maps[field_id] = field_options

        user_map = {}
        for user_id, user_info in (table_schema.get("k5") or {}).items():
            if isinstance(user_info, dict):
                user_map[str(user_id)] = str(user_info.get("k2") or user_info.get("k7") or user_id)
        return {"option_maps": option_maps, "user_map": user_map}

    def _decode_cell(self, field_id, field_info, cell, context):
        if not isinstance(cell, dict):
            return ""

        field_type = field_info.get("k31")
        if field_type == 1:
            return self._decode_rich_text(cell.get("k1"))
        if field_type == 2:
            return self._normalize_cell(cell.get("k2"))
        if field_type in (4, 12):
            return self._decode_timestamp(cell.get(f"k{field_type}") or cell.get("k4") or cell.get("k12"))
        if field_type in (9, 17):
            value_key = f"k{field_type}"
            return self._decode_options(field_id, cell.get(value_key), context["option_maps"])
        if field_type in (7, 27):
            return self._decode_people_or_group(field_type, cell, context["user_map"])
        if field_type == 15:
            return self._normalize_cell(cell.get("k15"))
        if field_type == 19:
            return self._decode_formula_or_link(cell)

        for key in ("k1", "k2", "k4", "k9", "k12", "k15", "k17", "k27"):
            if key in cell:
                return self._normalize_cell(cell.get(key))
        return ""

    @staticmethod
    def _decode_rich_text(value):
        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict):
                    parts.append(str(item.get("k2") or ""))
                else:
                    parts.append(str(item))
            return "".join(parts).strip()
        return WeComDocsFileApi._normalize_cell(value)

    @staticmethod
    def _decode_options(field_id, values, option_maps):
        if values in (None, ""):
            return ""
        if not isinstance(values, list):
            values = [values]
        options = option_maps.get(field_id) or {}
        return ",".join(options.get(str(value), str(value)) for value in values if str(value))

    @staticmethod
    def _decode_people_or_group(field_type, cell, user_map):
        value_key = f"k{field_type}"
        values = cell.get(value_key) or []
        if not isinstance(values, list):
            values = [values]
        parts = []
        for item in values:
            if isinstance(item, dict):
                value = item.get("k3") or item.get("k2") or item.get("k1") or ""
                value = user_map.get(str(value), str(value))
            else:
                value = user_map.get(str(item), str(item))
            if value:
                parts.append(value)
        return ",".join(parts)

    @staticmethod
    def _decode_formula_or_link(cell):
        payload = ((cell.get("k36") or {}).get("k1")) if isinstance(cell.get("k36"), dict) else ""
        if payload:
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = {}
            values = []
            for item in data.get("data") or []:
                if item.get("text"):
                    values.append(str(item.get("text")))
                elif item.get("timestamp"):
                    values.append(WeComDocsFileApi._decode_timestamp(item.get("timestamp")))
            return ",".join(value for value in values if value)
        return ""

    @staticmethod
    def _decode_timestamp(value):
        if value in (None, ""):
            return ""
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value).strip()
        seconds = number / 1000 if number > 10000000000 else number
        try:
            return datetime.utcfromtimestamp(seconds).strftime("%Y-%m-%d")
        except (OverflowError, OSError, ValueError):
            return str(value).strip()

    @staticmethod
    def _loads_json_list(value, context):
        if isinstance(value, list):
            return value
        if not value:
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{context} 解析失败") from exc
        if not isinstance(parsed, list):
            raise RuntimeError(f"{context} 不是列表结构")
        return parsed

    @staticmethod
    def _parse_document_url(document_url):
        parsed = urlparse(document_url)
        match = WeComDocsFileApi.DOC_ID_PATTERN.search(parsed.path)
        if not match:
            raise RuntimeError("企微文档 URL 未解析到 smartsheet 文件ID")
        query = parse_qs(parsed.query)
        return {
            "pad_id": match.group(1),
            "table_id": (query.get("tab") or [""])[0],
            "view_id": (query.get("viewId") or [""])[0],
            "scode": (query.get("scode") or [""])[0],
        }

    def _get_cookie_value(self, name):
        cookies = SimpleCookie()
        cookies.load(self.cookie or "")
        morsel = cookies.get(name)
        return morsel.value if morsel else ""

    @staticmethod
    def _strip_query(document_url):
        parsed = urlparse(document_url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    @staticmethod
    def _normalize_cell(value):
        if value is None:
            return ""
        return str(value).strip()
