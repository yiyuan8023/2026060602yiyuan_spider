"""
主要函数列表：
ensure_datetime：确保输入是 datetime 对象，支持自动检测常见日期格式
get_is_date:判断是不是日期
get_date：将指定日期转换为文本日期格式
get_time_ago：获取指定日期n个时间单位前的日期字符串
get_recent_days：获取最近n天的日期列表（不包括今天）
get_date_range：获取两个日期之间的日期列表，支持多种日期格式
get_date_List_sorted：获取指定非连续日期列表并排序，支持多种日期格式输入和自定义输出格式
get_format_timestamp：将时间戳转换为标准日期格式
get_second_timestamp：将时间转换为时间戳（秒级）
get_millisecond_timestamp：将时间转换为毫秒级时间戳  # noqa
get_second_timestamp_18oe：将时间转换为毫秒级时间戳（通过秒级转换）
get_month_first_and_Last_day：获取指定日期所在月份的第一天和最后一天日期字符串
get_recent_months_first_day：获取最近n个月的月初日期列表（不包括当前月份）
get_month_first_days_in_range：获取指定日期区间内所有月份的月初日期列表
get_unique_month_first_days：获取非连续日期列表中每个日期所在月份的月初日期
get_date_min_max：获取日期列表中的最小值和最大值日期
get_min_max_timestamps：获取日期列表中的最小值和最大值日期对应的时间戳
get_spLit_date_range：将日期区间按指定天数间隔分割
get_df_min_max_date:获取df表中日期列中的最大日期和最小日期
get_items_min_max_date:获取items表中日期列中的最大日期和最小日期
"""

from calendar import monthrange
from datetime import datetime, timedelta, date
from typing import Union, List, Tuple

import pandas as pd

from extra.logger_ import logger


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
            "%Y.%m.%d",
            "%Y.%m.%d %H:%M:%S",
            "%m/%d/%Y",
            "%m/%d/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%d/%m/%Y %H:%M:%S",
        ]

        # 尝试各种格式
        for fmt in common_formats:
            try:
                return datetime.strptime(date_input, fmt)
            except ValueError:
                continue

        # 如果所有格式都失败，抛出错误
        raise ValueError(
            f"无法解析日期字符串 '{date_input}'，支持的格式包括: {', '.join(common_formats)}"
        )
    else:
        raise TypeError(
            f"不支持的日期格式。请提供 datetime 对象或字符串，当前类型: {type(date_input)}"
        )


def get_is_date(date_input):
    """
    判断输入是否为日期格式（支持字符串、datetime对象）
    date_input: 待检测的字符串
    bool: 如果是日期格式返回True，否则返回False
    """
    # if not isinstance(date_input, str):
    #     return False

    try:
        # 使用现有的ensure_datetime函数尝试解析日期
        ensure_datetime(date_input)
        return True
    except (ValueError, TypeError):
        # 如果解析失败，说明不是有效的日期格式
        return False


def get_date(
    date_input: Union[str, datetime, None] = None, date_format: str = "%Y-%m-%d"
) -> str:
    """
    将指定日期转换为文本日期格式
    """

    # 如果未提供日期参数，则使用当前日期
    if date_input is None:
        dt = datetime.now()
    else:
        # 使用ensure_datetime函数解析输入日期，支持多种格式
        dt = ensure_datetime(date_input)

    # 按指定格式返回日期字符串
    return dt.strftime(date_format)


