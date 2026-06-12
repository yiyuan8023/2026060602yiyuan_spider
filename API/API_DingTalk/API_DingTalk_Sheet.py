# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一贯
- 创建时间：2026-06-11 06:29:55
- 最近修改：2026-06-11 06:29:55
- 文件用途：封装钉钉在线表格链接解析、AccessToken 获取、操作人身份解析、Sheet 列表和范围读取。
- 业务范围：适用于读取 alidocs.dingtalk.com 钉钉在线表格数据，优先从表格链接 /nodes/{workbookId} 解析 workbookId。
- 依赖入口：使用 requests、urllib.parse、API_DingTalk_Base、extra.extra_reqlog 和 extra.logger_。
- 验收方式：修改后执行 py_compile；使用 parse_workbook_id 和类导入探针验证基础逻辑，真实读取需配置钉钉应用权限后小范围验证。
- 注意事项：读取表格需要 Document.Workbook.Read 权限；日志不得输出 accessToken、完整 operatorId 或敏感表格内容。
"""

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import requests

from API.API_DingTalk.API_DingTalk_Base import (
    DEFAULT_TIMEOUT,
    DingTalkApiError,
    ensure_state_dir,
    get_config_value,
    load_dingtalk_section,
    mask_secret,
    require_config_value,
)
from extra.extra_reqlog import req_log
from extra.logger_ import logger


class DingTalkSheetClient:
    """钉钉在线表格读取客户端。"""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        *,
        operator_id: str | None = None,
        user_id: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        section = load_dingtalk_section()
        self.client_id = require_config_value(
            client_id or get_config_value("DINGTALK_CLIENT_ID", "client_id", section=section),
            "DINGTALK_CLIENT_ID / dingtalk.client_id",
        )
        self.client_secret = require_config_value(
            client_secret or get_config_value("DINGTALK_CLIENT_SECRET", "client_secret", section=section),
            "DINGTALK_CLIENT_SECRET / dingtalk.client_secret",
        )
        self.operator_id = operator_id or get_config_value(
            ["DINGTALK_UNION_ID", "DINGTALK_OPERATOR_ID"],
            "operator_id",
            section=section,
        )
        self.user_id = user_id or get_config_value("DINGTALK_USER_ID", "user_id", section=section)
        self.timeout = timeout

    @staticmethod
    def parse_workbook_id(value: str) -> str:
        """从钉钉在线表格链接或 workbookId 中解析 workbookId。"""
        raw_value = (value or "").strip()
        if not raw_value:
            raise DingTalkApiError("缺少钉钉表格链接或 workbookId")

        if raw_value.startswith(("http://", "https://")):
            parsed = urlparse(raw_value)
            match = re.search(r"/nodes/([^/?#]+)", parsed.path)
            if match:
                return match.group(1)
            raise DingTalkApiError("无法从钉钉表格链接解析 workbookId，预期路径包含 /nodes/{id}")

        return raw_value

    def get_access_token(self) -> str:
        """获取钉钉应用 accessToken。"""
        response = requests.post(
            "https://api.dingtalk.com/v1.0/oauth2/accessToken",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={"appKey": self.client_id, "appSecret": self.client_secret},
            timeout=self.timeout,
        )
        req_log(response, context="钉钉获取AccessToken", raise_error=True)
        data = response.json()
        token = data.get("accessToken")
        if not token:
            raise DingTalkApiError(f"钉钉AccessToken返回缺少accessToken：{data}")
        return token

    def get_union_id(self, access_token: str, user_id: str) -> str:
        """把钉钉 userId 转成文档 API 需要的 unionId/operatorId。"""
        response = requests.post(
            f"https://oapi.dingtalk.com/topapi/v2/user/get?access_token={quote(access_token, safe='')}",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={"userid": user_id, "language": "zh_CN"},
            timeout=self.timeout,
        )
        req_log(response, context="钉钉userId转unionId", raise_error=True)
        data = response.json()
        if data.get("errcode") != 0:
            raise DingTalkApiError(f"钉钉userId转unionId失败：{data}")

        union_id = (data.get("result") or {}).get("unionid")
        if not union_id:
            raise DingTalkApiError(f"钉钉用户详情返回缺少unionid：{data}")
        return union_id

    def resolve_operator_id(self, access_token: str) -> str:
        """解析文档 API operatorId，优先使用 unionId/operatorId，再用 userId 转换。"""
        if self.operator_id:
            logger.info(f"钉钉表格使用operatorId：{mask_secret(str(self.operator_id))}")
            return str(self.operator_id)

        if self.user_id:
            union_id = self.get_union_id(access_token, str(self.user_id))
            logger.info(f"钉钉表格从userId转换operatorId：{mask_secret(union_id)}")
            return union_id

        state_path = ensure_state_dir() / "last_dingtalk_message.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            sender_staff_id = state.get("sender_staff_id")
            if sender_staff_id:
                return self.get_union_id(access_token, str(sender_staff_id))

        raise DingTalkApiError("缺少 DINGTALK_UNION_ID、DINGTALK_OPERATOR_ID 或 DINGTALK_USER_ID")

    @staticmethod
    def _auth_headers(access_token: str) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-acs-dingtalk-access-token": access_token,
        }

    def request_json(self, url: str, access_token: str, params: dict[str, str], *, context: str) -> dict[str, Any]:
        """请求钉钉文档 API 并返回 JSON。"""
        response = requests.get(
            url,
            headers=self._auth_headers(access_token),
            params=params,
            timeout=self.timeout,
        )
        req_log(response, context=context, raise_error=True)
        return response.json()

    @staticmethod
    def _find_list(value: Any) -> list[Any] | None:
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for key in ("sheets", "value", "data", "result", "workSheets", "worksheetList"):
                found = DingTalkSheetClient._find_list(value.get(key))
                if found is not None:
                    return found
        return None

    @classmethod
    def pick_sheet_id(cls, sheets_payload: dict[str, Any], sheet_name: str) -> str:
        """从 Sheet 列表响应中按名称选出 sheetId。"""
        sheets = cls._find_list(sheets_payload)
        if not sheets:
            raise DingTalkApiError(f"钉钉表格响应中没有找到Sheet列表：{sheets_payload}")

        for sheet in sheets:
            if not isinstance(sheet, dict):
                continue
            name = sheet.get("name") or sheet.get("sheetName") or sheet.get("title")
            sheet_id = sheet.get("sheetId") or sheet.get("id")
            if name == sheet_name and sheet_id:
                return str(sheet_id)

        names = [
            str(sheet.get("name") or sheet.get("sheetName") or sheet.get("title") or "<unknown>")
            for sheet in sheets
            if isinstance(sheet, dict)
        ]
        raise DingTalkApiError(f"Sheet {sheet_name!r} 不存在，可用Sheet：{names}")

    def read_range(
        self,
        workbook_url_or_id: str,
        *,
        sheet_name: str,
        range_address: str,
        output_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """读取指定钉钉在线表格范围。"""
        workbook_id = self.parse_workbook_id(workbook_url_or_id)
        access_token = self.get_access_token()
        operator_id = self.resolve_operator_id(access_token)
        params = {"operatorId": operator_id}

        sheets_url = f"https://api.dingtalk.com/v1.0/doc/workbooks/{quote(workbook_id, safe='')}/sheets"
        sheets_payload = self.request_json(sheets_url, access_token, params, context="钉钉表格读取Sheet列表")
        sheet_id = self.pick_sheet_id(sheets_payload, sheet_name)

        range_url = (
            f"https://api.dingtalk.com/v1.0/doc/workbooks/{quote(workbook_id, safe='')}"
            f"/sheets/{quote(sheet_id, safe='')}/ranges/{quote(range_address, safe='')}"
        )
        range_payload = self.request_json(range_url, access_token, params, context="钉钉表格读取范围")
        result = {
            "workbook_id": workbook_id,
            "sheet_name": sheet_name,
            "sheet_id": sheet_id,
            "range": range_address,
            "payload": range_payload,
        }

        if output_path:
            path = Path(output_path)
        else:
            path = ensure_state_dir() / "last_dingtalk_sheet_read.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"钉钉表格读取结果已保存：{path}")
        return result
