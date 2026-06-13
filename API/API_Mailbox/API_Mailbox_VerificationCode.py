# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：Codex
- 创建时间：2026-06-13 19:26:00
- 最近修改：2026-06-13 20:11:17
- 文件用途：提供短信验证码识别和最新验证码邮件定位能力，给后续店铺登录接入复用。
- 业务范围：适用于 163 邮箱短信转发、平台验证码邮件和其他带验证码标题/正文的收件箱读取场景。
- 依赖入口：复用 API_Mailbox_Base 中的 MailboxBaseApi、MailboxMessage 与正文提取能力，使用标准库 dataclasses、re 和 typing。
- 验收方式：修改后执行 py_compile；验证最近邮件验证码提取和最新验证码定位结果。
- 注意事项：返回结果只暴露必要摘要，不在日志中打印完整验证码或完整邮件正文。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Iterable, Optional

from API.API_Mailbox.API_Mailbox_Base import MailboxBaseApi, MailboxMessage


# ==================== 正则表达式模式定义 ====================

# 匹配短信来源标识,格式如【淘宝】、【京东】等
SOURCE_PATTERN = re.compile(r"【([^】]{1,50})】")

# 匹配验证码相关关键词(支持中英文)
KEYWORD_PATTERN = re.compile(
    r"(验证码|校验码|动态码|确认码|短信码|随机码|verification code|verify code|otp|code)",
    re.IGNORECASE,
)

# 验证码提取模式元组:
# 1. 前向匹配: "验证码" + 分隔符(最多12个非字母数字字符) + 验证码(4-8位字母数字)
# 2. 后向匹配: 验证码(4-8位字母数字) + 分隔符 + "验证码"
CODE_PATTERNS = (
    # 模式1: 关键词在前,验证码在后
    re.compile(
        r"(?:验证码|校验码|动态码|确认码|短信码|随机码|verification code|verify code|otp|code)"
        r"[^0-9A-Za-z]{0,12}([0-9A-Za-z]{4,8})",
        re.IGNORECASE,
    ),
    # 模式2: 验证码在前,关键词在后
    re.compile(
        r"\b([0-9A-Za-z]{4,8})\b[^0-9A-Za-z]{0,12}"
        r"(?:验证码|校验码|动态码|确认码|短信码|随机码|verification code|verify code|otp|code)",
        re.IGNORECASE,
    ),
)

# 备用数字匹配模式:当找到关键词但未匹配到标准验证码格式时,提取4-8位纯数字
FALLBACK_DIGIT_PATTERN = re.compile(r"\b(\d{4,8})\b")

# 密码相关关键词匹配
PASSWORD_KEYWORD_PATTERN = re.compile(r"(密码|解压密码|提取密码)", re.IGNORECASE)

# 密码提取模式元组:
# 1. 前向匹配: "密码" + 分隔符 + 密码(4-32位字母数字)
# 2. 后向匹配: 密码(4-32位字母数字) + 分隔符 + "密码"
PASSWORD_PATTERNS = (
    re.compile(r"(?:解压密码|提取密码|密码)[^0-9A-Za-z]{0,12}([0-9A-Za-z]{4,32})", re.IGNORECASE),
    re.compile(r"([0-9A-Za-z]{4,32})[^0-9A-Za-z]{0,12}(?:解压密码|提取密码|密码)", re.IGNORECASE),
)


@dataclass
class VerificationCodeMatch:
    """命中的验证码邮件信息数据类。
    
    用于存储从邮件中提取到的完整验证码信息,包括验证码本身、发件人、主题等元数据。
    """

    code: str  # 提取到的验证码
    sender: str  # 发件人地址或名称
    subject: str  # 邮件主题
    sent_at: Optional[str]  # 邮件发送时间
    uid: str  # 邮件唯一标识符
    body_summary: str  # 邮件正文摘要

    def to_dict(self) -> dict:
        """将数据类实例转换为字典格式,便于序列化输出。"""
        return asdict(self)


