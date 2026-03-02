from pathlib import Path
import shutil  # shutil 可以实现文件的移动拷贝等操作

from extra.logger_ import logger

# 创建path对象
root = Path(r"C:\Users\admin\Documents\Navicat\MySQL\Servers\223.5.242.173")
destination_folder = Path(r"Z:\数据库备份")


for p in root.rglob(
    "*.nb3"
):  # 递归遍历所有文件,root.rglob返回文件夹下所有满足条件的文件

    # print(f'{p.stem}{p.parent.name}{p.suffix}') #文件名称+文件夹名称+后缀

    # 构建保存路径文件夹
    f = destination_folder / p.parent.name  # 目标路径+文件夹名称

    # 创建文件夹，如果文件夹已存在，则不报错，make directory
    f.mkdir(exist_ok=True)

    # 构建文件储存路径，主要目的是文件改名字，如果无需更名，直接使用f即可
    a = f / f"{p.stem}{p.parent.name}{p.suffix}"  #
    print(a)

    # 复制文件
    try:
        move = shutil.move(p, a)  # 源路径，目标路径
        print(f"{a}移动完成")
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
    except PermissionError as e:
        logger.error(f"权限错误: {e}")
    except Exception as e:
        logger.error(f"其他错误: {e}")
