# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:40:00
- 最近修改：2026-06-10 21:40:00
- 文件用途：封装拼多多数据中心商品数据相关接口请求，返回平台原始 JSON 和必要的字体映射。
- 业务范围：适用于商品明细效果、商品概况和商品概况实时数据接口，字段解析与入库由 parser 和 jobs 负责。
- 依赖入口：使用 API.API_Pdd.API_Pdd_Base.PddBaseApi。
- 验收方式：修改后执行 py_compile 和 API_Pdd 包导入探针；真实请求由单店铺单日期任务验证。
- 注意事项：API 层不写业务表、不拼唯一 key、不输出 Cookie；字体混淆接口只返回 font_mapping 供 parser 使用。
"""

from typing import Any, Dict, Optional, Tuple

from API.API_Pdd.API_Pdd_Base import PddBaseApi


class PddGoodsApi(PddBaseApi):
    """拼多多数据中心商品数据接口。"""

    def goods_detail(
        self,
        start_date: str,
        end_date: str,
        page_num: int = 1,
        page_size: int = 50,
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, str]]:
        """商品数据-商品明细-商品明细效果。"""
        headers, font_mapping = self.build_font_headers_and_mapping()
        payload = {
            "goodsId": "",
            "startDate": start_date,
            "endDate": end_date,
            "queryType": 0,
            "sortCol": 0,
            "sortType": 1,
            "pageNum": page_num,
            "pageSize": page_size,
            "actVs": 1,
            "crawlerInfo": "",
        }
        response_json = self.post_json(
            "https://mms.pinduoduo.com/sydney/api/goodsDataShow/queryGoodsDetailVOListForMMS",
            payload,
            headers=headers,
            context="拼多多商品明细效果",
        )
        return response_json, font_mapping

    def goods_general_situation(
        self,
        start_date: str,
        end_date: str,
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, str]]:
        """商品数据-商品概况。"""
        headers, font_mapping = self.build_font_headers_and_mapping()
        payload = {
            "queryType": 7,
            "queryDate": end_date,
            "startDate": start_date,
            "endDate": end_date,
        }
        response_json = self.post_json(
            "https://mms.pinduoduo.com/sydney/api/goodsDataShow/queryGoodsPagePlnOstListByDate",
            payload,
            headers=headers,
            context="拼多多商品概况",
        )
        return response_json, font_mapping

    def goods_general_situation_realtime(self) -> Optional[Dict[str, Any]]:
        """商品数据-商品概况-实时数据。"""
        return self.post_json(
            "https://mms.pinduoduo.com/sydney/api/goodsDataShow/queryGoodsPageOverviewForMms",
            {},
            headers=self.build_headers(need_anti_content=True),
            context="拼多多商品概况实时数据",
        )
