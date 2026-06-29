import json
import os
import shutil
from pathlib import Path

from extra.logger_ import logger

LOCAL_CONFIG_PATH = Path.cwd() / "config" / "local.json"
DEFAULT_DESTINATION = Path(r"Z:\数据库备份")


def load_local_paths():
    if not LOCAL_CONFIG_PATH.exists():
        return {}

    try:
        with LOCAL_CONFIG_PATH.open("r", encoding="utf-8") as file:
            config_data = json.load(file)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"本地配置文件格式错误: {LOCAL_CONFIG_PATH}") from exc

    path_config = config_data.get("paths", {})
    if not isinstance(path_config, dict):
        raise RuntimeError(f"本地配置项 paths 必须是对象: {LOCAL_CONFIG_PATH}")
    return path_config


def resolve_backup_paths():
    local_paths = load_local_paths()
    backup_root = os.environ.get("NAVICAT_BACKUP_ROOT") or local_paths.get("navicat_backup_root")
    if not backup_root:
        raise RuntimeError(
            "缺少 Navicat 备份目录，请在环境变量 NAVICAT_BACKUP_ROOT 或 "
            "config/local.json 的 paths.navicat_backup_root 中配置。"
        )

    destination = (
        os.environ.get("DATABASE_BACKUP_DESTINATION")
        or local_paths.get("database_backup_destination")
        or str(DEFAULT_DESTINATION)
    )

    root = Path(backup_root)
    if not root.exists():
        raise RuntimeError(f"Navicat 备份目录不存在: {root}")
    if not root.is_dir():
        raise RuntimeError(f"Navicat 备份目录不是文件夹: {root}")

    return root, Path(destination)


def move_backup_files():
    root, destination_folder = resolve_backup_paths()
    destination_folder.mkdir(parents=True, exist_ok=True)

    moved_count = 0
    for backup_file in root.rglob("*.nb3"):
        target_folder = destination_folder / backup_file.parent.name
        target_folder.mkdir(parents=True, exist_ok=True)

        target_file = target_folder / f"{backup_file.stem}{backup_file.parent.name}{backup_file.suffix}"
        logger.info("准备移动: %s -> %s", backup_file, target_file)

        try:
            shutil.move(str(backup_file), str(target_file))
            moved_count += 1
            logger.info("移动完成: %s", target_file)
        except FileNotFoundError as exc:
            logger.error("文件未找到: %s", exc)
        except PermissionError as exc:
            logger.error("权限错误: %s", exc)
        except Exception as exc:
            logger.error("移动失败: %s", exc)

    if moved_count == 0:
        logger.warning("未找到可移动的 .nb3 备份文件。源目录: %s", root)
    else:
        logger.info("备份文件移动完成，共处理 %s 个文件。", moved_count)


def main():
    move_backup_files()


if __name__ == "__main__":
    main()
