# file_to_database.py
import pandas as pd
import os
from typing import List, Dict
from extra.database_manager import DatabaseManager
from extra.logger_ import logger


class FileToItems:

    # 读取xlsx或csv文件并存入数据库
    def __init__(self):
        pass

    def read_file(self, file_path: str, skip_rows: int = 0):
        """
           读取xlsx或csv文件

           Args:
               file_path: 文件路径
               skip_rows: 跳过文件开头的行数（默认为0）
           """

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 根据文件扩展名选择读取方法
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, skiprows=skip_rows)

        elif file_extension in ['.csv', '.txt']:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            df = None
            for encoding_ in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding_, skiprows=skip_rows)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if df is None:
                # 如果所有编码都失败，使用错误处理方式
                df = pd.read_csv(file_path, encoding='utf-8', encoding_errors='replace', skiprows=skip_rows)
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}")

        logger.info(f"成功读取文件: {file_path}, 共 {len(df)} 行数据")
        items = self.df_to_dict_list(df)
        return items

    @staticmethod
    def df_to_dict_list(df: pd.DataFrame) -> List[Dict]:
        # 将DataFrame转换为字典列表
        df.columns = df.columns
        df = df.where(pd.notnull(df), None)  # 将NaN替换为None
        dict_list = df.to_dict('records')  # 转换为字典列表
        return dict_list


# 使用示例
if __name__ == "__main__":
    logger.info(f"\n{'*' * 120}")
    file_path_ = r'E:\1\【生意参谋平台】商品_全部_2025-08-26_2025-08-26.xls'  # NOQA
    table_name = '【生意参谋平台】商品_全部_2025-08-26_2025-08-26.xls'
    shop_name = '林内官方旗舰店'

    # 创建实例
    items_ = FileToItems().read_file(file_path_, skip_rows=4)
    # print(items_)

    for item in items_:
        item.update({
            "店铺名称": shop_name,
            "计划类型": "全部推广类型"
        })
        # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
    # print(items)

    # DatabaseManager().upsert_data(items, table_name, primary_key='key')
    DatabaseManager().upsert_data(items_, table_name, uu_id=True, user=True)
    # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
