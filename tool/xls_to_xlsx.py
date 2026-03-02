import os
import pandas as pd
from openpyxl import Workbook


def convert_xls_to_xlsx(input_folder, output_folder=None):
    """
    将文件夹中的所有xls文件转换为xlsx格式

    Parameters:
    input_folder (str): 包含xls文件的输入文件夹路径
    output_folder (str): 输出xlsx文件的文件夹路径，默认与输入文件夹相同
    """

    # 如果未指定输出文件夹，则使用输入文件夹
    if output_folder is None:
        output_folder = input_folder

    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        if filename.endswith(".xls") and not filename.startswith("~$"):
            # 构建完整的文件路径
            xls_path = os.path.join(input_folder, filename)
            xlsx_filename = filename.replace(".xls", ".xlsx")
            xlsx_path = os.path.join(output_folder, xlsx_filename)

            try:
                # 读取xls文件
                df = pd.read_excel(xls_path)

                # 保存为xlsx格式
                df.to_excel(xlsx_path, index=False)
                print(f"成功转换: {filename} -> {xlsx_filename}")

            except Exception as e:
                print(f"转换失败 {filename}: {str(e)}")


# 使用示例
if __name__ == "__main__":
    # 指定包含xls文件的文件夹路径
    input_folder = r"C:\Users\admin\Desktop\保健品类目\飞瓜商品鱼油"
    output_folder = r"C:\Users\admin\Desktop\保健品类目\飞瓜商品已处理"

    # 调用转换函数
    convert_xls_to_xlsx(input_folder)
