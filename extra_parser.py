# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-04-18
# Time: 13:54
# Project: jide
# File: extra_parser
import argparse
from datetime import datetime

from extra_time import get_month_first_and_last_day


def parse_date(date_str):
    """将字符串转换为日期对象"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的日期格式: {date_str}. 使用 YYYY-MM-DD 格式.")

def parser_main():
    parser = argparse.ArgumentParser(description="数据采集工具")

    # 添加模式参数，默认为 monthly
    parser.add_argument(
        '--mode',
        type=str,
        choices=['monthly', 'daily', 'weekly'],
        default='daily',
        help='采集模式 (monthly, daily, weekly)，默认为 monthly'
    )

    # 添加每日模式参数
    parser.add_argument(
        '--start-date',
        type=parse_date,
        help='开始日期 (YYYY-MM-DD)，仅在 daily 模式下有效'
    )
    parser.add_argument(
        '--end-date',
        type=parse_date,
        help='结束日期 (YYYY-MM-DD)，仅在 daily 模式下有效'
    )
    parser.add_argument(
        '--month',
        type=str,
        help='输入月份(01)，仅在 monthly 模式下有效'
    )
    mode= parser.parse_args().mode
    if mode=='daily':
        args = parser.parse_args()
        return args.start_date, args.end_date
    elif mode=='monthly':
        month = parser.parse_args().month
        return get_month_first_and_last_day(month)



