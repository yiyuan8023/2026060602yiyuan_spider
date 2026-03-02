import os
import fnmatch
from typing import List


def list_file_path(
    folder_path: str,
    include_subfolders: bool = True,
    file_pattern: str = "*",
    file_extension: str = None,
) -> List[str]:
    """
    列出文件夹中的所有文件
    :param folder_path: 目标文件夹路径
    :param include_subfolders: 是否包含子文件夹中的文件
    :param file_pattern: 文件名通配符模式，如 '*.py', 'test_*' 等
    :param file_extension: 文件扩展名，如 '.py', '.txt' 等
    :return: 文件绝对路径列表
    """
    files = []

    if include_subfolders:
        # 递归遍历所有子文件夹
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                abs_path = os.path.abspath(file_path)

                # 检查通配符匹配
                if not fnmatch.fnmatch(filename, file_pattern):
                    continue

                # 检查文件扩展名
                if file_extension and not filename.lower().endswith(
                    file_extension.lower()
                ):
                    continue

                files.append(abs_path)
    else:
        # 只遍历当前文件夹
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                abs_path = os.path.abspath(item_path)

                # 检查通配符匹配
                if not fnmatch.fnmatch(item, file_pattern):
                    continue

                # 检查文件扩展名
                if file_extension and not item.lower().endswith(file_extension.lower()):
                    continue

                files.append(abs_path)

    # 按文件修改时间升序排列
    files.sort(key=lambda x: os.path.getmtime(x))

    return files


if __name__ == "__main__":
    # A = list_file_path(r"E:\1", include_subfolders=True, file_pattern="*", file_extension="xlsx")
    B = list_file_path(r"E:\1", file_pattern="S202*", file_extension="xlsx")
    # print(A)
    print(B)
