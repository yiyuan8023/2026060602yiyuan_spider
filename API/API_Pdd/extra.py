from datetime import datetime, timedelta
def cus_date(today=None):
    from datetime import datetime, timedelta
    import calendar

    # 获取当前日期
    if not today:
        today = datetime.today()
    else:
        today=datetime.strptime(today,"%Y-%m-%d %H:%M:%S")
    # 计算上个月的第一天
    first_day_of_last_month = today.replace(day=1) - timedelta(days=1)
    first_day_of_last_month = first_day_of_last_month.replace(day=1)

    # 计算上个月的最后一天
    last_day_of_last_month = (today.replace(day=1) - timedelta(days=1)).replace(
        day=calendar.monthrange(today.year, today.month - 1)[1])

    # 格式化日期为'YYYYMMDD'
    first_day_formatted = first_day_of_last_month.strftime('%Y-%m-%d')
    last_day_formatted = last_day_of_last_month.strftime('%Y-%m-%d')
    # cate_date = first_day_of_last_month.strftime('%Y%m')
    return {
        "FormDate": first_day_formatted,
        "ToDate": last_day_formatted,
        # "cate_date": cate_date

    }

def getTimeStr(timedelta_: int = 0) -> str:
    """
    获取当前时间日期的前n天或者后n天日期的字符串形式
    默认获取当天的时间"2024-3-21"
    :param timedelta_:
    :return:
    """
    # 获取今天的日期
    today = datetime.now()
    time_ = today + timedelta(days=timedelta_)
    time_str = time_.strftime('%Y-%m-%d')
    return time_str

def date_day():
    now = datetime.now()
    day = now.day
    return day
