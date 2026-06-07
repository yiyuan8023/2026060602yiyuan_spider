# html_to_mysql.py
import os
from database import DBManager
from extra.logger_ import logger


def read_html_to_mysql(folder_path, table_name):
    """
    读取文件夹下的HTML文件并保存到MySQL数据库
    folder_path (str): HTML文件所在的文件夹路径
    """
    try:
        # 统计处理的文件数量
        processed_count = 0
        error_count = 0
        items = []

        # 遍历文件夹中的所有文件
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # 检查是否为HTML文件
                if file.lower().endswith((".html", ".htm")):
                    file_path = os.path.join(root, file)

                    try:
                        # 读取HTML文件内容
                        with open(file_path, "r", encoding="utf-8") as f:
                            html_content = f.read()
                            processed_count += 1
                            print(f" {html_content}")
                    except UnicodeDecodeError:
                        # 如果UTF-8解码失败，尝试其他编码
                        try:
                            with open(file_path, "r", encoding="gbk") as f:
                                html_content = f.read()
                        except UnicodeDecodeError:
                            print(f"无法解码文件: {file_path}")
                            error_count += 1
                            continue
                    except Exception as e:
                        print(f"读取文件 {file_path} 时出错: {e}")
                        error_count += 1
                        continue

                    # 获取文件大小
                    file_size = os.path.getsize(file_path)

                    # 准备插入数据
                    item = {
                        "file_path": file_path,
                        "file": file,
                        "html_content": html_content,
                        "file_size": file_size,
                    }
                    items.append(item)
        print(items)
        DBManager().update_insert_data(
            items, table_name, primary_key="file", uu_id=True, user=True
        )
        logger.info(f"{folder_path}的数据已入库")
        logger.info(f"成功处理文件数: {processed_count}")
        logger.info(f"出错文件数: {error_count}")
        # logger.info("-" * 100)
        logger.info(f"\n{'*' * 120}")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    # 指定HTML文件所在的文件夹路径
    folder_path_ = r"D:\1921681859\AA"
    table_name_ = f"gzh_html_files_202508"

    # 检查文件夹是否存在
    if not os.path.exists(folder_path_):
        logger.info(f"文件夹不存在: {folder_path_}")

    # 读取HTML文件并保存到数据库
    read_html_to_mysql(folder_path_, table_name_)
