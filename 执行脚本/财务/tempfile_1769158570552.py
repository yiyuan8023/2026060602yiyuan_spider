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
                                non_empty_headers = [header for header in headers if pd.notna(header) and str(header).strip() != '']
                                
                                # 检查重复标题
                                duplicate_headers = find_duplicate_headers(headers)

                                # 添加结果
                                results.append({
                                    '文件名称': file,
                                    '完整路径': file_path,
                                    '工作表名称': sheet_name,
                                    '标题数量': len(headers),
                                    '非空标题数量': len(non_empty_headers),
                                    '空标题数量': len(headers) - len(non_empty_headers),
                                    '标题名称': ', '.join(str(header) for header in headers if pd.notna(header) and str(header).strip() != ''),
                                    '包含空标题': len(headers) != len(non_empty_headers),
                                    '重复标题数量': len(duplicate_headers),
                                    '重复标题': ', '.join(set(str(header) for header in duplicate_headers if pd.notna(header) and str(header).strip() != '')),
                                    '包含重复标题': len(duplicate_headers) > 0
                                })
                            else:
                                # 如果工作表为空
                                results.append({
                                    '文件名称': file,
                                    '完整路径': file_path,
                                    '工作表名称': sheet_name,
                                    '标题数量': 0,
                                    '非空标题数量': 0,
                                    '空标题数量': 0,
                                    '标题名称': '',
                                    '包含空标题': False,
                                    '重复标题数量': 0,
                                    '重复标题': '',
                                    '包含重复标题': False
                                })

                        except Exception as e:
                            print(f"处理工作表 {sheet_name} 时出错 ({file_path}): {str(e)}")
                            continue

                except Exception as e:
                    print(f"无法读取文件 {file_path}: {str(e)}")
                    continue

    return results

def find_duplicate_headers(headers):
    """
    查找重复的标题
    """
    seen = set()
    duplicates = set()

    for header in headers:
        if pd.notna(header) and str(header).strip() != '':
            header_str = str(header).strip()
            if header_str in seen:
                duplicates.add(header_str)
            else:
                seen.add(header_str)

    return list(duplicates)

def find_tables_with_empty_headers(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    查找包含空标题的表格
    返回包含空标题的表格信息
    """
    tables_with_empty_headers = []

    for result in results:
        if result['包含空标题']:
            # 重新读取整个工作表来找出具体的空标题位置
            try:
                df = pd.read_excel(result['完整路径'], sheet_name=result['工作表名称'], header=None, nrows=1)
                if not df.empty and len(df) > 0:
                    headers = df.iloc[0].tolist()

                    empty_header_positions = []
                    for idx, header in enumerate(headers):
                        if pd.isna(header) or (isinstance(header, str) and header.strip() == ''):
                            empty_header_positions.append(idx)

                    result['空标题位置'] = empty_header_positions
                    tables_with_empty_headers.append(result)
            except Exception as e:
                print(f"再次读取文件 {result['完整路径']} 时出错: {str(e)}")

    return tables_with_empty_headers

def find_tables_with_duplicate_headers(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    查找包含重复标题的表格
    返回包含重复标题的表格信息
    """
    tables_with_duplicate_headers = []

    for result in results:
        if result['包含重复标题']:
            tables_with_duplicate_headers.append(result)

    return tables_with_duplicate_headers

def remove_empty_header_columns(file_path: str, output_path: str):
    """
    删除标题为空的列
    """
    try:
        # 读取Excel文件的所有工作表
        excel_file = pd.ExcelFile(file_path)
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name in excel_file.sheet_names:
                # 读取整个工作表数据
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)

                # 获取标题行
                headers = df.columns.tolist()

                # 找出空标题的位置
                empty_indices = []
                for idx, header in enumerate(headers):
                    if pd.isna(header) or (isinstance(header, str) and header.strip() == ''):
                        empty_indices.append(idx)

                if empty_indices:
                    # 获取非空标题的列
                    non_empty_columns = [col for col in df.columns
                                       if not pd.isna(col) and (not isinstance(col, str) or col.strip() != '')]

                    # 选择非空标题的列
                    df_cleaned = df[non_empty_columns]

                    # 写入新的工作表
                    df_cleaned.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"已清理文件 {file_path} 中工作表 '{sheet_name}' 的空标题列，保留 {len(non_empty_columns)} 列")
                else:
                    # 如果没有空标题，直接复制原表
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"文件 {file_path} 中工作表 '{sheet_name}' 没有空标题列")

        print(f"已将修复后的文件保存到: {output_path}")
        return True
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return False

