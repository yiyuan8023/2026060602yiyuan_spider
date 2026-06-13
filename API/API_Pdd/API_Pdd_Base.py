# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:38
- 最近修改：2026-06-08 13:47:18
- 文件用途：提供拼多多商家后台请求、anti_content 生成、字体反爬规则获取和字体映射识别等基础能力。
- 业务范围：适用于 API_Pdd 下数据中心各能力模块，具体接口和业务字段由能力文件与 parser 文件负责。
- 依赖入口：使用 requests、execjs、ddddocr、PIL、fontTools、cookie_manager.extra_cookie、extra.extra_reqlog 和 extra.logger_。
- 验收方式：修改后执行 py_compile 和 API_Pdd 包导入探针；真实请求由具体任务脚本做单店铺单日期验证。
- 注意事项：基础层不处理最终表名、店铺列表、日期循环和数据库入库；日志不得输出完整 Cookie、签名参数或下载 URL。
"""

import io
import json
import os
import subprocess
from typing import Any, Dict, Optional

import ddddocr
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
import requests
from retrying import retry

from config import UA
from cookie_manager.extra_cookie import get_ramdom_ua
from extra.extra_reqlog import req_log
from extra.logger_ import logger


import execjs  # noqa


REQUEST_TIMEOUT = (5, 30)


class PddBaseApi:
    """拼多多基础能力，负责请求封装、anti_content 和字体反爬映射。"""

    def __init__(self, cookie: Optional[str] = None, shop_name: Optional[str] = None):
        self.cookie = cookie or ""
        self.shop_name = shop_name
        self._font_mapping_cache: Dict[str, Dict[str, str]] = {}
        current_dir = os.path.dirname(os.path.abspath(__file__))
        js_file_path = os.path.join(current_dir, "anti_content.js")
        logger.info(f"加载拼多多 anti_content 脚本: {js_file_path}")

        with open(js_file_path, "r", encoding="utf8") as js_file:
            self.context = self._compile_execjs(js_file.read())

    @staticmethod
    def _with_utf8_popen(callback):
        """只在执行 PyExecJS 相关动作时临时修正子进程编码。"""
        original_popen = subprocess.Popen

        def popen_with_utf8(*args, **kwargs):
            kwargs.setdefault("encoding", "utf-8")
            return original_popen(*args, **kwargs)

        subprocess.Popen = popen_with_utf8
        try:
            return callback()
        finally:
            subprocess.Popen = original_popen

    @classmethod
    def _compile_execjs(cls, js_code: str):
        """局部编译 anti_content，避免全局修改 subprocess.Popen。"""
        return cls._with_utf8_popen(lambda: execjs.compile(js_code))

    def get_anti_content(self) -> str:
        """获取拼多多接口 Anti-Content 参数。"""
        return self._with_utf8_popen(lambda: self.context.call("get_anti_content"))

    def build_headers(
        self,
        *,
        need_anti_content: bool = False,
        web_spider_rule: Optional[str] = None,
    ) -> Dict[str, str]:
        """构造通用请求头，必要时补充 anti_content 和字体规则。"""
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Cookie": self.cookie,
        }
        if need_anti_content:
            headers["Anti-Content"] = self.get_anti_content()
        if web_spider_rule:
            headers["Webspiderrule"] = web_spider_rule
        return headers

    def post_json(
        self,
        url: str,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
        context: str,
    ) -> Optional[Dict[str, Any]]:
        """发送 JSON POST 请求，只返回平台原始 JSON。"""
        try:
            response = requests.post(
                url=url,
                data=json.dumps(payload, ensure_ascii=False),
                headers=headers or self.build_headers(),
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.error(f"{context} 请求异常，已跳过解析：{exc}")
            return None

        req_log(response, context=context)
        if response.status_code != 200:
            logger.warning(f"{context} 请求失败，状态码：{response.status_code}")
            return None

        try:
            return response.json()
        except ValueError:
            logger.error(f"{context} 返回内容不是 JSON，已跳过解析")
            return None

    def get_json(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        context: str,
    ) -> Optional[Dict[str, Any]]:
        """发送 JSON GET 请求，只返回平台原始 JSON。"""
        try:
            response = requests.get(
                url=url,
                params=params,
                headers=headers or self.build_headers(),
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.error(f"{context} 请求异常，已跳过解析：{exc}")
            return None

        req_log(response, context=context)
        if response.status_code != 200:
            logger.warning(f"{context} 请求失败，状态码：{response.status_code}")
            return None

        try:
            return response.json()
        except ValueError:
            logger.error(f"{context} 返回内容不是 JSON，已跳过解析")
            return None

    @logger.catch
    def get_web_spider_rule(self) -> Optional[Dict[str, Optional[str]]]:
        """获取 web_spider_rule 参数和 ttf 字体链接。"""
        api = "https://api.yangkeduo.com/api/phantom/web/en/ft"
        payload = {"scene": "cp_b_data_center"}
        try:
            response = requests.post(
                url=api,
                data=json.dumps(payload),
                headers={"User-Agent": get_ramdom_ua()},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.error(f"拼多多字体反爬规则请求异常：{exc}")
            return None

        req_log(response, context="拼多多字体反爬规则")
        if response.status_code != 200:
            logger.warning(f"拼多多字体反爬规则请求失败，状态码：{response.status_code}")
            return None

        try:
            response_json = response.json()
        except ValueError:
            logger.error("拼多多字体反爬规则返回内容不是 JSON")
            return None
        return {
            "web_spider_rule": response_json.get("web_spider_rule"),
            "ttf_url": response_json.get("ttf_url"),
        }

    def build_font_headers_and_mapping(self) -> tuple[Dict[str, str], Dict[str, str]]:
        """为字体混淆接口准备请求头和字体映射。"""
        rule_data = self.get_web_spider_rule() or {}
        web_spider_rule = rule_data.get("web_spider_rule")
        ttf_url = rule_data.get("ttf_url")
        headers = self.build_headers(
            need_anti_content=True,
            web_spider_rule=web_spider_rule,
        )
        font_mapping = self.get_cached_font_mapping(ttf_url) if ttf_url else {}
        return headers, font_mapping

    def get_cached_font_mapping(self, ttf_url: str) -> Dict[str, str]:
        """同一个 API 实例内按 ttf_url 复用字体映射，避免分页重复 OCR。"""
        if ttf_url not in self._font_mapping_cache:
            self._font_mapping_cache[ttf_url] = self.get_font_mapping(ttf_url) or {}
        else:
            logger.info("复用拼多多字体映射缓存")
        return self._font_mapping_cache[ttf_url]

    @logger.catch
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def get_font_mapping(self, ttf_url: str) -> Dict[str, str]:
        """解析 ttf 中字体的映射关系。"""
        try:
            response = requests.get(
                url=ttf_url,
                headers={"User-Agent": get_ramdom_ua()},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.error(f"拼多多字体文件下载异常：{exc}")
            raise

        req_log(response, context="拼多多字体文件", log_success=False, raise_error=True)
        font_bytes = io.BytesIO(response.content)
        font = TTFont(font_bytes)
        ocr = ddddocr.DdddOcr()
        unicode_names = font.getGlyphOrder()[2:]
        char_keys = []
        char_values = []

        font_bytes.seek(0)
        image_font = ImageFont.truetype(font_bytes, 40)
        # 平台用自定义字体混淆数字，这里把 glyph 渲染成图片后交给 OCR 识别。
        for unicode_name in unicode_names:
            unknown_char = f"\\u{unicode_name[3:]}".encode("utf8").decode("unicode_escape")
            image = Image.new(mode="RGB", size=(42, 40), color="white")
            draw = ImageDraw.Draw(im=image)
            draw.text(xy=(0, 0), text=unknown_char, fill=0, font=image_font)
            image_byte = io.BytesIO()
            image.save(image_byte, format="JPEG")
            unicode_key = unicode_name[3:].lower()
            char_keys.append(r"\u" + unicode_key)
            char_values.append(ocr.classification(image_byte.getvalue()))

        font_mapping = dict(zip(char_keys, char_values))
        logger.info(f"拼多多字体映射识别完成，共 {len(font_mapping)} 个 glyph")
        return font_mapping
