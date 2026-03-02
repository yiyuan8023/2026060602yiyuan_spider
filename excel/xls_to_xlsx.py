import os
import pandas as pd
from typing import Union, List
import warnings
import xlrd


def convert_xls_to_xlsx(
    input_path: Union[str, List[str]], output_path: str = None, overwrite: bool = False
) -> dict:
    """
    将XLS格式文件另存为XLSX格式
    Args:
        input_path (Union[str, List[str]]): 输入文件路径或文件夹路径，或文件路径列表
        output_path (str, optional): 输出文件夹路径，如果为None则保存到原文件同目录
        overwrite (bool): 是否覆盖已存在的XLSX文件，默认False

    Returns:
        dict: 转换结果统计 {'success': [], 'failed': []}
    """

    # 忽略pandas警告
    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

    result = {"success": [], "failed": []}  # 成功转换的文件  # 转换失败的文件

    # 获取所有需要转换的文件列表
    file_list = _get_file_list(input_path)

    for file_path in file_list:
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"⚠️ 文件不存在: {file_path}")
                result["failed"].append(file_path)
                continue

            # 检查是否为XLS文件
            if not file_path.lower().endswith(".xls"):
                print(f"⚠️ 文件不是XLS格式: {file_path}")
                result["failed"].append(file_path)
                continue

            # 确定输出文件路径
            output_file_path = _get_output_path(file_path, output_path, overwrite)

            if output_file_path is None:
                result["failed"].append(file_path)
                continue

            # 执行转换
            if _convert_single_file_pandas(file_path, output_file_path):
                result["success"].append(output_file_path)
                print(f"✅ 转换成功: {file_path} -> {output_file_path}")
            else:
                # 如果pandas方法失败，尝试xlrd方法
                if _convert_single_file_xlrd(file_path, output_file_path):
                    result["success"].append(output_file_path)
                    print(f"✅ 转换成功 (xlrd方法): {file_path} -> {output_file_path}")
                else:
                    result["failed"].append(file_path)
                    print(f"❌ 转换失败: {file_path}")

        except Exception as e:
            print(f"❌ 转换文件 {file_path} 时出错: {str(e)}")
            result["failed"].append(file_path)
            continue

    print(f"\n📊 转换完成!")
    print(f"   成功: {len(result['success'])} 个文件")
    print(f"   失败: {len(result['failed'])} 个文件")

    return result


def _get_file_list(input_path: Union[str, List[str]]) -> List[str]:
    """
    获取需要转换的文件列表

    Args:
        input_path (Union[str, List[str]]): 输入路径或文件列表

    Returns:
        List[str]: 文件路径列表
    """
    if isinstance(input_path, list):
        return input_path
    elif os.path.isfile(input_path):
        return [input_path]
    elif os.path.isdir(input_path):
        # 获取文件夹中所有XLS文件
        file_list = []
        for root, dirs, files in os.walk(input_path):
            for file in files:
                if file.lower().endswith(".xls") and not file.lower().endswith(".xlsx"):
                    file_list.append(os.path.join(root, file))
        return file_list
    else:
        raise ValueError(f"无效的输入路径: {input_path}")


def _get_output_path(
    input_file: str, output_path: str = None, overwrite: bool = False
) -> Union[str, None]:
    """
    确定输出文件路径

    Args:
        input_file (str): 输入文件路径
        output_path (str, optional): 输出文件夹路径
        overwrite (bool): 是否覆盖已存在的文件

    Returns:
        Union[str, None]: 输出文件路径，如果无法确定则返回None
    """
    # 生成输出文件名（将.xls替换为.xlsx）
    base_name = os.path.basename(input_file)
    output_name = base_name.rsplit(".", 1)[0] + ".xlsx"

    # 确定输出目录
    if output_path is None:
        # 保存到原文件同目录
        output_dir = os.path.dirname(input_file)
    else:
        # 保存到指定目录
        output_dir = output_path
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

    # 构建完整输出路径
    output_file_path = os.path.join(output_dir, output_name)

    # 检查是否已存在且不覆盖
    if os.path.exists(output_file_path) and not overwrite:
        print(f"⚠️ 文件已存在，跳过: {output_file_path}")
        return None

    return output_file_path


