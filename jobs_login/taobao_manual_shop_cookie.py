"""
开发说明：
- 作者：一元
- 创建时间：2026-06-15 17:24:32
- 最近修改：2026-06-15 17:54:03
- 文件用途：启动淘宝登录人工介入 Cookie 准备任务，按 TASK_CONFIG 选择店铺并调用 API 层执行。
- 业务范围：适用于淘系生意参谋/卖家后台 Cookie 手动刷新场景，默认按 TASK_CONFIG.shops 逐店写入 get_cookie。
- 依赖入口：调用 API_login.API_TaoXi_login.taobao_manual_task 解析本地账号密码配置并执行人工介入 Cookie 保存。
- 验收方式：修改后执行 py_compile；真实运行时建议先把 TASK_CONFIG.shops 缩到单店铺验证 get_cookie 写入。
- 注意事项：本脚本会打开可见浏览器；日志不得输出真实密码、完整 Cookie 或数据库敏感配置。
"""

from __future__ import annotations

import argparse
from pathlib import Path


from API_login.API_TaoXi_login.taobao_login import DEFAULT_COOKIE_SITE
from API_login.API_TaoXi_login.manual_login.taobao_manual_task import (
    DEFAULT_OUTPUT_DIR,
    load_manual_task_config,
    run_manual_shop_cookie,
)
from extra.logger_ import logger


TABLE_NAME = "get_cookie"
SITE = DEFAULT_COOKIE_SITE

TASK_CONFIG = {
    "table_name": TABLE_NAME,
    "site": SITE,
    "recent_days": 1,
    "manual_timeout": 300,
    "shops": [
        "林内官方旗舰店",
        "林内热水器旗舰店",
        "林内品牌折扣店",
        "智慧家电直销店",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="淘宝登录人工介入 Cookie 保存任务")
    parser.add_argument("--shop-name", help="临时覆盖 TASK_CONFIG.shops，只处理指定店铺")
    parser.add_argument("--manual-timeout", type=int, help="人工处理滑块/短信/扫码的最长等待秒数")
    parser.add_argument("--save-local", action="store_true", help="额外保存本地 Cookie JSON/TXT 文件")
    parser.add_argument("--no-db", action="store_true", help="只获取 Cookie，不写入 get_cookie")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="本地 Cookie/截图输出目录")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    task_config = load_manual_task_config(TASK_CONFIG, selected_shop_name=args.shop_name)
    results = []
    failed_results = []

    logger.info(
        f"人工介入淘宝登录 Cookie 任务开始，配置店铺数={len(task_config['shops'])}，"
        f"店铺={','.join(str(item.get('shop_name')) for item in task_config['shops'])}"
    )
    for shop_config in task_config["shops"]:
        shop_name = shop_config.get("shop_name") or "未知店铺"
        try:
            result = run_manual_shop_cookie(
                task_config,
                shop_config,
                save_database=not args.no_db,
                save_local=args.save_local,
                output_dir=Path(args.output_dir),
                manual_timeout=args.manual_timeout,
            )
            results.append(result)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            logger.error(f"{shop_name} 人工介入淘宝登录 Cookie 保存失败，已跳过继续下一个店铺：{error_message}")
            failed_results.append({"shop_name": shop_name, "error": error_message})
            continue

    logger.info(
        f"人工介入淘宝登录 Cookie 任务完成，总店铺数={len(task_config['shops'])}，"
        f"成功={len(results)}，失败={len(failed_results)}"
    )
    if failed_results:
        failed_names = "、".join(item["shop_name"] for item in failed_results)
        raise RuntimeError(f"人工介入淘宝登录 Cookie 存在失败店铺：{failed_names}")


if __name__ == "__main__":
    main()