def get_time_ago(
    n: int = 1,
    unit: str = "days",
    base_date: Union[str, datetime, None] = None,
    date_format: str = "%Y-%m-%d",
) -> str:
    """
    获取指定日期n个时间单位前的日期字符串

    Args:
        n (int): 时间单位数量，正数表示过去，负数表示未来
        unit (str): 时间单位，支持 'days', 'hours', 'minutes', 'seconds', 'weeks'
        base_date (str, datetime, None): 基准日期时间，None表示当前时间
        date_format (str): 输出日期格式

    Examples:
        >>> get_time_ago(1, 'days', '2025-04-10 15:30:45')
        '2025-04-09'
    """
    # 确定基准日期时间
    if base_date is None:
        target_date = datetime.now()
    else:
        target_date = ensure_datetime(base_date)

    # 根据单位计算时间差
    if unit == "days":
        result_date = target_date - timedelta(days=n)
    elif unit == "hours":
        result_date = target_date - timedelta(hours=n)
    elif unit == "minutes":
        result_date = target_date - timedelta(minutes=n)
    elif unit == "seconds":
        result_date = target_date - timedelta(seconds=n)
    elif unit == "weeks":
        result_date = target_date - timedelta(weeks=n)
    else:
        raise ValueError(
            f"不支持的时间单位: {unit}，支持的单位: days, hours, minutes, seconds, weeks"
        )

    # 返回格式化的日期字符串
    return result_date.strftime(date_format)


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
        date_ = today - timedelta(days=i + 1)
        date_list.append(date_.strftime("%Y-%m-%d"))

    return date_list


def get_date_range(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime, None] = None,
    date_format: str = "%Y-%m-%d",
) -> List[str]:
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


def get_date_list_sorted(
    date_inputs: List[Union[str, datetime]],
    date_format: str = "%Y-%m-%d",
    reverse: bool = False,
) -> List[str]:
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

    date_dt_list.sort(reverse=reverse)  # 按日期排序
    result = [dt.strftime(date_format) for dt in date_dt_list]  # 格式化输出
    return result


def get_format_timestamp(timestamp):
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
    return int(dt.timestamp())  # 转换为秒级时间戳并返回


def get_millisecond_timestamp(time_input: Union[str, datetime, None] = None) -> int:
    """
    将时间转换为毫秒级时间戳。如果未提供时间输入，则返回当前时间的时间戳。（13位）
    """

    # 解析输入参数为 datetime 对象
    if time_input is None:
        dt = datetime.now()
    else:
        dt = ensure_datetime(time_input)

    # 直接生成毫秒级时间戳
    return int(dt.timestamp() * 1000)


def get_second_timestamp_1000(time_input: Union[str, datetime, None] = None) -> int:
    """
    将时间转换为毫秒级时间戳。如果未提供时间输入，则返回当前时间的时间戳。（13位）
    """
    second_timestamp = get_second_timestamp(time_input)
    return second_timestamp * 1000  # 转换为毫秒级时间戳


def get_month_first_and_last_day(
    date_input: Union[str, datetime, None] = None,
) -> Tuple[str, str]:
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
        date_list.append(first_day.strftime("%Y-%m-%d"))

    return date_list


def get_month_first_days_in_range(
    start_date: Union[str, datetime], end_date: Union[str, datetime, None] = None
) -> List[str]:
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


def get_date_min_max(
    date_inputs: List[Union[str, datetime]], date_format: str = "%Y-%m-%d"
) -> Tuple[str, str]:
    """
    获取日期列表中的最小值和最大值日期
    Examples:
        >>> get_date_min_max(["2025-07-30", "2025-07-21", "2025/07/25"])
        ('2025-07-21', '2025-07-30')
    """
    if not date_inputs:
        raise ValueError("日期输入列表不能为空")

    # 处理日期列表，转换为datetime对象
    date_dt_list = []
    for date_input in date_inputs:
        dt = ensure_datetime(date_input)
        date_dt_list.append(dt)

    # 获取最小值和最大值
    min_date = min(date_dt_list)
    max_date = max(date_dt_list)

    # 格式化输出
    return min_date.strftime(date_format), max_date.strftime(date_format)


