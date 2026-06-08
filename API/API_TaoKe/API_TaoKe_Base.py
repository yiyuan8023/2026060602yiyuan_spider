# File: TaoKeBaseApi

from extra.logger_ import logger
from config import UA


class TaoKeBaseApi(object):
    def __init__(self, cookie):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua, "cookie": self.cookie}

    def get_task_status_list(self, task_status_list_res):
        """
        获取淘宝联盟任务状态列表,通用
        """
        # 调用API获取任务状态列表
        # logger.info(task_status_list_res)
        if not task_status_list_res:
            return {}, {}

        # 检查返回结果中的错误码，判断cookie是否过期
        if task_status_list_res.get("code") == 601:
            raise "cookie过期"

        result = task_status_list_res.get("data", {}).get("result", [])
        finish_task, un_finish_task = self._process_task_status(result)

        logger.info(finish_task)
        return finish_task, un_finish_task

    @staticmethod
    def _process_task_status(result):
        """
        处理任务状态列表，分类已完成和未完成的任务
        :param result: 任务状态列表
        :return: (finish_task, un_finish_task)
        """
        finish_task = {}  # {文件名: 任务ID}
        un_finish_task = {}  # {文件名: 任务ID}

        for task in result:
            if task.get("process") == "100" and task.get("status") == 1:
                finish_task[task["fileName"]] = task["id"]
            elif task.get("process") == "0":
                un_finish_task[task["fileName"]] = task["id"]
            elif task.get("errorMessage") == "超时停止调度":
                un_finish_task[task["fileName"]] = task["id"]
        return finish_task, un_finish_task
