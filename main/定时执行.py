import os
import schedule
import time
import subprocess
from extra.logger_ import logger, error_logs, error_cookie_logs
import locale
import sys


def run_script(script_name):
    """
    运行指定脚本
    """
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', script_name)
        script_path = os.path.abspath(script_path)

        logger.info(f"开始执行脚本: {script_path}")

        if not os.path.exists(script_path):
            logger.error(f"脚本文件不存在: {script_path}")
            return

        # 指定环境编码为UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8' # noqa

        result = subprocess.run(['python', script_path],
                                capture_output=True, text=True, timeout=3600,
                                encoding='utf-8', env=env)

        # 检查错误日志
        if len(error_cookie_logs) > 0:  # cookie相关错误
            logger.error(f"检测到cookie失效错误，需要重新获取cookie")
            # 可以在这里添加重新获取cookie的逻辑
            # 或者发送告警通知

        if result.returncode == 0:
            logger.info(f"脚本执行成功: {script_name}")
            logger.info(f"输出: {result.stdout}")
        else:
            logger.error(f"脚本执行失败: {script_name}")
            logger.error(f"错误: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error(f"脚本执行超时: {script_name}")
    except Exception as e:
        logger.error(f"执行脚本时出错: {script_name}, 错误: {e}")
    finally:
        # 清空错误日志列表，避免重复处理
        error_logs.clear()
        error_cookie_logs.clear()


def setup_schedules():
    for config in SCRIPT_SCHEDULES:
        schedule.every().day.at(config["time"]).do(lambda s=config["script"]: run_script(s))


def main():
    """
    主函数
    """
    # 设置多个定时任务
    # schedule.every().day.at("14:40").do(lambda: run_script('执行脚本/test/test001.py'))
    # schedule.every().day.at("14:40:30").do(lambda: run_script('执行脚本/test/test001.py'))

    # 也可以设置其他频率
    # schedule.every(2).hours.do(lambda: run_script('script_name.py'))
    # schedule.every().monday.at("09:30").do(lambda: run_script('script_name.py'))

    # 使用配置化的定时任务
    setup_schedules()

    logger.info("定时任务已启动，等待执行...")

    while True:
        schedule.run_pending()
        time.sleep(20)  # 每20秒检查一次


# 脚本配置
SCRIPT_SCHEDULES = [
    {"time": "15:22",
     "script": "执行脚本/淘系_淘宝联盟/tb_tk_淘宝联盟_服务商合作_普通招商_我报名的活动_报名的商品_2025091.py"},
#     {"time": "14:53", "script": "执行脚本/淘系_淘宝联盟/tb_tk_淘宝联盟_数据分析_定向计划报表_分天明细_202509.py"},
#     {"time": "14:54", "script": "执行脚本/淘系_淘宝联盟/tb_tk_淘宝联盟_商品分析_202504.py"},
#     {"time": "14:55",
#      "script": "执行脚本/淘系_生意参谋/ttb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505.py"},
]

if __name__ == "__main__":
    main()