@dataclass
class VerificationCodeExtractResult:
    """单条文本验证码提取结果数据类。
    
    用于存储从短信或邮件文本中提取的验证码及其来源信息。
    """

    source: str  # 验证码来源(如"淘宝"、"京东"等)
    code: str  # 提取到的验证码
    sent_at: Optional[str] = None  # 可选的发送时间戳

    def to_dict(self) -> dict:
        """将数据类实例转换为字典格式。"""
        return asdict(self)


@dataclass
class PasswordExtractResult:
    """单条文本密码提取结果数据类。
    
    用于存储从短信或邮件文本中提取的密码及其来源信息。
    """

    source: str  # 密码来源(如"淘宝"、"京东"等)
    password: str  # 提取到的密码
    sent_at: Optional[str] = None  # 可选的发送时间戳

    def to_dict(self) -> dict:
        """将数据类实例转换为字典格式。"""
        return asdict(self)


def _extract_code_candidates(text: str) -> Iterable[str]:
    """从文本中提取所有可能的验证码候选值。
    
    提取策略:
    1. 首先尝试使用 CODE_PATTERNS 进行精确匹配(关键词+验证码组合)
    2. 如果未找到,但文本中包含验证码关键词,则使用备用模式提取4-8位数字
    
    Args:
        text: 待提取的文本内容(邮件主题、正文等)
        
    Returns:
        验证码候选值列表,按匹配优先级排序
    """
    if not text:
        return []

    candidates: list[str] = []
    # 第一阶段:使用精确模式匹配
    for pattern in CODE_PATTERNS:
        for match in pattern.finditer(text):
            candidates.append(match.group(1))

    # 如果找到候选值,直接返回
    if candidates:
        return candidates

    # 第二阶段:如果文本包含关键词但未匹配到标准格式,尝试提取纯数字
    if KEYWORD_PATTERN.search(text):
        for match in FALLBACK_DIGIT_PATTERN.finditer(text):
            candidates.append(match.group(1))

    return candidates


def extract_source(text: str) -> str:
    """从文本中提取短信/邮件的来源标识。
    
    优先匹配【】格式的來源标识,如【淘宝】、【京东】等。
    
    Args:
        text: 待提取的文本内容
        
    Returns:
        提取到的来源字符串,如果未找到则返回空字符串
    """
    match = SOURCE_PATTERN.search(text or "")
    return match.group(1).strip() if match else ""


def extract_verification_code(subject: str, body_text: str) -> Optional[str]:
    """从邮件标题和正文中提取最有可能的验证码。
    
    提取优先级:
    1. 单独从标题中提取
    2. 单独从正文中提取
    3. 从标题+正文的组合文本中提取
    
    过滤规则:排除包含"code"、"verify"、"otp"等英文单词的候选值(避免误匹配)
    
    Args:
        subject: 邮件主题
        body_text: 邮件正文文本
        
    Returns:
        提取到的验证码字符串,如果未找到则返回 None
    """
    subject = subject or ""
    body_text = body_text or ""
    # 合并主题和正文用于后续提取
    combined_text = "\n".join(part for part in (subject, body_text) if part).strip()

    # 按优先级依次尝试从不同文本源中提取
    for source_text in (subject, body_text, combined_text):
        for candidate in _extract_code_candidates(source_text):
            # 过滤掉包含特定英文关键词的候选值(可能是URL或其他非验证码内容)
            if any(keyword in candidate.lower() for keyword in ("code", "verify", "otp")):
                continue
            return candidate
    return None


def extract_verification_code_from_text(
    text: str,
    sent_at: Optional[str] = None,
) -> Optional[VerificationCodeExtractResult]:
    """从单条短信/邮件文本中提取来源和验证码。
    
    Args:
        text: 完整的短信或邮件文本内容
        sent_at: 可选的发送时间戳
        
    Returns:
        验证码提取结果对象,包含来源、验证码和时间信息;如果未找到则返回 None
    """
    normalized = (text or "").strip()
    if not normalized:
        return None

    # 调用核心提取函数(无主题,只有正文)
    code = extract_verification_code("", normalized)
    if not code:
        return None

    # 构建并返回提取结果
    return VerificationCodeExtractResult(
        source=extract_source(normalized),
        code=code,
        sent_at=sent_at,
    )


