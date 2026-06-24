#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-15 17:24:32
- 最近修改：2026-06-15 17:54:03
- 文件用途：提供淘宝人工介入登录任务辅助能力，负责合并 jobs 配置、本地账号密码配置和单店铺执行参数。
- 业务范围：适用于 jobs_login/taobao_manual_shop_cookie.py 的人工介入 Cookie 刷新任务。
- 依赖入口：config.local_config.get_local_section、extra.logger_、taobao_login_manual.capture_manual_login_cookie。
- 验收方式：修改后执行 py_compile 和只读配置解析探针；真实运行需由 jobs 脚本指定店铺后人工验证。
- 注意事项：本文件会读取本地账号密码配置，但不得打印密码、完整 Cookie 或数据库敏感配置。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config.local_config import get_local_section
from extra.logger_ import logger

try:
    from ..API_TaoXi_SYCM_login import DEFAULT_COOKIE_SITE
except ImportError:
    from API_login.API_TaoXi_login.API_TaoXi_SYCM_login import DEFAULT_COOKIE_SITE
try:
    from ..auto_login.taobao_login_auto import DEFAULT_OUTPUT_DIR
except ImportError:
    from API_login.API_TaoXi_login.auto_login.taobao_login_auto import DEFAULT_OUTPUT_DIR
from .taobao_login_manual import capture_manual_login_cookie


DEFAULT_TABLE_NAME = "get_cookie"


def normalize_shop_configs(raw_shops: Any, defaults: dict[str, Any]) -> list[dict[str, Any]]:
    """支持 local.json 中 shops 使用列表、字典或店铺名字符串。"""
    if isinstance(raw_shops, dict):
        raw_items = []
        for shop_name, shop_config in raw_shops.items():
            if isinstance(shop_config, dict):
                raw_items.append({"shop_name": shop_name, **shop_config})
            else:
                raw_items.append({"shop_name": shop_name})
    elif isinstance(raw_shops, list):
        raw_items = raw_shops
    else:
        raw_items = []

    shop_configs: list[dict[str, Any]] = []
    for raw_item in raw_items:
        if isinstance(raw_item, str):
            raw_config = {"shop_name": raw_item}
        elif isinstance(raw_item, dict):
            raw_config = raw_item.copy()
        else:
            raise RuntimeError("config/local.json 的 taobao_login.shops 仅支持对象、列表或店铺名字符串")

        if not raw_config.get("shop_name"):
            raise RuntimeError("config/local.json 的 taobao_login.shops 存在缺少 shop_name 的配置")
        shop_configs.append({**defaults, **raw_config})
    return shop_configs


def pick_task_shop_configs(
    local_shop_configs: list[dict[str, Any]],
    selected_shops: list[str | dict[str, Any]],
) -> list[dict[str, Any]]:
    """按 jobs 的 TASK_CONFIG.shops 选择本次人工介入店铺，并从 local.json 补齐账号密码。"""
    shop_config_by_name = {str(item.get("shop_name")): item for item in local_shop_configs if item.get("shop_name")}
    task_shop_configs: list[dict[str, Any]] = []
    missing_shop_names = []

    for selected_shop in selected_shops:
        if isinstance(selected_shop, str):
            selected_config = {"shop_name": selected_shop}
        elif isinstance(selected_shop, dict):
            selected_config = selected_shop.copy()
        else:
            raise RuntimeError("TASK_CONFIG.shops 仅支持店铺名字符串或店铺配置对象")

        shop_name = str(selected_config.get("shop_name") or "").strip()
        if not shop_name:
            raise RuntimeError("TASK_CONFIG.shops 存在缺少 shop_name 的配置")

        local_shop_config = shop_config_by_name.get(shop_name)
        if not local_shop_config:
            missing_shop_names.append(shop_name)
            continue
        task_shop_configs.append({**local_shop_config, **selected_config})

    if missing_shop_names:
        available = "、".join(shop_config_by_name)
        missing = "、".join(missing_shop_names)
        raise RuntimeError(f"TASK_CONFIG.shops 中的店铺未在 config/local.json 配置账号密码：{missing}；可选店铺：{available}")
    return task_shop_configs


