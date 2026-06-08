import json
import os

from config.local_config import get_local_section


def get_chitu_password(shop_name):
    local_config = get_local_section("chitu")
    local_passwords = local_config.get("passwords", {})
    if local_passwords and not isinstance(local_passwords, dict):
        raise RuntimeError("本地配置 chitu.passwords 必须是对象。")
    password = local_passwords.get(shop_name)
    if password:
        return password

    password = local_config.get("default_password")
    if password:
        return password

    raw_mapping = os.environ.get("CHITU_PASSWORDS_JSON", "")
    if raw_mapping:
        try:
            mapping = json.loads(raw_mapping)
        except json.JSONDecodeError as exc:
            raise RuntimeError("CHITU_PASSWORDS_JSON 不是合法 JSON。") from exc
        password = mapping.get(shop_name)
        if password:
            return password

    password = os.environ.get("CHITU_PASSWORD")
    if password:
        return password

    raise RuntimeError(f"缺少赤兔导出校验密码: {shop_name}")