def remove_duplicate_header_columns(file_path: str, output_path: str):
    """
    删除具有重复标题的列，保留第一次出现的列
    """
    try:
        # 读取Excel文件的所有工作表
        excel_file = pd.ExcelFile(file_path)
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name in excel_file.sheet_names:
                # 读取整个工作表数据
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)

                # 获取标题行
                headers = df.columns.tolist()

                # 记录已经见过的标题，移除重复的列
                seen_headers = set()
                columns_to_keep = []

                for idx, header in enumerate(headers):
                    header_str = str(header).strip() if pd.notna(header) else ""

                    # 只有当标题非空且未出现过时才保留
                    if header_str != "" and header_str not in seen_headers:
                        columns_to_keep.append(df.columns[idx])
                        seen_headers.add(header_str)

                if len(columns_to_keep) < len(headers):
                    # 有重复标题，只保留非重复的列
                    df_cleaned = df[columns_to_keep]

                    # 写入新的工作表
                    df_cleaned.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"已清理文件 {file_path} 中工作表 '{sheet_name}' 的重复标题列，保留 {len(columns_to_keep)} 列")
                else:
                    # 没有重复标题，直接复制原表
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"文件 {file_path} 中工作表 '{sheet_name}' 没有重复标题列")

        print(f"已将修复后的文件保存到: {output_path}")
        return True
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return False

def fix_all_files_with_empty_headers(results: List[Dict[str, Any]], base_folder: str):
    """
    修复所有包含空标题的文件
    """
    # 获取所有包含空标题的唯一文件
    files_with_empty_headers = {}
    for result in results:
        if result['包含空标题']:
            if result['完整路径'] not in files_with_empty_headers:
                files_with_empty_headers[result['完整路径']] = result['文件名称']

    print(f"\n发现 {len(files_with_empty_headers)} 个文件包含空标题列，开始修复...")

    for file_path, file_name in files_with_empty_headers.items():
        # 生成修复后的文件名
        dir_path = os.path.dirname(file_path)
        name_part, ext_part = os.path.splitext(file_name)
        output_path = os.path.join(dir_path, f"{name_part}_已修复空标题{ext_part}")

        print(f"\n正在修复文件: {file_name}")
        remove_empty_header_columns(file_path, output_path)

def fix_all_files_with_duplicate_headers(results: List[Dict[str, Any]], base_folder: str):
    """
    修复所有包含重复标题的文件
    """
    # 获取所有包含重复标题的唯一文件
    files_with_duplicate_headers = {}
    for result in results:
        if result['包含重复标题']:
            if result['完整路径'] not in files_with_duplicate_headers:
                files_with_duplicate_headers[result['完整路径']] = result['文件名称']

    print(f"\n发现 {len(files_with_duplicate_headers)} 个文件包含重复标题列，开始修复...")

    for file_path, file_name in files_with_duplicate_headers.items():
        # 生成修复后的文件名
        dir_path = os.path.dirname(file_path)
        name_part, ext_part = os.path.splitext(file_name)
        output_path = os.path.join(dir_path, f"{name_part}_已修复重复标题{ext_part}")

        print(f"\n正在修复文件: {file_name}")
        remove_duplicate_header_columns(file_path, output_path)

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