def load_manual_task_config(
    job_task_config: dict[str, Any],
    selected_shop_name: str | None = None,
) -> dict[str, Any]:
    """读取 local.json 的账号密码，并按 jobs 的 TASK_CONFIG 或命令行选择本次处理店铺。"""
    local_config = get_local_section("taobao_login")
    if not local_config:
        raise RuntimeError("config/local.json 未配置 taobao_login")

    defaults = local_config.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise RuntimeError("config/local.json 的 taobao_login.defaults 必须是对象")

    local_shop_configs = normalize_shop_configs(local_config.get("shops"), defaults)
    if not local_shop_configs:
        raise RuntimeError("config/local.json 的 taobao_login.shops 未配置店铺")

    selected_shops: list[str | dict[str, Any]]
    if selected_shop_name:
        selected_shops = [selected_shop_name]
    else:
        selected_shops = job_task_config.get("shops") or [str(item["shop_name"]) for item in local_shop_configs]

    task_config = job_task_config.copy()
    task_config["table_name"] = job_task_config.get("table_name") or local_config.get("table_name", DEFAULT_TABLE_NAME)
    task_config["site"] = job_task_config.get("site") or local_config.get("site", DEFAULT_COOKIE_SITE)
    task_config["manual_timeout"] = int(
        job_task_config.get("manual_timeout")
        or local_config.get("manual_timeout")
        or defaults.get("manual_timeout", 300)
    )
    task_config["shops"] = pick_task_shop_configs(local_shop_configs, selected_shops)
    return task_config


def require_login_fields(shop_config: dict[str, Any]) -> tuple[str, str, str]:
    """校验单店铺人工登录所需账号密码字段。"""
    shop_name = str(shop_config.get("shop_name") or "").strip()
    login_id = str(shop_config.get("login_id") or "").strip()
    password = str(shop_config.get("password") or "")
    if not shop_name:
        raise RuntimeError("店铺配置缺少 shop_name")
    if not login_id:
        raise RuntimeError(f"{shop_name} 缺少 login_id，请在 config/local.json 配置完整登录账号")
    if not password:
        raise RuntimeError(f"{shop_name} 缺少 password，请在 config/local.json 配置登录密码")
    return shop_name, login_id, password


def run_manual_shop_cookie(
    task_config: dict[str, Any],
    shop_config: dict[str, Any],
    *,
    save_database: bool = True,
    save_local: bool = False,
    output_dir: Path | str | None = None,
    manual_timeout: int | None = None,
) -> dict[str, Any]:
    """执行单店铺人工介入登录 Cookie 保存。"""
    shop_name, login_id, password = require_login_fields(shop_config)
    timeout = int(manual_timeout or shop_config.get("manual_timeout") or task_config["manual_timeout"])
    site = str(shop_config.get("site") or task_config["site"])

    logger.info(f"{shop_name} 开始人工介入淘宝登录 Cookie 保存，站点={site}，目标表={task_config['table_name']}")
    result = capture_manual_login_cookie(
        shop_name=shop_name,
        login_id=login_id,
        password=password,
        site=site,
        save_database=save_database,
        save_local=save_local,
        output_dir=Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR,
        manual_timeout=timeout,
        yingdao_account=shop_config.get("yingdao_account"),
        maintainer_email=shop_config.get("maintainer_email"),
    )

    status = result.get("status")
    if status != "success":
        raise RuntimeError(f"{shop_name} 人工介入淘宝登录 Cookie 保存失败，状态={status}")

    logger.info(
        f"{shop_name} 人工介入淘宝登录 Cookie 保存完成，"
        f"Cookie 数量={result.get('cookie_count', 0)}，写库={result.get('saved_to_db')}，"
        f"本地保存={result.get('saved_local')}"
    )
    return result
