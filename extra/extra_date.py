from calendar import monthrange
from datetime import datetime, timedelta, date
from typing import Union, List, Tuple


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

def get_recent_days(n: int = 3) -> List[str]:
    """
    获取最近n天的日期列表（不包括今天）
    Args:   n (int): 天数，默认为3
    Returns：list: 日期列表，格式为 'YYYY-MM-DD'
    """
    today = datetime.now()
    date_list = []

    # 从最早的日期到今天的顺序添加
    for i in range(n):
        date_ = today - timedelta(days=i+1)
        date_list.append(date_.strftime('%Y-%m-%d'))

    return date_list


def get_date_range(start_date: Union[str, datetime],
                   end_date  : Union[str, datetime, None] =None ,
                   date_format: str = "%Y-%m-%d") -> List[str]:
    """
    获取两个日期之间的日期列表，支持多种日期格式
    如果解说日期为None,只返回开始日期一天数据

    Args:
        start_date (str 或 datetime): 起始日期
        end_date (str 或 datetime): 结束日期
        date_format (str): 输出日期格式，默认为 "%Y-%m-%d"
    Returns:
        list: 日期列表

    Examples:
        >>> get_date_range("2025-07-21", "2025-07-24")
        ['2025-07-21', '2025-07-22', '2025-07-23', '2025-07-24']
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

    date_dt_list.sort(reverse=reverse) # 按日期排序
    result = [dt.strftime(date_format) for dt in date_dt_list] # 格式化输出
    return result



def format_timestamp(timestamp):
    """
    将时间戳转换为标准日期格式
    Args:       timestamp (int/float): 时间戳（支持秒级或毫秒级）
    Returns:    str: 格式化后的日期字符串 (YYYY-MM-DD)
    """
    if not timestamp:
        return None

    # 判断是秒级还是毫秒级时间戳
    # 一般以1970年到当前时间的毫秒数来判断临界值
    if timestamp > 9999999999:  # 大约2286年之前的毫秒级时间戳
        # 毫秒级时间戳转换为秒级
        timestamp = timestamp / 1000

    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
    except (ValueError, OSError):
        # 时间戳无效时返回None
        return None

def get_second_timestamp(time_input: Union[str, datetime, None] = None) -> int:
    """
    将时间转换为时间戳。如果未提供时间输入，则返回当前时间的时间戳。（9位）
    """

    # 解析输入参数为 datetime 对象
    if time_input is None:
        dt = datetime.now()
    else:
        dt = ensure_datetime(time_input)
    return int(dt.timestamp()) # 转换为秒级时间戳并返回


def get_millisecond_timestamp(time_input: Union[str, datetime, None] = None) -> int:
    """
    将时间转换为毫秒级时间戳。如果未提供时间输入，则返回当前时间的时间戳。（13位）
    """
    second_timestamp = get_second_timestamp(time_input)
    return second_timestamp * 1000 # 转换为毫秒级时间戳


def get_month_first_and_last_day (date_input: Union[str, datetime, None] = None) -> Tuple[str, str]:
    """
    获取指定日期所在月份的第一天和最后一天日期字符串。
    """
    # 获取目标日期
    if date_input is None:
        target_date = datetime.now().date()
    else:
        # 使用 ensure_datetime 函数来解析输入日期
        target_datetime = ensure_datetime(date_input)
        target_date = target_datetime.date()

    # 获取年份和月份
    target_year = target_date.year
    target_month = target_date.month

    # 获取该月的最后一天
    _, last_day = monthrange(target_year, target_month)

    # 构建并返回日期字符串
    first_day_str = f"{target_year:04d}-{target_month:02d}-01"
    last_day_str = f"{target_year:04d}-{target_month:02d}-{last_day:02d}"

    return first_day_str, last_day_str


def get_recent_months_first_day(n=3) -> List[str]:
    """
    获取最近n个月的月初日期列表（不包括当前月份）
    Examples:
        >>> get_recent_months_first_day(3)
        ['2025-02-01', '2025-03-01', '2025-04-01']  # 假设当前为2025年5月
    """
    today = datetime.now()
    date_list = []

    # 从最早的月份到上一个月的顺序添加
    for i in range(n):
        # 计算需要回溯的月份
        target_month = today.month - (n - i)
        target_year = today.year

        # 处理跨年情况
        if target_month <= 0:
            target_year -= 1
            target_month += 12

        # 构造每月第一天的日期
        first_day = date(target_year, target_month, 1)
        date_list.append(first_day.strftime('%Y-%m-%d'))

    return date_list


def get_month_first_days_in_range(start_date: Union[str, datetime],
                                  end_date: Union[str, datetime, None] = None) -> List[str]:
    """
    获取指定日期区间内所有月份的月初日期列表，自动去重并按时间顺序排列
    Args:
        start_date (str 或 datetime): 起始日期
        end_date (str 或 datetime, optional): 结束日期，如果为None则等于起始日期
    Returns:
        list: 去重并排序的月初日期列表，格式为 'YYYY-MM-DD'

    Examples:
        >>> get_month_first_days_in_range("2025-03-15", "2025-06-10")
        ['2025-03-01', '2025-04-01', '2025-05-01', '2025-06-01']
    """

    start_dt = ensure_datetime(start_date)

    if end_date is None:
        end_dt = start_dt
    else:
        end_dt = ensure_datetime(end_date)

    # 确保起始日期不大于结束日期
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt

    # 使用集合存储月初日期以自动去重
    month_first_days = set()

    # 从起始日期所在月份开始，逐月添加月初日期直到结束日期所在月份
    current_year = start_dt.year
    current_month = start_dt.month

    end_year = end_dt.year
    end_month = end_dt.month

    # 遍历所有月份
    while (current_year, current_month) <= (end_year, end_month):
        # 添加该月第一天
        first_day_str = f"{current_year:04d}-{current_month:02d}-01"
        month_first_days.add(first_day_str)

        # 移动到下一个月
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    # 转换为列表并排序
    result = sorted(list(month_first_days))
    return result


def get_unique_month_first_days(date_inputs: List[Union[str, datetime]]) -> List[str]:
    """
    获取非连续日期列表中每个日期所在月份的月初日期，对结果去重并排序
    Args:  date_inputs: 日期输入列表，支持多种格式
    Returns: List[str]: 去重并排序后的月初日期列表，格式为 'YYYY-MM-DD'
    Examples:
        >>> get_unique_month_first_days(["2025-03-15", "2025-03-20", "2025-05-10"])
        ['2025-03-01', '2025-05-01']
    """
    if not date_inputs:
        return []

    # 使用集合存储月初日期以自动去重
    month_first_days = set()

    # 处理每个输入日期
    for date_input in date_inputs:
        # 使用 ensure_datetime 解析日期
        dt = ensure_datetime(date_input)

        # 获取该日期所在月份的月初日期
        first_day_str = f"{dt.year:04d}-{dt.month:02d}-01"
        month_first_days.add(first_day_str)

    # 转换为列表并排序
    result = sorted(list(month_first_days))
    return result


def get_n_days_ago_date(n: int = 1,
                             base_date: Union[str, datetime, None] = None,
                             date_format: str = "%Y-%m-%d") -> str:
    """
    获取指定日期n天前的日期字符串
    Args:
        n (int): 天数偏移量，默认为1（表示前一天）
        base_date (str 或 datetime 或 None): 基准日期,可以是字符串或datetime对象，如果为None则使用今天
        date_format (str): 日期格式字符串，默认为"%Y-%m-%d"

    Returns:
        str: 格式化后的日期字符串
    Examples:
        >>> get_n_days_ago_date()  # 获取昨天日期
        '2025-04-04'
        >>> get_n_days_ago_date(7)  # 获取7天前日期
        '2025-03-29'
        >>> get_n_days_ago_date(1, '2025-04-10')  # 获取2025-04-10的前一天
        '2025-04-09'
    """
    # 确定基准日期
    if base_date is None:
        target_date = datetime.now() # 如果没有提供基准日期，使用今天
    else:
        target_date = ensure_datetime(base_date)  # 使用 ensure_datetime 函数解析输入日期

    result_date = target_date - timedelta(days=n) # 计算n天前的日期

    # 返回格式化的日期字符串
    return result_date.strftime(date_format)


# 使用示例
if __name__ == "__main__":
    # 获取最近3天
    recent_3_days = get_recent_days(3)
    print(f"最近3天: {recent_3_days}")

    result1 = get_date_range("20250721")
    print(f"日期区间: {result1}")

    result_format = get_date_list_sorted(["2025-07-01", "2025-07-21", "2025-07-25"], )
    print(f"中文格式: {result_format}")

    print(f"获取最近3个月的月初: {get_recent_months_first_day(3)}")