def save_empty_headers_report(empty_headers_results: List[Dict[str, Any]], output_path: str):
    """
    将包含空标题的表格信息保存到Excel文件
    """
    if not empty_headers_results:
        print("没有找到包含空标题的表格")
        return

    df = pd.DataFrame(empty_headers_results)
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"空标题报告已保存到: {output_path}")
    print(f"共找到 {len(empty_headers_results)} 个包含空标题的表格")

def save_duplicate_headers_report(duplicate_headers_results: List[Dict[str, Any]], output_path: str):
    """
    将包含重复标题的表格信息保存到Excel文件
    """
    if not duplicate_headers_results:
        print("没有找到包含重复标题的表格")
        return

    df = pd.DataFrame(duplicate_headers_results)
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"重复标题报告已保存到: {output_path}")
    print(f"共找到 {len(duplicate_headers_results)} 个包含重复标题的表格")

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
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(
        os.path.dirname(folder_path),
        f"抖音账单工作表标题分析_{timestamp}.xlsx"
    )

    # 生成空标题报告文件名
    empty_headers_output_file = os.path.join(
        os.path.dirname(folder_path),
        f"抖音账单空标题报告_{timestamp}.xlsx"
    )

    # 生成重复标题报告文件名
    duplicate_headers_output_file = os.path.join(
        os.path.dirname(folder_path),
        f"抖音账单重复标题报告_{timestamp}.xlsx"
    )

    # 保存结果
    save_analysis_results(results, output_file)

    # 查找包含空标题的表格
    empty_headers_results = find_tables_with_empty_headers(results)

    # 查找包含重复标题的表格
    duplicate_headers_results = find_tables_with_duplicate_headers(results)

    # 保存空标题报告
    save_empty_headers_report(empty_headers_results, empty_headers_output_file)

    # 保存重复标题报告
    save_duplicate_headers_report(duplicate_headers_results, duplicate_headers_output_file)

    # 打印统计信息
    print("\n统计信息:")
    print(f"- 总共找到 {len(results)} 个工作表")

    if results:
        unique_files = set(result['文件名称'] for result in results)
        print(f"- 来自 {len(unique_files)} 个不同的Excel文件")

        total_headers = sum(result['标题数量'] for result in results)
        print(f"- 总共找到 {total_headers} 个标题字段")

        total_empty_headers = sum(result['空标题数量'] for result in results)
        print(f"- 其中包含 {total_empty_headers} 个空标题字段")

        total_duplicate_headers = sum(result['重复标题数量'] for result in results)
        print(f"- 其中包含 {total_duplicate_headers} 个重复标题字段")

        print(f"- 共有 {len(empty_headers_results)} 个工作表包含空标题")
        print(f"- 共有 {len(duplicate_headers_results)} 个工作表包含重复标题")

        if empty_headers_results:
            print("\n包含空标题的表格详情:")
            for result in empty_headers_results:
                print(f"  - 文件: {result['文件名称']}, 工作表: {result['工作表名称']}, "
                      f"空标题数量: {result['空标题数量']}, 空标题位置: {result.get('空标题位置', [])}")

        if duplicate_headers_results:
            print("\n包含重复标题的表格详情:")
            for result in duplicate_headers_results:
                print(f"  - 文件: {result['文件名称']}, 工作表: {result['工作表名称']}, "
                      f"重复标题: {result['重复标题']}")

            # 询问用户是否要修复这些文件
            user_input = input("\n是否要修复包含重复标题的文件？(y/n): ")
            if user_input.lower() in ['y', 'yes', '是']:
                fix_all_files_with_duplicate_headers(results, folder_path)

        # 询问用户是否要修复包含空标题的文件
        user_input = input("\n是否要修复包含空标题的文件？(y/n): ")
        if user_input.lower() in ['y', 'yes', '是']:
            fix_all_files_with_empty_headers(results, folder_path)

if __name__ == "__main__":
    main()
