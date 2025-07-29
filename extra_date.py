
from datetime import datetime, timedelta
from typing import Union, List


def get_recent_days(n=3):
    """
    获取最近n天的日期列表（不包括今天）
    Args:   n (int): 天数，默认为3
    Returns：list: 日期列表，格式为 'YYYY-MM-DD'
    """
    today = datetime.now()
    date_list = []

    # 从最早的日期到今天的顺序添加
    for i in range(n):
        date = today - timedelta(days=i+1)
        date_list.append(date.strftime('%Y-%m-%d'))

    return date_list


def get_date_range(start_date: Union[str, datetime],
                   end_date  : Union[str, datetime, None] =None ,
                   date_format: str = "%Y-%m-%d") -> List[str]:
    """
    获取两个日期之间的日期列表，支持多种日期格式

    Args:
        start_date (str 或 datetime): 起始日期
        end_date (str 或 datetime): 结束日期
        date_format (str): 输出日期格式，默认为 "%Y-%m-%d"
    Returns:
        list: 日期列表

    Examples:
        >>> get_date_range("2025-07-21", "2025-07-27")
        ['2025-07-21', '2025-07-22', '2025-07-23', '2025-07-24', '2025-07-25', '2025-07-26', '2025-07-27']

    """
    # 使用ensure_datetime 函数，将输入转换为 datetime 对象
    if end_date is None:
        end_date = start_date

    start_dt = ensure_datetime(start_date)
    end_dt = ensure_datetime(end_date)

    # 确保起始日期不大于结束日期
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt

    # 生成日期列表
    date_list = []
    current_date = start_dt

    while current_date <= end_dt:
        date_list.append(current_date.strftime(date_format))
        current_date += timedelta(days=1)

    return date_list


def get_date_list_sorted(date_inputs: List[Union[str, datetime]],
                         date_format: str = "%Y-%m-%d",
                         reverse: bool = False) -> List[str]:
    """
    获取指定非连续日期列表并排序，支持多种日期格式输入和自定义输出格式
    Args:
        date_inputs (List[Union[str, datetime]]): 日期输入列表，支持多种格式
        date_format (str): 输出日期格式，默认为 "%Y-%m-%d"
        reverse (bool): 是否倒序排列，默认为False（升序）
    Returns:
        List[str]: 排序后按照指定格式输出的日期列表
    Examples:
        >>> get_date_list_sorted(["2025-07-30", "2025-07-21", "2025/07/25"])
        ['2025-07-21', '2025-07-25', '2025-07-30']
    """

    # 处理并排序日期列表
    date_dt_list = []
    for date_input in date_inputs:
        dt = ensure_datetime(date_input)
        date_dt_list.append(dt)

    # 按日期排序
    date_dt_list.sort(reverse=reverse)

    # 格式化输出
    return [dt.strftime(date_format) for dt in date_dt_list]


def ensure_datetime(date_input: Union[str, datetime]) -> datetime:
    """
    确保输入是 datetime 对象，支持自动检测常见日期格式。
    """
    if isinstance(date_input, datetime):
        return date_input
    elif isinstance(date_input, str):
        # 常见日期格式列表（与项目中保持一致）
        common_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M",
            "%Y%m%d",
        ]

        # 尝试各种格式
        for fmt in common_formats:
            try:
                return datetime.strptime(date_input, fmt)
            except ValueError:
                continue

        # 如果所有格式都失败，抛出错误
        raise ValueError(f"无法解析日期字符串 '{date_input}'，支持的格式包括: {', '.join(common_formats)}")
    else:
        raise TypeError(f"不支持的日期格式。请提供 datetime 对象或字符串，当前类型: {type(date_input)}")

# 使用示例
if __name__ == "__main__":
    # 获取最近3天
    recent_3_days = get_recent_days(3)
    print(f"最近3天: {recent_3_days}")

    result1 = get_date_range("20250721")
    print(f"日期区间: {result1}")

    result_format = get_date_list_sorted(["2025-07-01", "2025-07-21", "2025-07-25"], )
    print(f"中文格式: {result_format}")
