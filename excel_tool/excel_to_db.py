# file_to_database.py
import numpy as np
import pandas as pd
import os
from typing import List, Dict, Optional
from database import DBManager
from extra.logger_ import logger

# import win32com.client
# import pythoncom
# import tempfile

import sys

# 尝试导入不同的库
try:
    import msoffcrypto

    MSOFFCRYPTO_AVAILABLE = True
except ImportError:
    MSOFFCRYPTO_AVAILABLE = False
    logger.warning("未安装msoffcrypto-tool")


class FileToItems:

    # 读取xlsx或csv文件并存入数据库
    def __init__(
        self,
        file_path: str,
        skip_rows: int = 0,
        sheet_name=0,
        password: Optional[str] = None,
    ):
        """
        Args:
            file_path: 文件路径
            skip_rows: 跳过文件开头的行数（默认为0）
            password: Excel文件密码（可选）
        """
        self.file_path = file_path
        self.skip_rows = skip_rows
        self.password = password
        self.sheet_name = sheet_name

    def read_file(self):
        # 读取xlsx或csv文件

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"文件不存在: {self.file_path}")

        # 根据文件扩展名选择读取方法
        file_extension = os.path.splitext(self.file_path)[1].lower()

        if file_extension in [".xlsx", ".xls"]:
            df = self._read_excel_with_password()

        elif file_extension in [".csv", ".txt"]:
            # 尝试不同的编码
            df = self._read_csv()
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}")

        logger.info(f"成功读取文件: {self.file_path}, 共 {len(df)} 行数据")
        items = self.df_to_dict_list(df)
        return items

    def _read_csv(self):
        # 尝试不同的编码
        encodings = ["utf-8", "gbk", "gb2312", "latin1"]
        df = None
        for encoding_ in encodings:
            try:
                df = pd.read_csv(
                    self.file_path, encoding=encoding_, skiprows=self.skip_rows
                )
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue

        if df is None:
            # 如果所有编码都失败，使用错误处理方式
            df = pd.read_csv(
                self.file_path,
                encoding="utf-8",
                encoding_errors="replace",
                skiprows=self.skip_rows,
            )
            return df

    def _read_excel_with_password(self):
        """
        读取带密码保护的Excel文件
        """
        try:
            # 首先尝试不使用密码读取
            if self.password is None:
                try:
                    df = pd.read_excel(
                        self.file_path,
                        skiprows=self.skip_rows,
                        sheet_name=self.sheet_name,
                        dtype=str,
                    )
                    return df
                except Exception as exc:
                    # 检查是否是密码保护相关的错误
                    error_msg = str(exc).lower()
                    if (
                        "password" in error_msg
                        or "encrypted" in error_msg
                        or "workbook" in error_msg
                    ):
                        logger.info("检测到文件可能需要密码保护")
                    else:
                        raise exc

            # 如果提供了密码，使用密码读取
            if self.password is not None:
                # 尝试多种方法读取加密Excel文件
                df = self._try_multiple_methods()
                if df is not None:
                    return df
                else:
                    raise Exception("所有方法都未能成功读取加密Excel文件")

        except Exception as exc:
            logger.error(f"读取Excel文件失败: {str(exc)}")
            raise exc

    def _try_multiple_methods(self):
        """尝试多种方法读取加密Excel文件"""

        # 方法1: 使用msoffcrypto-tool (如果可用)
        if MSOFFCRYPTO_AVAILABLE:
            try:
                df = self._read_with_msoffcrypto()
                if df is not None:
                    logger.info(f"msoffcrypto读取加密Excel文件方法成功")
                    return df
            except Exception as exc:
                logger.warning(f"msoffcrypto方法失败: {str(exc)}")

        # 方法2: 使用临时解密方法
        try:
            df = self._read_with_temp_decrypt()
            if df is not None:
                logger.info(f"临时读取加密Excel文件方法成功")
                return df
        except Exception as exc:
            logger.warning(f"临时解密方法失败: {str(exc)}")

        # 方法3: 如果是.xlsx文件，尝试使用win32com (Windows only)
        if sys.platform == "win32":
            try:
                df = self._read_with_win32com()
                if df is not None:
                    logger.info(f"win32com读取加密Excel文件方法成功")
                    return df
            except Exception as exc:
                logger.warning(f"win32com方法失败: {str(exc)}")

        return None

    def _read_with_msoffcrypto(self):
        """使用msoffcrypto-tool读取"""
        try:
            import msoffcrypto

            # 确保文件被正确关闭
            with open(self.file_path, "rb") as f:
                office_file = msoffcrypto.OfficeFile(f)
                office_file.load_key(password=self.password)

                # 使用临时文件
                with tempfile.NamedTemporaryFile(
                    suffix=".xlsx", delete=False
                ) as tmp_file:
                    temp_filename = tmp_file.name

                try:
                    office_file.save(temp_filename)
                    df = pd.read_excel(
                        temp_filename,
                        skiprows=self.skip_rows,
                        dtype=str,
                        sheet_name=self.sheet_name,
                    )
                    return df
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_filename):
                        os.unlink(temp_filename)

        except Exception as exc:
            raise exc

    def _read_with_temp_decrypt(self):
        """使用临时解密方法"""
        try:
            import msoffcrypto

            # 创建临时解密文件
            temp_decrypted_path = self.file_path + ".decrypted.xlsx"

            # 确保文件被正确关闭
            with open(self.file_path, "rb") as f:
                office_file = msoffcrypto.OfficeFile(f)
                office_file.load_key(password=self.password)

                with open(temp_decrypted_path, "wb") as temp_f:
                    office_file.save(temp_f)

            try:
                # 读取解密后的文件
                df = pd.read_excel(
                    temp_decrypted_path,
                    skiprows=self.skip_rows,
                    dtype=str,
                    sheet_name=self.sheet_name,
                )
                return df
            finally:
                # 清理临时文件
                if os.path.exists(temp_decrypted_path):
                    os.unlink(temp_decrypted_path)

        except Exception as exc:
            # 清理可能残留的临时文件
            temp_decrypted_path = self.file_path + ".decrypted.xlsx"
            if os.path.exists(temp_decrypted_path):
                os.unlink(temp_decrypted_path)
            raise exc

    def _read_with_win32com(self):
        """使用win32com读取（仅Windows）"""
        try:
            import win32com.client
            import pythoncom
            import tempfile  # noqa

            # 初始化COM
            pythoncom.CoInitialize()

            # 创建Excel应用
            excel_app = win32com.client.Dispatch("Excel.Application")
            excel_app.Visible = False
            excel_app.DisplayAlerts = False

            # 创建临时文件路径（保存到桌面）
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            temp_filename = f"unlocked_{os.path.basename(self.file_path)}"
            temp_path = os.path.join(desktop_path, temp_filename)

            try:
                # 打开加密文件
                workbook = excel_app.Workbooks.Open(
                    self.file_path,
                    False,  # UpdateLinks
                    True,  # ReadOnly
                    None,  # Format
                    self.password,  # Password
                    self.password,  # WriteResPassword
                )

                # 另存为无密码文件到桌面
                workbook.SaveAs(temp_path, None, "", "")
                # 关闭工作簿
                workbook.Close(SaveChanges=False)

                # 读取无密码文件
                df = pd.read_excel(
                    temp_path,
                    skiprows=self.skip_rows,
                    dtype=str,
                    sheet_name=self.sheet_name,
                )
                logger.info(df)

                logger.info(f"文件已解密并保存到桌面: {temp_path}")
                return df
            except Exception as exc:
                logger.error(f"读取Excel文件时出错: {str(exc)}")
                raise

            finally:

                excel_app.Quit()

                pythoncom.CoUninitialize()

                # 注意：这里不自动删除文件，因为文件保存在桌面供用户查看                #
                # 如果需要自动清理，可以取消下面的注释

                # try:
                #     if os.path.exists(temp_path):
                #         os.unlink(temp_path)
                # except Exception as e:
                #     logger.warning(f"清理临时文件失败: {str(e)}")

        except Exception as exc:
            raise exc

    @staticmethod
    def df_to_dict_list(df: pd.DataFrame) -> List[Dict]:
        # 将DataFrame转换为字典列表

        # 将NaN替换为None
        df = df.where(pd.notnull(df), None)
        # 将空字符串替换为None
        df.replace({np.nan: None}, inplace=True)

        # 转换为字典列表
        dict_list = df.to_dict("records")
        return dict_list


# 使用示例
if __name__ == "__main__":
    logger.info(f"\n{'*' * 120}")
    file_path_ = r"E:\1\快手小店批量导出-2025-09-16+16_20.xlsx"  # NOQA
    table_name = "rinnai_ks_快手小店_订单查询_订单列表_202501"  # noqa
    shop_name = "林内官方旗舰店"

    # 创建实例 - 需要密码
    try:
        items_ = FileToItems(file_path_, skip_rows=4, password="b632b4").read_file()

        # 显示列名和数据信息
        if items_ and len(items_) > 0:
            logger.info(f"列名: {list(items_[0].keys())}")
            logger.info(f"数据行数: {len(items_)}")
            logger.info(f"第一行数据示例: {items_[0]}")

        for item in items_:
            item.update(
                {
                    "店铺名称": shop_name,
                }
            )

        DBManager().update_insert_data(items_, table_name, primary_key="订单号")
        logger.info("-" * 100)
        logger.info("数据导入完成")
    except Exception as e:
        logger.error(f"数据导入失败: {str(e)}")

    logger.info(f"\n{'*' * 120}")
