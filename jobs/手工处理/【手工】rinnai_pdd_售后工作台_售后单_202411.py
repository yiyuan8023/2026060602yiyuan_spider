# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-13 00:20:00
- 最近修改：2026-06-13 00:20:00
- 文件用途：读取拼多多售后工作台导出的 Excel 明细，补充店铺字段后写入既有售后单表。
- 业务范围：适用于林内拼多多售后工作台列表页“批量导出”得到的售后单明细文件；当前默认导入少爷提供的 2026-06-12 导出文件。
- 依赖入口：调用 excel_tool.excel_to_db.FileToItems 读取 Excel，使用 database.DBManager 执行 update_insert_data，使用 extra.logger_ 输出日志。
- 验收方式：修改后执行 py_compile；正式写库前先用当前样例文件验证读取行数、主键字段和店铺字段补充结果。
- 注意事项：不在日志中输出完整地址、Cookie、数据库密码等敏感信息；当前脚本是手工导入入口，不负责页面登录、导出任务创建或接口抓包。
"""

from __future__ import annotations

from pathlib import Path

from database import DBManager
from excel_tool.excel_to_db import FileToItems
from extra.logger_ import logger


DB_CONFIG = "rinnai"  # noqa
FILE_PATH = Path(r"E:\1\f7e9050c92a851b0016442ab604b0488_20260612235138.xlsx")
TABLE_NAME = "rinnai_pdd_售后工作台_售后单_202411"  # noqa
PRIMARY_KEY = "售后编号"
SHOP_NAME = "林内官方旗舰店"


def build_write_items(file_path: Path, shop_name: str):
    """读取导出文件并补充入库所需字段。"""
    raw_items = FileToItems(str(file_path)).read_file()
    write_items = []
    for raw_item in raw_items:
        item = dict(raw_item)
        item["店铺名称"] = shop_name
        write_items.append(item)
    return write_items


if __name__ == "__main__":
    logger.info(f"\n{'*' * 120}")
    logger.info(f"开始导入拼多多售后工作台明细，file={FILE_PATH.name}，shop={SHOP_NAME}")

    if not FILE_PATH.exists():
        raise FileNotFoundError(f"导入文件不存在: {FILE_PATH}")

    items_ = build_write_items(FILE_PATH, SHOP_NAME)
    if not items_:
        logger.warning(f"{FILE_PATH.name} 未读取到可入库数据")
    else:
        logger.info(
            f"拼多多售后工作台明细读取完成，rows={len(items_)}，"
            f"columns={list(items_[0].keys())}"
        )
        with DBManager(db_config=DB_CONFIG) as db_manager:
            db_manager.update_insert_data(items_, TABLE_NAME, primary_key=PRIMARY_KEY)
        logger.info(
            f"拼多多售后工作台明细已入库 {len(items_)} 条，"
            f"table={TABLE_NAME}，primary_key={PRIMARY_KEY}"
        )

    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
