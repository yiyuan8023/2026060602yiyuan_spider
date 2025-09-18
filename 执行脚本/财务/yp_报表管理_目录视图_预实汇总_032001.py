import pandas as pd

from datetime import datetime
import os

from extra.database_manager import DatabaseManager
from extra.extra_df_dict import df_to_dict
from extra.logger_ import logger


def process_excel_workbook_no_warning(input_file, output_file):
    """
    无警告版本 - 完全避免 pandas 警告，并添加额外字段
    """
    print("正在读取Excel文件...")

    # 一次性读取所有sheet的数据
    all_sheets_data = pd.read_excel(input_file, sheet_name=None, header=None)

    # 获取所有sheet名称
    sheet_names = list(all_sheets_data.keys())

    # 跳过第一个sheet，处理后续所有sheet
    all_processed_data = []

    # 标准列名（添加新字段）
    standard_columns = ['序号', '项目', '类别', '明细科目', '标准', '决算', '预算', '上年',
                        'sheet名称', '月份', '编制部门', '当前版本', '对应金蝶部门', '文件名称', '入库日期', '年份']

    print(f"开始处理 {len(sheet_names) - 1} 个工作表...")

    # 统计变量
    total_rows_processed = 0  # 总处理行数
    total_data_blocks = 0  # 总数据块数
    filtered_empty_rows = 0  # 被过滤的空行数

    # 获取文件名（不含路径和扩展名）
    file_name = os.path.splitext(os.path.basename(input_file))[0]

    # 获取当前系统日期
    current_date = datetime.now().strftime('%Y-%m-%d')

    # 固定年份
    year = '2025'

    # 跳过第一个sheet，处理后续所有sheet
    for idx, sheet_name in enumerate(sheet_names[1:], 1):
        print(f"处理进度: {idx}/{len(sheet_names) - 1} - 工作表: {sheet_name}")

        try:
            # 直接获取已读取的数据
            df = all_sheets_data[sheet_name]

            # 确保有足够的数据
            if len(df) > 7 and len(df.columns) >= 41:  # 至少41列
                # 循环12次，每次处理3列数据
                for cycle in range(12):
                    # 计算当前需要读取的列索引
                    start_col = 5 + (cycle * 3)  # 从第6列开始
                    end_col = start_col + 3

                    # 确保不超出列范围
                    if end_col <= 41:  # 固定41列
                        # 提取数据（从第8行开始，索引7）
                        if len(df) > 7:
                            # 提取固定列（前5列）和动态列（3列）
                            fixed_data = df.iloc[7:, :5].reset_index(drop=True)
                            dynamic_data = df.iloc[7:, start_col:end_col].reset_index(drop=True)

                            # 合并数据
                            merged_data = pd.concat([fixed_data, dynamic_data], axis=1)

                            # 设置列名
                            if merged_data.shape[1] == 8:  # 确保列数正确
                                merged_data.columns = ['序号', '项目', '类别', '明细科目', '标准', '决算', '预算',
                                                       '上年']

                                # 添加额外列
                                merged_data['月份'] = f"{cycle + 1}"
                                merged_data['sheet名称'] = sheet_name

                                # 添加新的字段列
                                # B3单元格 (索引: 行2, 列1)
                                merged_data['编制部门'] = df.iloc[2, 1] if not pd.isna(df.iloc[2, 1]) else ""
                                # B4单元格 (索引: 行3, 列1)
                                merged_data['当前版本'] = df.iloc[3, 1] if not pd.isna(df.iloc[3, 1]) else ""
                                # D4单元格 (索引: 行3, 列3)
                                merged_data['对应金蝶部门'] = df.iloc[3, 3] if not pd.isna(df.iloc[3, 3]) else ""
                                merged_data['文件名称'] = file_name
                                merged_data['入库日期'] = current_date
                                merged_data['年份'] = year


                                # merged_data[
                                #     'key'] = (
                                #     f"{merged_data['编制部门']}_{merged_data['当前版本']}_{merged_data['年份']}_"
                                #     f"{merged_data['月份']}_{merged_data['入库日期']}")

                                # 过滤掉决算、预算、上年三列都为空或为0的行
                                filter_columns = ['决算', '预算', '上年']

                                # 确保这些列存在
                                if all(col in merged_data.columns for col in filter_columns):
                                    # 完全避免警告的方法：直接使用布尔逻辑进行过滤
                                    decision_data = merged_data[filter_columns]

                                    # 创建布尔掩码，检查每行是否应该保留
                                    # 保留条件：至少有一列非空且非零
                                    keep_mask = pd.Series([False] * len(decision_data), index=decision_data.index)

                                    for col in filter_columns:
                                        # 对每列检查非空（但不过滤0）
                                        col_data = decision_data[col]
                                        # 标记非空的项（包括0值）
                                        col_mask = ~col_data.isna()
                                        keep_mask = keep_mask | col_mask

                                    # 应用过滤
                                    filtered_data = merged_data[keep_mask]

                                    # 统计被过滤的行数
                                    filtered_count = len(merged_data) - len(filtered_data)
                                    filtered_empty_rows += filtered_count

                                    # 如果过滤后还有数据，则添加到结果中
                                    if not filtered_data.empty:
                                        # 更新统计信息
                                        total_rows_processed += len(filtered_data)
                                        total_data_blocks += 1
                                        all_processed_data.append(filtered_data)

                                        if filtered_count > 0:
                                            pass
                                            # print(f"  └─ 过滤掉 {filtered_count} 行空数据")
                                    else:
                                        print(f"  └─ 该数据块全部为空，已跳过")
                                else:
                                    # 如果列不完整，仍然添加数据
                                    all_processed_data.append(merged_data)
                                    # 更新统计信息
                                    total_rows_processed += len(merged_data)
                                    total_data_blocks += 1

        except Exception as e:
            print(f"处理工作表 {sheet_name} 时出错: {e}")
            continue

    # 合并所有处理后的数据
    if all_processed_data:
        print("正在合并所有数据...")
        final_df = pd.concat(all_processed_data, ignore_index=True)

        # 重新排列列顺序
        final_columns = [col for col in standard_columns if col in final_df.columns]
        final_df = final_df[final_columns]
        # 写入新的Excel文件
        final_df.to_excel(output_file, index=False)

        # 写入数据库
        items = df_to_dict(final_df)
        # print(items)
        for item in items:
            department = item.get('编制部门', '')
            item["前后台"] = department.split('[')[-1].split(']')[0] if '[' in department and ']' in department else ""
            item["key"] = f"{item['序号']}_{item['编制部门']}_{item['当前版本']}_{item['年份']}_{item['月份']}_{item['入库日期']}"
        DatabaseManager(db_config=db_config).upsert_data(items, table_name,primary_key='key')

        logger.info(f"✅ 数据处理完成!")
        logger.info(f"📊 总共处理了 {total_data_blocks} 个数据块")
        logger.info(f"📈 总处理行数: {total_rows_processed}")
        logger.info(f"🔍 过滤掉的空行数: {filtered_empty_rows}")
        logger.info(f"💾 最终输出行数: {len(final_df)}")
        logger.info(f"📄 结果已保存到: {output_file}")
        logger.info(f"📋 最终数据列数: {len(final_df.columns)}")

        logger.info("❌ 没有找到可处理的数据")


# 使用示例
if __name__ == "__main__":
    # 设置输入和输出文件路径
    input_file_ = r"Z:\000数据中台专用\26财务数据02\20240917财务预实分析\00临时文件\预实整体情况表-BI对接 (202508).xlsx"
    output_file_ = r"Z:\000数据中台专用\26财务数据02\20240917财务预实分析\00临时文件\预实整体情况表-BI对接 (202508)已处理.xlsx"
    table_name = 'yp_报表管理_目录视图_预实汇总_032001'
    # db_config = None # noqa
    db_config = "caiwu_hzbc" # noqa

    # 执行处理
    process_excel_workbook_no_warning(input_file_, output_file_)