def _extract_password_candidates(text: str) -> Iterable[str]:
    """从文本中提取所有可能的密码候选值。
    
    使用 PASSWORD_PATTERNS 进行匹配,支持"密码"关键词前后两种位置关系。
    
    Args:
        text: 待提取的文本内容
        
    Returns:
        密码候选值列表
    """
    if not text:
        return []

    candidates: list[str] = []
    for pattern in PASSWORD_PATTERNS:
        for match in pattern.finditer(text):
            candidates.append(match.group(1))
    return candidates


def extract_password_from_text(
    text: str,
    sent_at: Optional[str] = None,
) -> Optional[PasswordExtractResult]:
    """从单条短信/邮件文本中提取来源和密码。
    
    仅在文本包含密码相关关键词(密码、解压密码、提取密码)时才进行提取。
    
    Args:
        text: 完整的短信或邮件文本内容
        sent_at: 可选的发送时间戳
        
    Returns:
        密码提取结果对象,包含来源、密码和时间信息;如果未找到则返回 None
    """
    normalized = (text or "").strip()
    # 快速检查:如果不包含密码关键词,直接返回
    if not normalized or not PASSWORD_KEYWORD_PATTERN.search(normalized):
        return None

    # 提取第一个匹配的密码候选值
    for candidate in _extract_password_candidates(normalized):
        return PasswordExtractResult(
            source=extract_source(normalized),
            password=candidate,
            sent_at=sent_at,
        )
    return None


def extract_verification_code_from_message(
    message: MailboxMessage,
) -> Optional[VerificationCodeExtractResult]:
    """从邮箱 API 返回的单条邮件对象中提取来源和验证码。
    
    整合邮件的主题、正文文本和正文摘要,然后调用文本提取函数。
    
    Args:
        message: 邮件消息对象,包含 subject、body_text、body_summary、sent_at 等字段
        
    Returns:
        验证码提取结果对象;如果未找到则返回 None
    """
    # 合并邮件的各个文本字段
    message_text = "\n".join(
        part for part in (message.subject, message.body_text, message.body_summary) if part
    ).strip()
    return extract_verification_code_from_text(message_text, sent_at=message.sent_at)


def extract_password_from_message(
    message: MailboxMessage,
) -> Optional[PasswordExtractResult]:
    """从邮箱 API 返回的单条邮件对象中提取来源和密码。
    
    整合邮件的主题、正文文本和正文摘要,然后调用文本提取函数。
    
    Args:
        message: 邮件消息对象,包含 subject、body_text、body_summary、sent_at 等字段
        
    Returns:
        密码提取结果对象;如果未找到则返回 None
    """
    # 合并邮件的各个文本字段
    message_text = "\n".join(
        part for part in (message.subject, message.body_text, message.body_summary) if part
    ).strip()
    return extract_password_from_text(message_text, sent_at=message.sent_at)


