# daily_scheduler.py
import schedule
import time
import subprocess

import os
from datetime import datetime
from extra.logger_ import logger  # 导入现有的logger


def run_program(program_path, program_name="", working_dir=None):
    """
    运行指定程序

    Args:
        program_path: 程序路径或命令
        program_name: 程序名称（用于日志显示）
        working_dir: 工作目录
    """
    try:
        # 如果没有指定程序名称，则使用程序路径的最后一部分
        if not program_name:
            program_name = os.path.basename(program_path) if isinstance(program_path, str) else str(program_path)

        logger.info(f"开始执行程序: {program_name}")
        logger.info(f"程序路径: {program_path}")

        # 运行程序
        if isinstance(program_path, str):
            # 单个命令字符串
            command = program_path.split()
        elif isinstance(program_path, list):
            # 命令列表
            command = program_path
        else:
            raise ValueError("program_path 必须是字符串或列表")

        # 设置工作目录
        kwargs = {}
        if working_dir:
            kwargs['cwd'] = working_dir

        result = subprocess.run(command,
                                capture_output=True,
                                text=True,
                                timeout=3600,
                                **kwargs)

        if result.returncode == 0:
            logger.info(f"程序 {program_name} 执行成功")
            if result.stdout:
                logger.info(f"输出: {result.stdout}")
        else:
            logger.error(f"程序 {program_name} 执行失败: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error(f"程序 {program_name} 执行超时")
    except Exception as e:
        logger.error(f"执行程序 {program_name} 时出错: {e}")


def main():
    """
    主函数
    """
    # 定义要执行的程序列表 (程序路径, 执行时间, 程序名称, 工作目录)
    programs_schedule = [
        # (程序路径, 执行时间, 程序名称, 工作目录)
        (['python', 'tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505.py'],
         "09:00",
         "淘宝联盟CPS订单明细",
         r'C:\Users\admin\Desktop\yiyuan_spider\淘系_淘宝联盟'),

        (['python', 'tb_tk_淘宝联盟_商品分析_202504.py'],
         "10:30",
         "淘宝联盟商品分析",
         r'C:\Users\admin\Desktop\yiyuan_spider\淘系_淘宝联盟'),

        (['python', 'tb_tk_淘宝联盟_服务商合作_普通招商_我报名的活动_报名的商品_202509.py'],
         "14:00",
         "我报名的商品",
         r'C:\Users\admin\Desktop\yiyuan_spider\淘系_淘宝联盟'),

        # 可以添加更多程序
        # (['python', 'other_script.py'], "18:00", "其他脚本", r'C:\path\to\script'),
    ]

    # 设置定时任务
    for program_path, exec_time, program_name, working_dir in programs_schedule:
        # 为每个程序创建一个包装函数
        def make_job(p_path=None, p_name=None, work_dir=None):
            # 设置默认值
            if p_path is None:
                p_path = program_path
            if p_name is None:
                p_name = program_name
            if work_dir is None:
                work_dir = working_dir
            return lambda: run_program(p_path, p_name, work_dir)

        schedule.every().day.at(exec_time).do(make_job())
        logger.info(f"已设置定时任务: {program_name} 在 {exec_time} 执行")

    # 也可以设置其他类型的定时任务
    # schedule.every(30).minutes.do(lambda: run_program(['python', 'quick_check.py'], "快速检查"))
    # schedule.every().monday.at("09:00").do(lambda: run_program(['python', 'weekly_report.py'], "周报"))

    logger.info("定时任务已启动，等待执行...")

    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    main()
