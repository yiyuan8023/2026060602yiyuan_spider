import pandas as pd
import requests
import pdf2image
import os
from PIL import Image


def process_invoice_excel(excel_path, output_dir="./发票图片", dpi=200, poppler_path=None):
    """
    处理Excel文件中的发票PDF链接，转换为JPG图片

    Args:
        excel_path (str): Excel文件路径
        output_dir (str): 输出目录
        dpi (int): 图片分辨率
        poppler_path (str): poppler安装路径（Windows需要指定）

    Returns:
        dict: 处理结果统计
    """

    try:
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 读取Excel文件
        print(f"正在读取Excel文件: {excel_path}")
        df = pd.read_excel(excel_path)

        # 检查必要的列是否存在
        if '发票链接' not in df.columns or '交易主单' not in df.columns:
            raise ValueError("Excel文件中必须包含'发票链接'和'交易主单'列")

        # 统计信息
        total_count = len(df)
        success_count = 0
        failed_count = 0
        failed_items = []

        print(f"共找到 {total_count} 条发票记录")

        # 遍历每一行处理发票
        for index, row in df.iterrows():
            pdf_url = row['发票链接']
            transaction_id = row['交易主单']

            # 跳过空链接
            if not pdf_url or pd.isna(pdf_url) or not (
                    str(pdf_url).startswith('https') or str(pdf_url).startswith('http')):
                print(f"第{index + 1}行: 发票链接为空或无效，跳过")
                failed_count += 1
                failed_items.append({
                    'index': index + 1,
                    'transaction_id': transaction_id,
                    'reason': '发票链接为空或无效'
                })
                continue

            if pd.isna(transaction_id):
                print(f"第{index + 1}行: 交易主单为空，跳过")
                failed_count += 1
                failed_items.append({
                    'index': index + 1,
                    'transaction_id': 'N/A',
                    'reason': '交易主单为空'
                })
                continue

            # 转换为字符串并清理文件名
            transaction_id = str(transaction_id).strip()
            # 清理文件名中的非法字符
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                transaction_id = transaction_id.replace(char, '_')

            try:
                print(f"正在处理第{index + 1}行: {transaction_id}")

                # 下载PDF文件
                response = requests.get(pdf_url, timeout=30)
                response.raise_for_status()

                # 转换PDF为图片（指定poppler路径）
                if poppler_path and os.path.exists(poppler_path):
                    images = pdf2image.convert_from_bytes(
                        response.content,
                        dpi=dpi,
                        poppler_path=poppler_path
                    )
                else:
                    images = pdf2image.convert_from_bytes(response.content, dpi=dpi)

                # 保存图片
                for i, image in enumerate(images):
                    if len(images) == 1:
                        filename = f"{transaction_id}.jpg"
                    else:
                        filename = f"{transaction_id}_第{i + 1}页.jpg"

                    filepath = os.path.join(output_dir, filename)
                    image.save(filepath, 'JPEG', quality=95)
                    print(f"  已保存: {filename}")

                success_count += 1

            except requests.RequestException as e:
                print(f"  下载失败: {e}")
                failed_count += 1
                failed_items.append({
                    'index': index + 1,
                    'transaction_id': transaction_id,
                    'reason': f'下载失败: {str(e)}'
                })
            except pdf2image.exceptions.PDFInfoNotInstalledError:
                error_msg = "未安装poppler或未正确配置PATH，请安装poppler"
                print(f"  {error_msg}")
                failed_count += 1
                failed_items.append({
                    'index': index + 1,
                    'transaction_id': transaction_id,
                    'reason': error_msg
                })
            except pdf2image.exceptions.PDFPageCountError:
                error_msg = "无法获取PDF页数，可能是PDF文件损坏"
                print(f"  {error_msg}")
                failed_count += 1
                failed_items.append({
                    'index': index + 1,
                    'transaction_id': transaction_id,
                    'reason': error_msg
                })
            except Exception as e:
                print(f"  转换失败: {e}")
                failed_count += 1
                failed_items.append({
                    'index': index + 1,
                    'transaction_id': transaction_id,
                    'reason': f'转换失败: {str(e)}'
                })

        # 输出统计结果
        print("\n" + "=" * 50)
        print("处理完成!")
        print(f"总计: {total_count} 条")
        print(f"成功: {success_count} 条")
        print(f"失败: {failed_count} 条")

        if failed_items:
            print("\n失败详情:")
            for item in failed_items:
                print(f"  第{item['index']}行 [{item['transaction_id']}]: {item['reason']}")

        return {
            'total': total_count,
            'success': success_count,
            'failed': failed_count,
            'failed_details': failed_items
        }

    except FileNotFoundError:
        print(f"错误: 找不到文件 {excel_path}")
        return None
    except Exception as e:
        print(f"处理Excel文件时发生错误: {e}")
        return None


def batch_process_invoices(excel_paths, output_dir="./发票图片", dpi=200, poppler_path=None):
    """
    批量处理多个Excel文件

    Args:
        excel_paths (list): Excel文件路径列表
        output_dir (str): 输出目录
        dpi (int): 图片分辨率
        poppler_path (str): poppler安装路径
    """

    for excel_path in excel_paths:
        print(f"\n开始处理文件: {excel_path}")
        print("-" * 50)
        result = process_invoice_excel(excel_path, output_dir, dpi, poppler_path)

        if result:
            print(f"文件 {excel_path} 处理完成")
        else:
            print(f"文件 {excel_path} 处理失败")


# 使用示例
if __name__ == "__main__":
    # Windows系统需要指定poppler路径
    # 请根据您的实际安装路径修改
    poppler_path = r"C:\poppler\Library\bin"  # 示例路径，请修改为实际路径

    # 处理单个Excel文件
    excel_file = r"E:\1\河南银联无发票.xlsx"
    result = process_invoice_excel(
        excel_file,
        output_dir=r"E:\1\发票图片",
        dpi=200,
        poppler_path=poppler_path  # Windows系统需要指定此参数
    )

    # 如果要处理多个Excel文件
    # excel_files = [
    #     r"E:\1\河南银联无发票.xlsx",
    #     r"E:\1\其他发票.xlsx"
    # ]
    # batch_process_invoices(excel_files, output_dir=r"E:\1\发票图片", dpi=200, poppler_path=poppler_path)
