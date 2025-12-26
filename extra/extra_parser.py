import argparse
from datetime import datetime

from extra.extra_date import get_month_first_and_last_day


# 命令行参数解析工具，主要用于处理数据采集任务的时间范围参数


def parse_date(date_str):
    """将字符串转换为日期对象"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的日期格式: {date_str}. 使用 YYYY-MM-DD 格式.")


def parse_shop_names(shop_names_str):
    """解析店铺名称，支持逗号分隔的多个店铺"""
    if shop_names_str:
        return [name.strip() for name in shop_names_str.split(',')]
    return []


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
        '--start-date',  # 定义命令行参数的名称，用户在命令行中需要使用 --end-date 来指定该参数
        type=parse_date,  # 参数类型为 parse_date 函数，这意味着输入的字符串会被传递给 parse_date 函数进行验证和转换
        help='开始日期 (YYYY-MM-DD),仅在 daily 模式下有效'  # 参数的帮助信息
    )
    parser.add_argument(
        '--end-date',
        type=parse_date,
        help='结束日期 (YYYY-MM-DD),仅在 daily 模式下有效'
    )
    parser.add_argument(
        '--month',
        type=str,
        help='输入月份(01),仅在 monthly 模式下有效'
    )

    parser.add_argument(
        '--shop-names',
        type=parse_shop_names,
        help='输入店铺名称，多个店铺用逗号分隔，如：店铺1,店铺2'
    )
    # 解析命令行参数，将用户输入的参数转换为命名空间对象
    args = parser.parse_args()

    # 获取用户指定的模式参数（daily/monthly/weekly），默认为 daily
    mode = args.mode

    # 根据不同模式返回相应参数
    if mode == 'daily':
        # argparse 自动将连字符转换为下划线（Python的命名约定），--start-date 在代码中变为 start_date
        return args.start_date, args.end_date, args.shop_names

    elif mode == 'monthly':
        # monthly模式需要提供月份参数
        if not args.month:
            parser.error("monthly模式需要提供 --month 参数")
        return get_month_first_and_last_day(args.month), args.shop_names

    elif mode == 'weekly':
        # TODO: 实现weekly模式逻辑
        raise NotImplementedError("weekly模式暂未实现")
