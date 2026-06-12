# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一贯
- 创建时间：2026-06-11 06:29:55
- 最近修改：2026-06-11 06:29:55
- 文件用途：封装钉钉自定义群机器人 Webhook 发消息能力，支持文本、Markdown、ActionCard 和 FeedCard。
- 业务范围：适用于本项目任务完成提醒、失败告警、表格预览推送和其他主动群消息推送。
- 依赖入口：使用 requests、extra.extra_reqlog、extra.logger_ 以及 API_DingTalk_Base。
- 验收方式：修改后执行 py_compile；使用无真实请求的类初始化和 payload 构造探针验证导入。
- 注意事项：Webhook 和签名 Secret 只从环境变量或 config/local.json 读取，不在日志中输出完整值。
"""

from typing import Any

import requests

from API.API_DingTalk.API_DingTalk_Base import (
    DEFAULT_TIMEOUT,
    DingTalkApiError,
    build_signed_webhook_url,
    get_config_value,
    load_dingtalk_section,
    require_config_value,
)
from extra.extra_reqlog import req_log
from extra.logger_ import logger


class DingTalkWebhookSender:
    """钉钉自定义机器人 Webhook 发送器。"""

    def __init__(
        self,
        webhook: str | None = None,
        secret: str | None = None,
        *,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        section = load_dingtalk_section()
        self.webhook = require_config_value(
            webhook
            or get_config_value(
                ["DINGTALK_ROBOT_WEBHOOK", "DINGTALK_WEBHOOK"],
                "robot_webhook",
                section=section,
            ),
            "DINGTALK_ROBOT_WEBHOOK / dingtalk.robot_webhook",
        )
        self.secret = secret or get_config_value(
            ["DINGTALK_ROBOT_SECRET", "DINGTALK_SECRET"],
            "robot_secret",
            section=section,
        )
        self.timeout = timeout

    def send_payload(self, payload: dict[str, Any], *, context: str = "钉钉机器人发消息") -> dict[str, Any]:
        """发送原始钉钉机器人 payload。"""
        signed_webhook = build_signed_webhook_url(self.webhook, self.secret)
        try:
            response = requests.post(
                signed_webhook,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.error(f"{context}请求异常：{exc}")
            raise DingTalkApiError(f"{context}请求异常：{exc}") from exc

        req_log(response, context=context, raise_error=True)
        try:
            result = response.json()
        except ValueError as exc:
            raise DingTalkApiError(f"{context}返回不是 JSON：status_code={response.status_code}") from exc

        errcode = result.get("errcode")
        if errcode not in (None, 0):
            errmsg = result.get("errmsg", "")
            raise DingTalkApiError(f"{context}失败：errcode={errcode}, errmsg={errmsg}")
        return result

    def send_text(
        self,
        content: str,
        *,
        at_mobiles: list[str] | None = None,
        is_at_all: bool = False,
    ) -> dict[str, Any]:
        """发送文本消息。"""
        payload = {
            "msgtype": "text",
            "text": {"content": content},
            "at": {"atMobiles": at_mobiles or [], "isAtAll": is_at_all},
        }
        return self.send_payload(payload, context="钉钉机器人发送文本")

    def send_markdown(
        self,
        title: str,
        text: str,
        *,
        at_mobiles: list[str] | None = None,
        is_at_all: bool = False,
    ) -> dict[str, Any]:
        """发送 Markdown 消息。"""
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {"atMobiles": at_mobiles or [], "isAtAll": is_at_all},
        }
        return self.send_payload(payload, context="钉钉机器人发送Markdown")

    def send_action_card(
        self,
        title: str,
        text: str,
        *,
        single_title: str | None = None,
        single_url: str | None = None,
        buttons: list[dict[str, str]] | None = None,
        btn_orientation: str = "0",
    ) -> dict[str, Any]:
        """发送 ActionCard 消息，支持单按钮或多按钮。"""
        action_card: dict[str, Any] = {
            "title": title,
            "text": text,
            "btnOrientation": btn_orientation,
        }
        if buttons:
            action_card["btns"] = buttons
        else:
            action_card["singleTitle"] = single_title or "查看详情"
            action_card["singleURL"] = single_url or ""

        payload = {"msgtype": "actionCard", "actionCard": action_card}
        return self.send_payload(payload, context="钉钉机器人发送ActionCard")

    def send_feed_card(self, links: list[dict[str, str]]) -> dict[str, Any]:
        """发送 FeedCard 消息。"""
        payload = {"msgtype": "feedCard", "feedCard": {"links": links}}
        return self.send_payload(payload, context="钉钉机器人发送FeedCard")
