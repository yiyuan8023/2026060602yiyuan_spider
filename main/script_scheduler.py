import os
import subprocess
import threading
from datetime import datetime, timedelta

from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from extra.logger_ import logger


class ScriptScheduler:
    def __init__(self, max_workers=5, task_list=None):
        self.max_workers = max_workers
        self.task_list = task_list or []

        # 使用锁保护共享资源
        self.tasks_lock = threading.Lock()
        self.running_tasks = {}  # script_name -> thread_id
        self.pending_queue = Queue()

        # 线程池用于执行脚本
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # 存储脚本的绝对路径
        self.script_cache = {}

    def _get_script_path(self, script_name):
        """获取脚本的绝对路径"""
        if script_name not in self.script_cache:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 假设脚本在项目根目录下
            script_path = os.path.join(current_dir, "..", script_name)
            self.script_cache[script_name] = os.path.abspath(script_path)
        return self.script_cache[script_name]

    def execute_script(self, script_name):
        """执行单个脚本"""
        try:
            script_path = self._get_script_path(script_name)

            if not os.path.exists(script_path):
                logger.error(f"脚本文件不存在: {script_path}")
                return False

            # 准备环境
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"  # NOQA

            logger.info(f"开始执行脚本: {script_name}")

            # 执行脚本
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=3600,
                encoding="utf-8",
                env=env,
            )

            if result.returncode == 0:
                if "重复提交任务" in result.stdout:
                    logger.warning(f"脚本执行完成但存在重复提交: {script_name}")
                else:
                    logger.info(f"脚本执行成功: {script_name}")
                logger.debug(f"输出: {result.stdout[:500]}...")  # 只记录前500个字符
                return True
            else:
                logger.error(f"脚本执行失败: {script_name}")
                logger.error(f"错误: {result.stderr[:1000]}...")  # 只记录前1000个字符
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"脚本执行超时: {script_name}")
            return False
        except Exception as e:
            logger.error(f"执行脚本时出错: {script_name}, 错误: {e}")
            return False

    def _worker(self, script_name):
        """工作线程函数"""
        thread_id = threading.get_ident()

        try:
            # 标记为运行中
            with self.tasks_lock:
                self.running_tasks[script_name] = thread_id

            # 执行脚本
            success = self.execute_script(script_name)

            return success

        finally:
            # 从运行列表中移除
            with self.tasks_lock:
                if script_name in self.running_tasks:
                    del self.running_tasks[script_name]

            # 检查是否有待执行的任务
            self._process_pending_queue()

    def _process_pending_queue(self):
        """处理待执行队列"""
        with self.tasks_lock:
            current_running = len(self.running_tasks)

            # 如果有空闲的worker并且队列中有任务
            while current_running < self.max_workers and not self.pending_queue.empty():
                try:
                    script_name = self.pending_queue.get_nowait()
                    logger.info(f"从待执行队列中取出脚本: {script_name}")

                    # 提交到线程池执行
                    self.executor.submit(self._worker, script_name)
                    current_running += 1

                except Empty:
                    break

    def schedule_script(self, script_name):
        """调度脚本执行"""
        with self.tasks_lock:
            current_running = len(self.running_tasks)

            if script_name in self.running_tasks:
                logger.warning(f"脚本 {script_name} 正在运行，跳过本次执行")
                return

            if current_running < self.max_workers:
                # 直接执行
                logger.info(
                    f"当前运行任务数 {current_running} < {self.max_workers}，直接执行脚本: {script_name}"
                )
                self.executor.submit(self._worker, script_name)
            else:
                # 加入队列
                logger.info(
                    f"当前运行任务数 {current_running} >= {self.max_workers}，将脚本添加到待执行队列: {script_name}"
                )
                self.pending_queue.put(script_name)

    def start_timer_scheduler(self):
        """启动定时调度器"""
        scheduler_ = BlockingScheduler()

        for config in self.task_list:
            script_name = config["script"]

            if "cron" in config:
                # Cron表达式调度
                trigger = CronTrigger.from_crontab(config["cron"])
                scheduler_.add_job(
                    self.schedule_script, trigger, args=[script_name], id=script_name
                )
            elif "time" in config:
                # 每天固定时间执行
                time_parts = config["time"].split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                scheduler_.add_job(
                    self.schedule_script,
                    "cron",
                    hour=hour,
                    minute=minute,
                    args=[script_name],
                    id=script_name,
                )
            elif "date" in config:
                # 特定日期时间执行
                scheduler_.add_job(
                    self.schedule_script,
                    "date",
                    run_date=config["date"],
                    args=[script_name],
                    id=script_name,
                )

        logger.info("定时任务已启动，等待执行...")

        try:
            scheduler_.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("定时任务已停止")
            scheduler_.shutdown()
            self.executor.shutdown(wait=True)

    def run_all_scripts(self):
        """立即执行所有脚本"""
        for config in self.task_list:
            script_name = config["script"]
            self.schedule_script(script_name)

        # 等待所有任务完成
        self.executor.shutdown(wait=True)
        logger.info("所有脚本执行完成")


if __name__ == "__main__":
    now = (datetime.now() + timedelta(seconds=60)).strftime("%H:%M")
    print(now)
    SCRIPT_SCHEDULES = [
        {
            "time": now,
            "script": "执行脚本/淘系_淘宝联盟/tb_tk_淘宝联盟_商品分析_202504.py",
        },
        # {"script": "执行脚本/淘系_淘宝联盟/tb_tk_淘宝联盟_商品分析_202504.py"},
    ]

    scheduler = ScriptScheduler(max_workers=5, task_list=SCRIPT_SCHEDULES)
    # scheduler_.start_timer_scheduler()
    scheduler.run_all_scripts()