class MailboxVerificationCodeApi(MailboxBaseApi):
    """验证码提取 API 类。
    
    继承自 MailboxBaseApi,扩展了验证码自动识别和最新验证码定位功能。
    适用于店铺登录、账号验证等需要自动获取验证码的场景。
    """

    def fetch_recent_messages(self, limit: int = 20, mailbox: Optional[str] = None) -> list[MailboxMessage]:
        """读取最近的邮件列表,并自动补充验证码识别结果。
        
        在父类方法的基础上,对每封邮件执行验证码提取,并将结果存储到 message.verification_code 字段。
        
        Args:
            limit: 要读取的最近邮件数量,默认20封
            mailbox: 可选的邮箱标识,用于指定特定邮箱账户
            
        Returns:
            包含验证码识别结果的邮件对象列表
        """
        messages = super().fetch_recent_messages(limit=limit, mailbox=mailbox)
        # 为每封邮件提取验证码并附加到对象上
        for message in messages:
            message.verification_code = extract_verification_code(
                subject=message.subject,
                body_text=message.body_text,
            )
        return messages

    def find_latest_verification_code(
        self,
        limit: int = 20,
        mailbox: Optional[str] = None,
        sender_keyword: Optional[str] = None,
        subject_keyword: Optional[str] = None,
    ) -> Optional[VerificationCodeMatch]:
        """从最近的邮件中查找最新一条包含验证码的邮件。
        
        工作流程:
        1. 获取最近的邮件列表(自动提取验证码)
        2. 根据发件人或主题关键词进行过滤(可选)
        3. 返回第一条包含有效验证码的邮件信息
        
        Args:
            limit: 要扫描的最近邮件数量,默认20封
            mailbox: 可选的邮箱标识
            sender_keyword: 可选的发件人过滤关键词
            subject_keyword: 可选的主题过滤关键词
            
        Returns:
            最新验证码邮件的详细信息对象;如果未找到则返回 None
        """
        # 获取最近的邮件(已自动提取验证码)
        messages = self.fetch_recent_messages(limit=limit, mailbox=mailbox)
        # 应用过滤器缩小搜索范围
        filtered_messages = self.filter_messages(
            messages,
            sender_keyword=sender_keyword,
            subject_keyword=subject_keyword,
        )

        # 遍历过滤后的邮件,返回第一条包含验证码的邮件
        for message in filtered_messages:
            if message.verification_code:
                return VerificationCodeMatch(
                    code=message.verification_code,
                    sender=message.sender,
                    subject=message.subject,
                    sent_at=message.sent_at,
                    uid=message.uid,
                    body_summary=message.body_summary,
                )
        return None


# ==================== 主程序入口:调用示例 ====================
if __name__ == "__main__":
    """演示如何使用验证码提取 API。
    
    包含三个测试场景:
    1. 获取最近邮件并显示摘要
    2. 查找最新的验证码邮件(验证码脱敏显示)
    3. 直接从邮件对象提取验证码和密码
    """
    # 初始化 API 实例
    api = MailboxVerificationCodeApi()
    
    # # 场景1: 获取最近5封邮件并打印摘要
    # recent_messages = api.fetch_recent_messages(limit=5)
    # print("最近 5 封邮件摘要:")
    # print(json.dumps([message.to_dict() for message in recent_messages], ensure_ascii=False, indent=2))

    # 场景2: 查找最新的验证码邮件
    # latest_code = api.find_latest_verification_code(limit=20)
    # if latest_code:
    #     # 验证码脱敏处理:只显示最后2位,其余用*替代
    #     masked_code = "*" * max(len(latest_code.code) - 2, 0) + latest_code.code[-2:]
    #     print("\n最新验证码邮件:")
    #     print(
    #         json.dumps(
    #             {
    #                 "code_masked": masked_code,  # 脱敏后的验证码
    #                 "sender": latest_code.sender,
    #                 "subject": latest_code.subject,
    #                 "sent_at": latest_code.sent_at,
    #                 "uid": latest_code.uid,
    #                 "body_summary": latest_code.body_summary,
    #             },
    #             ensure_ascii=False,
    #             indent=2,
    #         )
    #     )
    # else:
    #     print("\n最近 20 封邮件中未找到验证码。")
    #
    # 场景3: 直接使用提取函数处理邮件对象
    print("\n直接使用邮箱 API 返回结果做提取:")

    recent_messages = api.fetch_recent_messages(limit=50)
    for message in recent_messages:
        # 分别提取验证码和密码
        verification_result = extract_verification_code_from_message(message)
        password_result = extract_password_from_message(message)
        print(verification_result)
        print(password_result)


        # 如果两者都为空,跳过该邮件
        # if not verification_result and not password_result:
        #     continue
        #
        # # 打印提取结果
        # print(
        #     json.dumps(
        #         {
        #             "uid": message.uid,
        #             "subject": message.subject,
        #             "sent_at": message.sent_at,
        #             "verification": (
        #                 verification_result.to_dict() if verification_result else None
        #             ),
        #             "password": password_result.to_dict() if password_result else None,
        #         },
        #         ensure_ascii=False,
        #         indent=2,
        #     )
        # )
