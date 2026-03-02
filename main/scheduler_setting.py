from datetime import datetime, timedelta

from script_scheduler import ScriptScheduler

now = (datetime.now() + timedelta(seconds=60)).strftime("%H:%M")

SCRIPT_SCHEDULES = [
    {
        "time": "09:30",
        "script": "执行脚本/淘系_淘宝联盟/tb_tk_淘宝联盟_服务商合作_普通招商_我报名的活动_报名的商品_202509.py",
    },
    {
        "time": "09:31",
        "script": "执行脚本/淘系_淘宝联盟/tb_tk_淘宝联盟_数据分析_定向计划报表_分天明细_202509.py",
    },
    {
        "time": "09:32",
        "script": "执行脚本/淘系_淘宝联盟/tb_tk_淘宝联盟_商品分析_202504.py",
    },
    {
        "time": "09:33",
        "script": "执行脚本/淘系_淘宝联盟/tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505.py",
    },
    {
        "time": "09:34",
        "script": "执行脚本/淘系_万相台/tb_tg_万相台无界_基础报表_货品全站推_202504.py",
    },
    {
        "time": "09:35",
        "script": "执行脚本/淘系_生意参谋/tb_sycm_自助分析_取数_商品_流量来源_所有商品_格式化.py",
    },  # noqa
]

if __name__ == "__main__":
    scheduler_ = ScriptScheduler(max_workers=5, task_list=SCRIPT_SCHEDULES)
    scheduler_.run_all_scripts()

    # 41 15 * * * - 每天15:41执行
    # 0 9 * * 1-5 - 每周一到周五上午9点执行
    # 30 * * * * - 每小时的第30分钟执行
    # 0 1 1 * * - 每月1号上午1点执行
    # https://www.yingdao.com/yddoc/rpa/zh-CN/710696135703605248

    # 或者指定具体执行日期 - 在指定日期执行一次
    # {"date": datetime(2025, 12, 27, 10, 30), "script": "执行脚本/test/test001.py"},
    # {"cron": "48 17 * * *", "script": "执行脚本/test/test001.py"},
    # {"time": "17:48:10", "script": "执行脚本/test/test002.py"},