def _convert_single_file_pandas(input_file: str, output_file: str) -> bool:
    """
    使用pandas转换单个文件

    Args:
        input_file (str): 输入文件路径
        output_file (str): 输出文件路径

    Returns:
        bool: 转换是否成功
    """
    try:
        # 尝试不同的xlrd版本参数
        try:
            # 新版本xlrd可能需要特定参数
            df = pd.read_excel(input_file, engine="xlrd")
        except Exception:
            # 如果失败，尝试不指定engine
            df = pd.read_excel(input_file)

        # 保存为XLSX文件
        df.to_excel(output_file, index=False, engine="openpyxl")
        return True

    except Exception as e:
        print(f"   pandas转换失败: {str(e)}")
        return False


def _convert_single_file_xlrd(input_file: str, output_file: str) -> bool:
    """
    使用xlrd直接转换单个文件

    Args:
        input_file (str): 输入文件路径
        output_file (str): 输出文件路径

    Returns:
        bool: 转换是否成功
    """
    try:
        import xlrd
        from openpyxl import Workbook

        # 打开XLS文件
        workbook = xlrd.open_workbook(input_file, encoding_override="utf-8")

        # 创建新的XLSX工作簿
        new_workbook = Workbook()

        # 删除默认工作表
        if new_workbook.active:
            new_workbook.remove(new_workbook.active)

        # 处理每个工作表
        for sheet_name in workbook.sheet_names():
            try:
                sheet = workbook.sheet_by_name(sheet_name)

                # 创建新的工作表（限制名称长度）
                safe_sheet_name = (
                    sheet_name[:31] if len(sheet_name) > 31 else sheet_name
                )
                new_sheet = new_workbook.create_sheet(title=safe_sheet_name)

                # 复制数据
                for row_idx in range(sheet.nrows):
                    row_data = []
                    for col_idx in range(sheet.ncols):
                        cell_value = sheet.cell_value(rowx=row_idx, colx=col_idx)
                        # 处理日期格式
                        if isinstance(cell_value, float) and cell_value > 1000:
                            try:
                                # 尝试转换为日期
                                date_tuple = xlrd.xldate_as_tuple(
                                    cell_value, workbook.datemode
                                )
                                cell_value = f"{date_tuple[0]}-{date_tuple[1]:02d}-{date_tuple[2]:02d}"
                            except:
                                pass
                        row_data.append(cell_value)
                    new_sheet.append(row_data)

            except Exception as sheet_error:
                print(f"   处理工作表 {sheet_name} 时出错: {str(sheet_error)}")
                continue

        # 保存XLSX文件
        new_workbook.save(output_file)
        return True

    except Exception as e:
        print(f"   xlrd直接转换失败: {str(e)}")
        return False


def batch_convert_xls_to_xlsx(
    input_folder: str, output_folder: str = None, overwrite: bool = False
) -> dict:
    """
    批量转换文件夹中的XLS文件为XLSX格式（简化接口）

    Args:
        input_folder (str): 输入文件夹路径
        output_folder (str, optional): 输出文件夹路径
        overwrite (bool): 是否覆盖已存在的文件

    Returns:
        dict: 转换结果统计
    """
    return convert_xls_to_xlsx(input_folder, output_folder, overwrite)


# 使用示例
if __name__ == "__main__":
    # 转换文件夹中所有XLS文件
    result = convert_xls_to_xlsx(
        "C:/Users/admin/Desktop/AA",
        "C:/Users/admin/Desktop/AA_converted",
        overwrite=False,
    )

    # 显示失败的文件
    if result["failed"]:
        print("\n失败文件列表:")
        for file in result["failed"]:
            print(f"  - {file}")
