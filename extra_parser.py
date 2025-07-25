import argparse
from datetime import datetime

from extra_time import get_month_first_and_last_day

# 命令行参数解析工具，主要用于处理数据采集任务的时间范围参数


def parse_date(date_str):
    """将字符串转换为日期对象"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的日期格式: {date_str}. 使用 YYYY-MM-DD 格式.")


# 创建参数解析器
def parser_main():
    parser = argparse.ArgumentParser(description="数据采集工具")

    # 添加模式参数，默认为 daily
    parser.add_argument(
        '--mode',
        type=str,
        choices=['monthly', 'daily', 'weekly'],
        default='daily',
        help='采集模式 (monthly, daily, weekly)，默认为 daily'
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

    # 解析命令行参数
    args = parser.parse_args()
    mode = args.mode

    # 根据不同模式返回相应参数
    if mode == 'daily':
        return args.start_date, args.end_date

    elif mode == 'monthly':
        # monthly模式需要提供月份参数
        if not args.month:
            parser.error("monthly模式需要提供 --month 参数")
        return get_month_first_and_last_day(args.month)

    elif mode == 'weekly':
        # TODO: 实现weekly模式逻辑
        raise NotImplementedError("weekly模式暂未实现")