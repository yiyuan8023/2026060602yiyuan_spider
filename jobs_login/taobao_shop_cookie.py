"""
开发说明：
- 作者：一元
- 创建时间：2026-06-15 14:36:14
- 最近修改：2026-06-15 15:35:54
- 文件用途：启动淘宝卖家后台登录 Cookie 准备任务，优先复用 cookie 视图，失效后刷新并写入 get_cookie。
- 业务范围：适用于淘系生意参谋/卖家后台 Cookie 登录态准备，默认处理脚本内配置的店铺。
- 依赖入口：调用 extra.select_shop_date.select_shop_date 获取数据库 Cookie，调用 API_login.API_TaoXi_login.API_TaoXi_SYCM_login.prepare_sycm_cookie 执行验证、登录和写库。
- 验收方式：修改后执行 py_compile 和导入探针；真实运行时先单店铺验证 Cookie 复用、失效刷新和 get_cookie 写入。
- 注意事项：日志不得输出真实 Cookie、账号密码或数据库敏感配置；正式运行建议通过 run_job.py 启动。
"""

from __future__ import annotations

from typing import Any

from API.API_DingTalk.API_DingTalk_Notify import DingTalkJobNotifier
from API_login.API_TaoXi_login.API_TaoXi_SYCM_login import prepare_sycm_cookie
from config.local_config import get_local_section
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

TABLE_NAME = "get_cookie"
SITE = "生意参谋"

TASK_CONFIG = {
    "table_name": TABLE_NAME,
    "site": SITE,
    "recent_days": 1,
    "shops": ["林内官方旗舰店", "林内热水器旗舰店", "林内品牌折扣店", "智慧家电直销店", "林内厨电旗舰店"],
}


def normalize_shop_configs(raw_shops, defaults: dict[str, Any]) -> list[dict[str, Any]]:
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

    shop_configs = []
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


def load_task_config() -> dict[str, Any]:
    """读取 config/local.json 中的 taobao_login 多店铺配置。"""
    local_config = get_local_section("taobao_login")
    task_config = TASK_CONFIG.copy()
    if not local_config:
        logger.warning("config/local.json 未配置 taobao_login，将不执行任何店铺")
        return task_config

    defaults = local_config.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise RuntimeError("config/local.json 的 taobao_login.defaults 必须是对象")

    for key in ("table_name", "site", "recent_days"):
        if key in local_config:
            task_config[key] = local_config[key]

    task_config["shops"] = normalize_shop_configs(local_config.get("shops"), defaults)
    return task_config


def find_shop_cookie_row(shop_cookies, shop_name: str):
    """从 select_shop_date 返回结果中找当前店铺 Cookie 行。"""
    for row in shop_cookies:
        if row and row[0] == shop_name:
            return row
    return shop_cookies[0] if shop_cookies else None


def require_login_id(shop_config: dict[str, Any], shop_name: str) -> str:
    """登录配置只接受完整 login_id，例如 主账号:子账号。"""
    if shop_config.get("login_id"):
        return str(shop_config["login_id"])
    raise RuntimeError(f"{shop_name} 缺少 login_id，请在 config/local.json 配置完整登录账号")


def build_dingtalk_notifier() -> DingTalkJobNotifier:
    """初始化钉钉通知器，配置异常不能影响登录任务继续执行。"""
    try:
        return DingTalkJobNotifier.from_config()
    except Exception as exc:
        logger.warning(f"钉钉通知初始化失败，已跳过本次任务通知：{type(exc).__name__}: {exc}")
        return DingTalkJobNotifier(enabled=False)


def notify_shop_failure(
        notifier: DingTalkJobNotifier,
        task_config: dict[str, Any],
        shop_name: str,
        error_message: str,
) -> None:
    """发送单店铺失败通知；通知失败只记录日志，不阻断后续店铺。"""
    if not notifier.enabled:
        return

    safe_error = error_message.replace("\n", " ")[:800]
    title = f"淘宝登录 Cookie 失败：{shop_name}"
    text = (
        f"### {title}\n\n"
        f"- 任务：`jobs_login/taobao_shop_cookie.py`\n"
        f"- 站点：{task_config.get('site')}\n"
        f"- 店铺：{shop_name}\n"
        f"- 目标表：`{task_config.get('table_name')}`\n"
        f"- 异常摘要：{safe_error}\n"
    )
    try:
        notifier.send_markdown(title, text)
    except Exception as exc:
        logger.warning(f"{shop_name} 钉钉失败通知发送失败：{type(exc).__name__}: {exc}")


def run_one_shop(task_config: dict[str, Any], shop_config: dict[str, Any]) -> dict[str, Any]:
    table_name = task_config["table_name"]
    site = task_config["site"]
    recent_days = int(shop_config.get("recent_days", task_config["recent_days"]))
    shop_name = shop_config["shop_name"]

    logger.info(f"{shop_name} 开始准备淘宝登录 Cookie，目标写入=get_cookie")

    shop_cookies, _crawl_day_list = select_shop_date(
        table_name,
        site,
        [shop_name],
        recent_days,
    )
    cookie_row = find_shop_cookie_row(shop_cookies, shop_name)
    db_cookie_str = cookie_row[1] if cookie_row else None
    db_cookie = cookie_row[2] if cookie_row else None

    result = prepare_sycm_cookie(
        shop_name=shop_name,
        login_id=require_login_id(shop_config, shop_name),
        password=shop_config.get("password") or "",
        db_cookie_str=db_cookie_str,
        db_cookie=db_cookie,
        site=site,
        save_local=False,
        timeout=shop_config.get("timeout"),
        max_retries=shop_config.get("max_retries"),
        retry_delay=shop_config.get("retry_delay"),
        validate_url=shop_config.get("validate_url"),
        user_agent=shop_config.get("user_agent"),
        yingdao_account=shop_config.get("yingdao_account"),
        maintainer_email=shop_config.get("maintainer_email"),
    )

    status = result.get("status")
    if status not in {"success", "db_cookie_valid"}:
        raise RuntimeError(f"{shop_name} 淘宝登录 Cookie 准备失败，状态={status}")

    logger.info(
        f"{shop_name} 淘宝登录 Cookie 准备完成，状态={status}，"
        f"Cookie 数量={result.get('cookie_count', 0)}，写库={result.get('saved_to_db')}"
    )
    return result


def main() -> None:
    task_config = load_task_config()
    if not task_config["shops"]:
        raise RuntimeError("未找到淘宝登录店铺配置，请在 config/local.json 的 taobao_login.shops 中配置")

    results = []
    failed_results = []
    notifier = build_dingtalk_notifier()
    for shop_config in task_config["shops"]:
        shop_name = shop_config.get("shop_name") or "未知店铺"
        try:
            results.append(run_one_shop(task_config, shop_config))
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            logger.error(f"{shop_name} 淘宝登录 Cookie 准备失败，已跳过继续下一个店铺：{error_message}")
            notify_shop_failure(notifier, task_config, shop_name, error_message)
            failed_results.append({"shop_name": shop_name, "error": error_message})
            continue

    logger.info(
        f"淘宝登录 Cookie 准备任务完成，总店铺数={len(task_config['shops'])}，"
        f"成功={len(results)}，失败={len(failed_results)}"
    )
    if failed_results:
        failed_names = "、".join(item["shop_name"] for item in failed_results)
        logger.warning(f"淘宝登录 Cookie 准备失败店铺：{failed_names}")


if __name__ == "__main__":
    main()
