"""
开发说明：
- 作者：一元
- 创建时间：2025-04-29 10:48:00
- 最近修改：2026-06-10 17:30:00
- 文件用途：封装赤兔 API 公共请求、Cookie 校验、导出密码校验、导出任务创建、状态轮询和下载能力。
- 业务范围：适用于 API_ChiTu 下所有赤兔接口模块，负责赤兔登录态和导出校验，不承载具体业务表入库。
- 依赖入口：使用 requests、retrying、cookie_manager.extra_cookie.get_ramdom_ua、extra.logger_。
- 验收方式：修改后执行 py_compile、API 包导入探针，并用单店铺单日期任务验证 Cookie、密码、报表导出链路。
- 注意事项：日志不得输出完整 Cookie、导出密码、授权信息或下载内容；API 初始化失败必须显式抛错。
"""

import json
from urllib.parse import urlencode

import requests
from retrying import retry

from cookie_manager.extra_cookie import get_ramdom_ua
from extra.logger_ import logger


CHITU_USER_API = "https://kf.topchitu.com/api/user"
CHITU_EXPORT_API = "https://kf.topchitu.com/api/export/"
CHITU_EXPORT_STATUS_API = "https://kf.topchitu.com/api/export/?"
CHITU_EXPORT_DOWNLOAD_API = "https://kf.topchitu.com/api/export/download?"
CHITU_EXPORT_VERIFY_INFO_API = (
    "https://kf.topchitu.com/api/export-verify/export-verify-info"
)
CHITU_VERIFY_PASSWORD_API = "https://kf.topchitu.com/api/export-verify/verify-password"


class ChituAPIError(RuntimeError):
    """赤兔 API 基础异常。"""


class ChituCookieError(ChituAPIError):
    """赤兔 Cookie 缺失或失效。"""


class ChituExportVerifyError(ChituAPIError):
    """赤兔导出校验失败。"""


class ChituReportError(ChituAPIError):
    """赤兔报表配置或导出失败。"""


class ChituBaseAPI:
    def __init__(self, cookie, password=None, shop_name=None, verify_export=True):
        self.cookie = cookie
        self.password = password
        self.shop_name = shop_name
        self.current_user = self.fetch_user()
        self.verify_status = False
        if verify_export:
            self.verify_status = self.ensure_export_verified()

    def _headers(self, extra_headers=None):
        headers = {"User-Agent": get_ramdom_ua(), "cookie": self.cookie}
        if extra_headers:
            headers.update(extra_headers)
        return headers

    @staticmethod
    def _summarize_response(response):
        text = response.text.replace("\n", " ").strip()
        return text[:300]

    def _log_response(self, response, context):
        if response.status_code == 200:
            logger.success(f"{self.shop_name} 赤兔 {context} 请求成功: 200")
            return
        logger.error(
            f"{self.shop_name} 赤兔 {context} 请求失败: "
            f"{response.status_code}, {self._summarize_response(response)}"
        )

    def _get_json(self, url, context, params=None, timeout=30, headers=None):
        response = requests.get(
            url,
            params=params,
            headers=self._headers(headers),
            timeout=timeout,
        )
        self._log_response(response, context)
        if response.status_code != 200:
            raise ChituAPIError(f"{context} 请求失败: {response.status_code}")
        return response.json()

    def _post_json(self, url, context, data, timeout=30, headers=None):
        request_headers = self._headers({"content-type": "application/json"})
        if headers:
            request_headers.update(headers)
        response = requests.post(
            url,
            data=json.dumps(data),
            headers=request_headers,
            timeout=timeout,
        )
        self._log_response(response, context)
        return response

    def fetch_user(self):
        if not self.cookie:
            raise ChituCookieError(f"{self.shop_name} 赤兔 Cookie 为空")

        try:
            response_json = self._get_json(CHITU_USER_API, "用户校验")
        except Exception as exc:
            raise ChituCookieError(f"{self.shop_name} 赤兔 Cookie 校验失败") from exc

        current_user = response_json.get("currentUser")
        if not current_user:
            raise ChituCookieError(f"{self.shop_name} 赤兔 Cookie 已失效")

        logger.success(f"{self.shop_name} 赤兔 Cookie 校验成功")
        return current_user

    def fetch_export_verify_status(self):
        response_json = self._get_json(CHITU_EXPORT_VERIFY_INFO_API, "导出状态校验")
        return bool(response_json.get("exportVerifyStatus"))

    def verify_password(self):
        if not self.password:
            raise ChituExportVerifyError(f"{self.shop_name} 未配置赤兔导出校验密码")

        response = self._post_json(
            CHITU_VERIFY_PASSWORD_API,
            "导出密码校验",
            {"password": self.password},
        )
        if response.status_code == 200 and not response.text:
            logger.success(f"{self.shop_name} 赤兔导出密码校验成功")
            return True

        logger.error(
            f"{self.shop_name} 赤兔导出密码校验失败: "
            f"{response.status_code}, {self._summarize_response(response)}"
        )
        return False

    def ensure_export_verified(self):
        if self.fetch_export_verify_status():
            logger.success(f"{self.shop_name} 赤兔导出状态已校验")
            return True

        if self.verify_password():
            return True

        raise ChituExportVerifyError(f"{self.shop_name} 赤兔导出校验失败")

    def create_export(self, data):
        response = self._post_json(CHITU_EXPORT_API, "创建导出任务", data)
        if response.status_code != 200:
            raise ChituReportError(f"{self.shop_name} 赤兔创建导出任务失败")

        response_json = response.json()
        task_id = response_json.get("id")
        if not task_id:
            raise ChituReportError(f"{self.shop_name} 赤兔导出任务缺少 id")

        logger.success(f"{self.shop_name} 赤兔正在生成报表, task_id={task_id}")
        self.wait_export_ready(task_id)
        return task_id

    @retry(stop_max_attempt_number=5, wait_fixed=5000)
    def wait_export_ready(self, task_id):
        params = {"taskIds": task_id}
        response_json = self._get_json(
            CHITU_EXPORT_STATUS_API,
            "查询导出任务",
            params=params,
        )
        export_status = response_json[0]["exportStatus"]
        logger.success(f"{self.shop_name} 赤兔报表 task_id={task_id}, 状态={export_status}")
        if export_status == "OK":
            return True
        raise ChituReportError(f"{self.shop_name} 赤兔导出任务未完成: {export_status}")

    def download_export(self, task_id):
        params = {"taskIds": task_id, "_version": 21}
        url = CHITU_EXPORT_DOWNLOAD_API + urlencode(params)
        response = requests.get(url, headers=self._headers(), timeout=60)
        self._log_response(response, "下载导出文件")
        if response.status_code != 200:
            raise ChituReportError(f"{self.shop_name} 赤兔下载导出文件失败")
        return response.content
