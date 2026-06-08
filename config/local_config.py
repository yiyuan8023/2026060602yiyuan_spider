import json
from functools import lru_cache
from pathlib import Path

LOCAL_CONFIG_PATH = Path(__file__).with_name("local.json")


@lru_cache(maxsize=1)
def load_local_config():
    if not LOCAL_CONFIG_PATH.exists():
        return {}
    try:
        with LOCAL_CONFIG_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"本地配置文件格式错误: {LOCAL_CONFIG_PATH}") from exc


def get_local_section(section_name):
    section = load_local_config().get(section_name, {})
    if not isinstance(section, dict):
        raise RuntimeError(f"本地配置项 {section_name} 必须是对象。")
    return section
