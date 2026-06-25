# -*- coding: utf-8 -*-
"""Run DChain merchant-warehouse export for recent 3 days including today."""

import runpy
import sys
from datetime import datetime, timedelta
from pathlib import Path


TARGET_SCRIPT = "tb_DChain_订单管理行业_商家仓_全部数据导出_202606.py"


def build_recent_three_day_args():
    """Build --start-date/--end-date for recent 3 days including today."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=2)
    return [
        "--start-date",
        start_date.strftime("%Y-%m-%d"),
        "--end-date",
        end_date.strftime("%Y-%m-%d"),
    ]


if __name__ == "__main__":
    script_path = Path(__file__).with_name(TARGET_SCRIPT)
    old_argv = sys.argv[:]
    sys.argv = [str(script_path), *build_recent_three_day_args()]
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = old_argv
