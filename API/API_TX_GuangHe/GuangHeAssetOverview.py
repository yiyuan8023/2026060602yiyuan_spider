import io
import json
from pathlib import Path

import pandas as pd
import requests

from API.API_TX_GuangHe.GuangHeBase import GuangHeBaseApi
from extra.extra_error import handle_request_error
from extra.logger_ import logger
from extra.settings import UA


PAGE_URL = "https://creator.guanghe.taobao.com/page/unify/asset-overview?tab=productAnalysis"


class GuangHeAssetOverviewApi(GuangHeBaseApi):
    """光合平台资产总览 API，负责 mtop 导出任务和 Excel 数据解析。"""

    def __init__(self, cookie):
        super().__init__(cookie=cookie, referer=PAGE_URL)

    def _get_content_consume_indicator_fields(self):
        """从 meta 接口取全量指标字段，避免导出文件缺列。"""
        response_json = self._mtop_request(
            "mtop.taobao.guanghe.creator.data.content.assert.meta",
            {"source": "guanghe", "tab": "itemAnalysisConsume"},
        )
        indicators = response_json["data"]["model"]["indicators"]
        return [item["indicatorField"] for item in indicators]

    def _create_download_task(self, day):
        """创建商品分析内容消费的单日下载任务。"""
        stat_day = self._format_day(day)
        indicator_fields = self._get_content_consume_indicator_fields()

        # params 是下载任务内部参数，scene 与外层 task scene 不同。
        task_params = {
            "source": "guanghe",
            "pageNo": 1,
            "pageSize": 10,
            "scene": "itemAnalysisConsumeDownload",
            "conditions": json.dumps(
                {
                    "content_type": "all",
                    "biz_line": "all",
                    "belong_type_lvl1": "all",
                    "ds": stat_day,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "timeRangeBegin": stat_day,
            "timeRangeEnd": stat_day,
            "timeRangeType": "1",
            "orderBy": "payAmtZcLast:absolute:desc,itemId:absolute:desc",
            "indicatorFields": json.dumps(
                indicator_fields, ensure_ascii=False, separators=(",", ":")
            ),
        }
        response_json = self._mtop_request(
            "mtop.taobao.guangguang.creator.download.task.create",
            {
                "source": "guanghe",
                "scene": "assert_item_analysis_download",
                "params": json.dumps(
                    task_params, ensure_ascii=False, separators=(",", ":")
                ),
            },
        )
        task_id = response_json["data"]["model"]["taskId"]
        logger.info(f"光合平台下载任务创建成功，task_id={task_id}")
        return task_id

    def _query_download_url(self, task_id, max_retry=30, interval=2):
        """轮询下载任务状态，status=2 且有 fileUrl 时表示文件可下载。"""
        for _ in range(max_retry):
            response_json = self._mtop_request(
                "mtop.taobao.guangguang.creator.download.task.status",
                {"source": "guanghe", "taskId": task_id},
            )
            model = response_json.get("data", {}).get("model", {})
            status = str(model.get("status", ""))
            if status == "2" and model.get("fileUrl"):
                logger.info(
                    f"光合平台下载任务完成，task_id={task_id}, file_name={model.get('fileName')}"
                )
                return model["fileUrl"]
            if status in {"3", "4", "-1"}:
                raise RuntimeError(f"光合平台下载任务失败: {model}")
            time.sleep(interval)

        raise TimeoutError(f"光合平台下载任务超时，task_id={task_id}")

    @staticmethod
    def _read_excel_content(content):
        """读取平台下载的 Excel 明细页，商品 id 按字符串保留。"""
        df = pd.read_excel(
            io.BytesIO(content),
            sheet_name="明细数据",
            dtype={"商品id": str},
        )
        df = df.fillna("")
        return df.to_dict("records")

    def product_analysis_content_consumption_excel(self, day):
        """按日期在线下载商品分析内容消费明细。"""
        try:
            task_id = self._create_download_task(day)
            download_url = self._query_download_url(task_id)
            response = requests.get(download_url, headers={"User-Agent": UA}, timeout=60)
            response.raise_for_status()
            return self._read_excel_content(response.content)
        except Exception as exc:
            return handle_request_error(exc, context="光合平台商品分析下载")

    @staticmethod
    def read_local_excel(file_path):
        """读取本地样例 Excel，用于离线校验字段和入库结构。"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        df = pd.read_excel(
            file_path,
            sheet_name="明细数据",
            dtype={"商品id": str},
        )
        df = df.fillna("")
        return df.to_dict("records")
