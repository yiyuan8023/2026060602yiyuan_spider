from typing import Optional

import chardet


def detect_text_encoding(file_content: bytes) -> Optional[str]:
    """检测文本文件的编码，检测失败时返回 None，让 pandas 使用默认策略。"""
    result = chardet.detect(file_content)
    return result.get("encoding")
