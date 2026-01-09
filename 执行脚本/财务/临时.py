import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any


def analyze_excel_files(folder_path: str) -> List[Dict[str, Any]]:
    """
    分析文件夹中的所有Excel文件，提取每个工作表的第一行标题
    返回包含文件名称、工作表名称和标题名称的列表
    """
    results = []

    # 支持的Excel文件扩展名
    excel_extensions = {'.xlsx', '.xls', '.xlsm'}

    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_ext = Path(file).suffix.lower()

            if file_ext in excel_extensions:
                file_path = os.path.join(root, file)

                try:
                    # 读取Excel文件的所有工作表
                    excel_file = pd.ExcelFile(file_path)

                    # 遍历所有工作表
                    for sheet_name in excel_file.sheet_names:
                        try:
                            # 读取工作表的第一行（标题行），但不设置为列标题
                            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=1)

                            if not df.empty and len(df) > 0:
                                # 获取第一行的所有标题
                                headers = df.iloc[0].tolist()

                                # 过滤掉空标题
                                headers = [header for header in headers if pd.notna(header)]

                                # 添加结果
                                results.append({
                                    '文件名称': file,
                                    '完整路径': file_path,
                                    '工作表名称': sheet_name,
                                    '标题数量': len(headers),
                                    '标题名称': ', '.join(str(header) for header in headers)
                                })
                            else:
                                # 如果工作表为空
                                results.append({
                                    '文件名称': file,
                                    '完整路径': file_path,
                                    '工作表名称': sheet_name,
                                    '标题数量': 0,
                                    '标题名称': ''
                                })

                        except Exception as e:
                            print(f"处理工作表 {sheet_name} 时出错 ({file_path}): {str(e)}")
                            continue

                except Exception as e:
                    print(f"无法读取文件 {file_path}: {str(e)}")
                    continue

    return results


def save_analysis_results(results: List[Dict[str, Any]], output_path: str):
    """
    将分析结果保存到Excel文件
    """
    if not results:
        print("没有找到任何Excel文件或数据")
        return

    df = pd.DataFrame(results)
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"分析结果已保存到: {output_path}")
    print(f"共处理了 {len(results)} 个工作表")


def main():
    # 指定要分析的文件夹路径
    folder_path = r"C:\Users\admin\Desktop\财务账单_其他平台\抖音账单"

    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"文件夹不存在: {folder_path}")
        return

    print(f"开始分析文件夹: {folder_path}")

    # 分析Excel文件
    results = analyze_excel_files(folder_path)

    # 生成输出文件名
    output_file = os.path.join(
        os.path.dirname(folder_path),
        f"抖音账单工作表标题分析_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

    # 保存结果
    save_analysis_results(results, output_file)

    # 打印统计信息
    print("\n统计信息:")
    print(f"- 总共找到 {len(results)} 个工作表")

    if results:
        unique_files = set(result['文件名称'] for result in results)
        print(f"- 来自 {len(unique_files)} 个不同的Excel文件")

        total_headers = sum(result['标题数量'] for result in results)
        print(f"- 总共找到 {total_headers} 个标题字段")


if __name__ == "__main__":
    main()
