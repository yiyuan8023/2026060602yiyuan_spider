# daily_scheduler.py
import schedule
import time
import subprocess
import logging
from datetime import datetime
from extra.logger_ import logger  # 导入现有的logger


def run_program():
    """
    运行指定程序
    """
    try:
        logging.info("开始执行程序...")

        # 方法1: 运行Python脚本
        result = subprocess.run(['python', 'tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505.py'],
                                capture_output=True, text=True, timeout=3600)

        # 方法2: 运行可执行文件
        # result = subprocess.run(['your_program.exe'],
        #                        capture_output=True, text=True, timeout=3600)

        if result.returncode == 0:
            logging.info(f"程序执行成功: {result.stdout}")
        else:
            logging.error(f"程序执行失败: {result.stderr}")

    except subprocess.TimeoutExpired:
        logging.error("程序执行超时")
    except Exception as e:
        logging.error(f"执行程序时出错: {e}")


def main():
    """
    主函数
    """
    # 设置定时任务
    # 每天上午9点执行
    schedule.every().day.at("09:00").do(run_program)

    # 也可以设置多个时间点
    # schedule.every().day.at("14:00").do(run_program)  # 下午2点
    # schedule.every().day.at("18:00").do(run_program)  # 下午6点

    logging.info("定时任务已启动，等待执行...")

    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    main()