def get_min_max_timestamps(date_inputs: List[Union[str, datetime]]) -> Tuple[int, int]:
    """
    获取日期列表中的最小值和最大值日期对应的时间戳
    """

    if not date_inputs:
        raise ValueError("日期输入列表不能为空")

    # 使用已有的函数获取最小值和最大值
    min_date, max_date = get_date_min_max(date_inputs)

    max_date = get_time_ago(
        -1, "days", max_date
    )  # 获取后一天日期，也就是指定到00:00:00

    # 转换为时间戳
    min_timestamp = get_millisecond_timestamp(min_date)
    max_timestamp = get_millisecond_timestamp(max_date)

    return min_timestamp, max_timestamp


def get_split_date_range(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    interval_days: int = 30,
    date_format: str = "%Y-%m-%d",
) -> List[Tuple[str, str]]:
    """
    将日期区间按指定天数间隔分割，返回包含最小日期和最大日期的列表

    Args:
        start_date: 开始日期，支持字符串或datetime对象
        end_date: 结束日期，支持字符串或datetime对象
        interval_days: 分割间隔天数，默认30天
        date_format: 输出日期格式，默认为 "%Y-%m-%d"

    Returns:
        List[Tuple[str, str]]: 包含(最小日期, 最大日期)的元组列表

    Examples:
        >>> get_split_date_range("2025-01-01", "2025-03-15", 30)
        [('2025-01-01', '2025-01-30'), ('2025-01-31', '2025-03-01'), ('2025-03-02', '2025-03-15')]
    """
    # 使用现有函数解析日期
    start_dt = ensure_datetime(start_date)
    end_dt = ensure_datetime(end_date)

    # 确保开始日期不大于结束日期
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt

    result = []
    current_start = start_dt

    while current_start <= end_dt:
        # 计算当前段的结束日期
        current_end = current_start + timedelta(days=interval_days - 1)

        # 如果计算出的结束日期超过了总结束日期，则使用总结束日期
        if current_end > end_dt:
            current_end = end_dt

        # 格式化日期字符串
        start_str = current_start.strftime(date_format)
        end_str = current_end.strftime(date_format)

        result.append((start_str, end_str))

        # 下一段的开始日期是当前段结束日期下一天
        current_start = current_end + timedelta(days=1)

    return result


def get_df_min_max_date(df, date_column_name="日期"):
    # DataFrame中将日期列转换为 datetime 类型
    df[date_column_name] = pd.to_datetime(df[date_column_name])

    # 获取日期区间的最小值和最大值
    min_date = df["日期"].min()
    max_date = df["日期"].max()
    logger.info(f"日期区间: {min_date} - {max_date}")
    return min_date, max_date


def get_items_min_max_date(items, date_column_name="日期"):
    """从items列表中获取最大日期和最小日期
    Args:
        items: 包含日期信息的字典列表
        date_column_name: 日期字段的键名，默认为"日期"

    Returns:
        tuple: (最小日期, 最大日期) 的元组
    """

    if not items:
        return None, None

    # 提取所有日期并转换为datetime对象
    dates = []
    for item in items:
        if date_column_name in item and item[date_column_name]:
            try:
                # 使用ensure_datetime函数处理日期格式
                date_obj = ensure_datetime(item[date_column_name])
                dates.append(date_obj)
            except ValueError:
                continue

    if not dates:
        return None, None

    # 获取最小值和最大值
    min_date = min(dates)
    max_date = max(dates)
    logger.info(f"日期区间: {min_date} - {max_date}")
    return min_date.strftime("%Y-%m-%d"), max_date.strftime("%Y-%m-%d")


# 使用示例
if __name__ == "__main__":
    # # 获取最近3天
    # recent_3_days = get_recent_days(3)
    # print(f"最近3天: {recent_3_days}")
    #
    # result1 = get_date_range("20250721")
    # print(f"日期区间: {result1}")
    #
    # result_format = get_date_list_sorted(["2025-07-01", "2025-07-21", "2025-07-25"], )
    # print(f"中文格式: {result_format}")
    #
    # print(f"获取最近3个月的月初: {get_recent_months_first_day(3)}")

    print(f"新增字段，添加时间: {get_date()}")
