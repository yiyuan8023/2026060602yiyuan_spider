# file_to_database.py
import pandas as pd
import os
from typing import List, Dict, Optional
from database import DBManager
from extra.logger_ import logger


class FileToItems:

    # 读取xlsx或csv文件并存入数据库
    def __init__(self):
        pass

    def read_file(
        self, file_path: str, skip_rows: int = 0, password: Optional[str] = None
    ):
        """
        读取xlsx或csv文件

        Args:
            file_path: 文件路径
            skip_rows: 跳过文件开头的行数（默认为0）
            password: Excel文件密码（可选）
        """

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 根据文件扩展名选择读取方法
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in [".xlsx", ".xls"]:
            df = self._read_excel_with_password(file_path, skip_rows, password)

        elif file_extension in [".csv", ".txt"]:
            # 尝试不同的编码
            encodings = ["utf-8", "gbk", "gb2312", "latin1"]
            df = None
            for encoding_ in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding_, skiprows=skip_rows)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if df is None:
                # 如果所有编码都失败，使用错误处理方式
                df = pd.read_csv(
                    file_path,
                    encoding="utf-8",
                    encoding_errors="replace",
                    skiprows=skip_rows,
                )
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}")

        logger.info(f"成功读取文件: {file_path}, 共 {len(df)} 行数据")
        items = self.df_to_dict_list(df)
        return items

    def _read_excel_with_password(
        self, file_path: str, skip_rows: int = 0, password: Optional[str] = None
    ):
        """
        读取带密码保护的Excel文件

        Args:
            file_path: Excel文件路径
            skip_rows: 跳过行数
            password: 文件密码

        Returns:
            pandas.DataFrame: 读取的数据框
        """
        try:
            # 首先尝试不使用密码读取
            if password is None:
                try:
                    df = pd.read_excel(file_path, skiprows=skip_rows)
                    return df
                except Exception as e:
                    # 如果失败，可能是需要密码
                    if "Password" in str(e) or "password" in str(e).lower():
                        logger.info("检测到文件可能需要密码保护")
                    else:
                        raise e

            # 如果提供了密码或检测到需要密码，使用密码读取
            if password is not None:
                try:
                    # 使用msoffcrypto-tool处理加密的Excel文件
                    import msoffcrypto
                    import io

                    with open(file_path, "rb") as f:
                        office_file = msoffcrypto.OfficeFile(f)
                        office_file.load_key(password=password)

                        # 解密到内存
                        decrypted = io.BytesIO()
                        office_file.save(decrypted)

                        # 从解密的数据读取Excel
                        df = pd.read_excel(decrypted, skiprows=skip_rows)
                        return df

                except ImportError:
                    logger.warning("未安装msoffcrypto-tool，无法处理加密Excel文件")
                    # 尝试使用pandas直接读取（某些情况下可能工作）
                    try:
                        df = pd.read_excel(
                            file_path, skiprows=skip_rows, engine="openpyxl"
                        )
                        return df
                    except Exception:
                        raise Exception(
                            "无法读取加密的Excel文件，请安装msoffcrypto-tool: pip install msoffcrypto-tool"
                        )
                except Exception as e:
                    raise Exception(f"密码错误或文件读取失败: {str(e)}")

            # 默认情况
            df = pd.read_excel(file_path, skiprows=skip_rows)
            return df

        except Exception as e:
            logger.error(f"读取Excel文件失败: {str(e)}")
            raise e

    @staticmethod
    def df_to_dict_list(df: pd.DataFrame) -> List[Dict]:
        # 将DataFrame转换为字典列表
        df.columns = df.columns
        df = df.where(pd.notnull(df), None)  # 将NaN替换为None
        dict_list = df.to_dict("records")  # 转换为字典列表
        return dict_list


# 使用示例
if __name__ == "__main__":
    logger.info(f"\n{'*' * 120}")
    file_path_ = r"E:\1\【生意参谋平台】商品_全部_2025-08-26_2025-08-26.xls"  # NOQA
    table_name = "【生意参谋平台】商品_全部_2025-08-26_2025-08-26.xls"
    shop_name = "林内官方旗舰店"

    # 创建实例 - 不需要密码
    # items_ = FileToItems().read_file(file_path_, skip_rows=4)

    # 创建实例 - 需要密码
    items_ = FileToItems().read_file(file_path_, skip_rows=4, password="your_password")
    # print(items_)

    for item in items_:
        item.update({"店铺名称": shop_name, "计划类型": "全部推广类型"})
        # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
    # print(items)

    # DBManager().update_insert_data(items, table_name, primary_key='key')
    DBManager().update_insert_data(items_, table_name, uu_id=True, user=True)
    # logger.info(f"{shop_name_list},{crawl_day_list}已入库")
    logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
