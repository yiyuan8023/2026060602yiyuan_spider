# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一贯
- 创建时间：2026-06-11 06:29:55
- 最近修改：2026-06-11 06:29:55
- 文件用途：暴露钉钉 API 包的基础配置、Webhook 发消息、Stream 回复、在线表格读取和任务通知能力。
- 业务范围：适用于本项目内需要调用钉钉机器人、钉钉文档表格和任务异常通知的 Python 模块。
- 依赖入口：使用 API_DingTalk_Base、API_DingTalk_Message、API_DingTalk_Notify、API_DingTalk_Reply、API_DingTalk_Sheet。
- 验收方式：修改后执行 py_compile，并执行 API.API_DingTalk 包导入探针。
- 注意事项：不要在包入口写入真实 Webhook、Secret、AppKey、AppSecret 或 sessionWebhook。
"""

from API.API_DingTalk.API_DingTalk_Base import DingTalkApiError, DingTalkConfigError
from API.API_DingTalk.API_DingTalk_Message import DingTalkWebhookSender
from API.API_DingTalk.API_DingTalk_Notify import DingTalkJobNotifier
from API.API_DingTalk.API_DingTalk_Sheet import DingTalkSheetClient

__all__ = [
    "DingTalkApiError",
    "DingTalkConfigError",
    "DingTalkWebhookSender",
    "DingTalkJobNotifier",
    "DingTalkSheetClient",
]
