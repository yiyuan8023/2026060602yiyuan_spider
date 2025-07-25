
from calendar import monthrange
from datetime import date ,datetime, timedelta
from typing import Union, List, Tuple, Optional


def get_date(day_offset=-1, date_format="%Y-%m-%d"):
    """
    获取相对于今天的日期字符串
    Args:
        day_offset (int): 相对于今天的天数偏移量，默认为-1（昨天）
        date_format (str): 日期格式字符串，默认为"%Y-%m-%d"
    Returns:
        str: 格式化后的日期字符串
    """
    # 获取当前日期并计算偏移后的日期
    target_date = date.today() + timedelta(days=day_offset)

    # 返回格式化的日期字符串
    return target_date.strftime(date_format)


def calculate_days_diff_with_range(date1: Union[str, datetime],
                                   date2: Union[str, datetime]) -> List[int]:
    """
    计算两个日期之间每一天相对于当前日期的天数差

    Args:
        date1 (str 或 datetime): 起始日期，可以是字符串格式"YYYY-MM-DD"或datetime对象
        date2 (str 或 datetime): 结束日期，可以是字符串格式"YYYY-MM-DD"或datetime对象

    Returns:
        list: 包含范围内每一天相对于当前日期天数差的列表

    Example:
        calculate_days_diff_with_range("2025-04-12", "2025-04-14")
        # 如果今天是2025-04-10，返回 [2, 3, 4]
        # 表示这些日期分别比今天晚2天、3天、4天
    """
    # 获取当前日期
    current_date = date.today()

    # 判断输入参数类型并统一转换为date对象
    def parse_date(input_date: Union[str, datetime, date]) -> date:
        """将输入转换为date对象"""
        if isinstance(input_date, datetime):
            return input_date.date()
        elif isinstance(input_date, date):
            return input_date
        elif isinstance(input_date, str):
            return datetime.strptime(input_date, "%Y-%m-%d").date()
        else:
            raise ValueError(f"不支持的日期格式: {type(input_date)}")

    # 确保start_date是较早的日期，end_date是较晚的日期
    start_date, end_date = sorted([parse_date(date1), parse_date(date2)])

    # 使用列表推导式计算日期范围内的所有天数差
    days_diff = [(start_date + timedelta(days=i) - current_date).days
                 for i in range((end_date - start_date).days + 1)]

    return days_diff

def convert_to_timestamp(time_input: Union[str, datetime],
                        time_format: str = "%Y-%m-%d") -> int:
    """
    将时间转换为时间戳。

    Args:
        time_input (str 或 datetime): 输入的时间，可以是字符串或 datetime 对象。
        time_format (str): 如果 time_input 是字符串，则需要指定其格式，默认为 "%Y-%m-%d"。

    Returns:
        int: 时间戳（毫秒级）。

    Examples:
        # >>> convert_to_timestamp('2025-04-05')
        1743811200000
        # >>> convert_to_timestamp('2025-04-05 14:30:00", "%Y-%m-%d %H:%M:%S')
        1743863400000
        # >>> convert_to_timestamp(datetime(2025, 4, 5))
        1743811200000
    """
    # 解析输入参数为 datetime 对象
    if isinstance(time_input, str):
        # 如果输入是字符串，先将其解析为 datetime 对象
        dt = datetime.strptime(time_input, time_format)
    elif isinstance(time_input, datetime):
        # 如果输入已经是 datetime 对象，直接使用
        dt = time_input
    else:
        raise TypeError(f"time_input 必须是字符串或 datetime 对象，当前类型: {type(time_input)}")

    # 转换为毫秒级时间戳并返回
    return int(dt.timestamp() * 1000)

def ensure_datetime(date_input: Union[str, datetime]) -> datetime:

    """
    确保输入是 datetime 对象，支持自动检测常见日期格式。
    Args:
        date_input (str 或 datetime): 输入的日期，可以是字符串或 datetime 对象

    Returns:
        datetime: 转换后的 datetime 对象
    Raises:
        TypeError: 当输入既不是字符串也不是 datetime 对象时
        ValueError: 当字符串无法解析为日期时
    """
    if isinstance(date_input, datetime):
        return date_input
    elif isinstance(date_input, str):
        # 常见日期格式列表
        common_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M"
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

def split_date_range(start_date: Union[str, datetime],
                     end_date: Union[str, datetime],
                     max_days: int = 90) -> List[Tuple[str, str]]:
    """
    将日期范围分割成多个较小的段，每段最多包含指定天数。

    Args:
        start_date (str 或 datetime): 起始日期
        end_date (str 或 datetime): 结束日期
        max_days (int): 每段最大天数，默认为90天

    Returns:
        List[Tuple[str, str]]: 包含多个日期段的列表，每个段是(起始日期, 结束日期)的元组

    Examples:
        >>> split_date_range("2025-01-01", "2025-04-01")
        [('2025-01-01', '2025-03-31'), ('2025-04-01', '2025-04-01')]

        >>> split_date_range("2025-04-01", "2025-01-01")  # 日期对调
        [('2025-01-01', '2025-03-31'), ('2025-04-01', '2025-04-01')]
    """
    # 确保输入是 datetime 对象
    start_dt = ensure_datetime(start_date)
    end_dt = ensure_datetime(end_date)

    # 如果起始日期晚于结束日期，自动对调
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt

    # 如果最大天数无效，设置默认值
    if max_days <= 0:
        max_days = 90

    result: List[Tuple[str, str]] = []
    current_start = start_dt

    # 分割日期范围
    while current_start <= end_dt:
        # 计算当前段的结束日期，不能超过最终结束日期
        current_end = min(current_start + timedelta(days=max_days - 1), end_dt)

        # 添加到结果中
        result.append((
            current_start.strftime("%Y-%m-%d"),
            current_end.strftime("%Y-%m-%d")
        ))

        # 更新下一段的开始日期
        current_start = current_end + timedelta(days=1)

    return result

def get_month_first_and_last_day(month_str: Optional[str] = None) -> Tuple[str, str]:
    """
    获取指定月份或上个月的第一天和最后一天日期字符串（优化版本）。
    Args:
        month_str (str, optional): 指定月份，格式为"MM"(如"03"表示三月)。
                                  如果为None，则返回上个月的日期范围。
    Returns:
        Tuple[str, str]: 包含该月第一天和最后一天的元组(first_day, last_day)
                        日期格式为"YYYY-MM-DD"
    """

    # 获取今天的日期信息
    today = date.today()

    # 确定目标年份和月份
    if month_str is None:
        # 计算上个月的年份和月份
        if today.month == 1:
            target_year = today.year - 1
            target_month = 12
        else:
            target_year = today.year
            target_month = today.month - 1
    else:
        # 使用指定月份
        target_month = int(month_str)
        target_year = today.year if target_month <= today.month else today.year - 1

    # 获取该月的最后一天数字
    _, last_day = monthrange(target_year, target_month)

    # 构建并返回日期字符串
    first_day = f"{target_year:04d}-{target_month:02d}-01"
    last_day_date = f"{target_year:04d}-{target_month:02d}-{last_day:02d}"

    return first_day, last_day_date

if __name__ == '__main__':

    print(get_month_first_and_last_day())  # 默认返回上个月的第一天和最后一天（如果现在是2025年5月）
    print(get_month_first_and_last_day('03'))  # 返回指定月份（如2025年3月）的第一天和最后一天