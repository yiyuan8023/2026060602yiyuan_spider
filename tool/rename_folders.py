import os
import pandas as pd
from pathlib import Path

def rename_folders_from_excel(excel_path, target_directory):
    """
    根据Excel表格中的映射关系重命名目标目录下的文件夹
    
    Args:
        excel_path (str): Excel文件路径，第一列是原始名称，第二列是新名称
        target_directory (str): 需要重命名文件夹的目标目录路径

    Returns:
        dict: 包含成功和失败重命名操作的统计信息
    """

    # 检查Excel文件是否存在
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel文件不存在: {excel_path}")

    # 检查目标目录是否存在
    if not os.path.exists(target_directory):
        raise FileNotFoundError(f"目标目录不存在: {target_directory}")

    # 读取Excel文件
    try:
        df = pd.read_excel(excel_path)
        print(f"Excel文件列名: {list(df.columns)}")
        print(f"数据行数: {len(df)}")
    except Exception as e:
        raise Exception(f"读取Excel文件失败: {e}")

    # 检查是否有至少两列
    if len(df.columns) < 2:
        raise ValueError("Excel文件必须至少包含两列（原始名称和新名称）")

    # 使用前两列作为原始名称和新名称
    original_name_col = df.columns[0]  # 第一列
    new_name_col = df.columns[1]       # 第二列

    print(f"使用列 '{original_name_col}' 作为原始名称，列 '{new_name_col}' 作为新名称")

    # 统计信息
    success_count = 0
    fail_count = 0
    failed_operations = []

    # 获取目标目录的Path对象
    target_path = Path(target_directory)

    # 遍历Excel中的每一行
    for index, row in df.iterrows():
        # 获取原始名称和新名称
        original_name = str(row[original_name_col]).strip() if pd.notna(row[original_name_col]) else ""
        new_name = str(row[new_name_col]).strip() if pd.notna(row[new_name_col]) else ""
        
        # 跳过空行
        if not original_name or not new_name:
            continue
            
        # 构造原始文件夹和新文件夹的完整路径
        original_folder = target_path / original_name
        new_folder = target_path / new_name
        
        # 检查原始文件夹是否存在
        if not original_folder.exists():
            fail_count += 1
            failed_operations.append(f"原始文件夹不存在: {original_name}")
            continue
            
        # 检查新名称是否已存在
        if new_folder.exists():
            fail_count += 1
            failed_operations.append(f"目标文件夹已存在: {new_name}")
            continue
            
        # 执行重命名操作
        try:
            original_folder.rename(new_folder)
            success_count += 1
            print(f"成功重命名: {original_name} -> {new_name}")
        except Exception as e:
            fail_count += 1
            failed_operations.append(f"重命名失败 {original_name} -> {new_name}: {str(e)}")
    
    # 返回统计结果
    result = {
        "success_count": success_count,
        "fail_count": fail_count,
        "failed_operations": failed_operations,
        "total_processed": success_count + fail_count
    }
    
    return result

# 使用示例
if __name__ == "__main__":
    # 定义Excel文件路径和目标目录
    excel_file = r"C:\Users\Administrator\Desktop\改名.xlsx"
    target_dir = r"C:\Users\Administrator\Desktop\国补审计材料_天猫【拱墅区202507】"
    
    try:
        # 执行重命名操作
        result = rename_folders_from_excel(excel_file, target_dir)
        
        # 打印结果统计
        print(f"\n重命名操作完成:")
        print(f"成功: {result['success_count']} 个")
        print(f"失败: {result['fail_count']} 个")
        print(f"总计: {result['total_processed']} 个")
        
        # 打印失败的操作详情
        if result['failed_operations']:
            print(f"\n失败的操作详情:")
            for operation in result['failed_operations']:
                print(f"  - {operation}")
                
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
