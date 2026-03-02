"""
扫描系统中所有程序及其启动位置的工具
"""

import os
import sys
import winreg
import psutil
from pathlib import Path


def get_installed_programs_from_registry():
    """
    从Windows注册表获取已安装程序信息

    Returns:
        list: 程序信息列表，每个元素为包含名称和安装位置的字典
    """
    programs = []

    # 注册表路径
    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    for reg_path in reg_paths:
        try:
            # 打开注册表键
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            # 遍历所有子键
            for i in range(winreg.QueryInfoKey(key)[0]):
                subkey_name = winreg.EnumKey(key, i)
                subkey_path = f"{reg_path}\\{subkey_name}"

                try:
                    subkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path)

                    # 获取程序显示名称
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    except FileNotFoundError:
                        # 如果没有DisplayName则跳过
                        winreg.CloseKey(subkey)
                        continue

                    # 尝试获取安装位置
                    try:
                        install_location = winreg.QueryValueEx(
                            subkey, "InstallLocation"
                        )[0]
                    except FileNotFoundError:
                        install_location = ""

                    # 尝试获取卸载字符串（可能包含可执行文件路径）
                    try:
                        uninstall_string = winreg.QueryValueEx(
                            subkey, "UninstallString"
                        )[0]
                    except FileNotFoundError:
                        uninstall_string = ""

                    programs.append(
                        {
                            "name": display_name,
                            "install_location": install_location,
                            "uninstall_string": uninstall_string,
                            "type": "Installed Program",
                        }
                    )
                    winreg.CloseKey(subkey)
                except (FileNotFoundError, OSError):
                    pass

            winreg.CloseKey(key)
        except FileNotFoundError:
            pass

    return programs


def get_start_menu_programs():
    """
    获取开始菜单中的程序快捷方式

    Returns:
        list: 程序信息列表，每个元素为包含名称和目标路径的字典
    """
    programs = []

    # 开始菜单路径
    start_menu_paths = [
        os.path.join(
            os.environ.get("PROGRAMDATA", ""),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
        ),
        os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
        ),
    ]

    # 检查是否安装了win32com库
    try:
        import win32com.client

        has_win32 = True
    except ImportError:
        has_win32 = False
        print("注意: 未安装pywin32库，无法解析快捷方式目标")

    for start_menu_path in start_menu_paths:
        if os.path.exists(start_menu_path):
            # 遍历所有.lnk文件
            for root, dirs, files in os.walk(start_menu_path):
                for file in files:
                    if file.endswith(".lnk"):
                        shortcut_path = os.path.join(root, file)
                        target_path = ""

                        if has_win32:
                            try:
                                # 解析快捷方式
                                shell = win32com.client.Dispatch("WScript.Shell")
                                shortcut = shell.CreateShortCut(shortcut_path)
                                target_path = shortcut.Targetpath
                            except Exception:
                                pass

                        programs.append(
                            {
                                "name": file[:-4],  # 去掉.lnk扩展名
                                "target_path": target_path,
                                "shortcut_path": shortcut_path,
                                "type": "Start Menu Shortcut",
                            }
                        )

    return programs


def scan_common_program_directories():
    """
    扫描常见的程序安装目录

    Returns:
        list: 程序信息列表，每个元素为包含名称和路径的字典
    """
    # 常见程序安装路径
    program_paths = [
        os.environ.get("PROGRAMFILES", ""),
        os.environ.get("PROGRAMFILES(X86)", ""),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Roaming"),
    ]

    programs = []

    for program_path in program_paths:
        if os.path.exists(program_path):
            try:
                for item in os.listdir(program_path):
                    item_path = os.path.join(program_path, item)
                    if os.path.isdir(item_path):
                        # 查找可执行文件
                        exe_files = []
                        try:
                            for root, dirs, files in os.walk(item_path):
                                for file in files:
                                    if file.endswith(".exe") and file.lower() not in [
                                        "unins000.exe",
                                        "uninstall.exe",
                                        "setup.exe",
                                        "installer.exe",
                                    ]:
                                        exe_files.append(os.path.join(root, file))
                                # 通常只需要查找第一层目录
                                break
                        except PermissionError:
                            pass

                        if exe_files:
                            programs.append(
                                {
                                    "name": item,
                                    "install_path": item_path,
                                    "executables": exe_files,
                                    "type": "Directory Scan",
                                }
                            )
            except PermissionError:
                pass

    return programs


def get_running_processes():
    """
    获取当前运行的进程信息

    Returns:
        list: 进程信息列表，每个元素为包含名称、PID和可执行文件路径的字典
    """
    processes = []
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            processes.append(
                {
                    "name": proc.info["name"],
                    "pid": proc.info["pid"],
                    "exe_path": proc.info["exe"] or "Unknown",
                    "type": "Running Process",
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes


def scan_all_programs():
    """
    综合扫描所有程序信息

    Returns:
        dict: 包含不同类型程序信息的字典
    """
    print("正在扫描已安装程序...")
    installed_programs = get_installed_programs_from_registry()

    print("正在扫描开始菜单程序...")
    start_menu_programs = get_start_menu_programs()

    print("正在扫描常见程序目录...")
    directory_programs = scan_common_program_directories()

    print("正在获取运行中的进程...")
    running_processes = get_running_processes()

    return {
        "installed_programs": installed_programs,
        "start_menu_programs": start_menu_programs,
        "directory_programs": directory_programs,
        "running_processes": running_processes,
    }


def save_programs_to_file(programs_data, output_file="programs_list.txt"):
    """
    将程序信息保存到文件

    Args:
        programs_data (dict): 程序信息数据
        output_file (str): 输出文件名
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("系统程序扫描结果\n")
        f.write("=" * 50 + "\n\n")

        # 已安装程序
        f.write(f"已安装程序 (共{len(programs_data['installed_programs'])}个):\n")
        f.write("-" * 30 + "\n")
        for program in programs_data["installed_programs"]:
            f.write(f"程序名称: {program['name']}\n")
            f.write(f"安装位置: {program['install_location']}\n")
            if program["uninstall_string"]:
                f.write(f"卸载路径: {program['uninstall_string']}\n")
            f.write("\n")

        # 开始菜单程序
        f.write(f"开始菜单程序 (共{len(programs_data['start_menu_programs'])}个):\n")
        f.write("-" * 30 + "\n")
        for program in programs_data["start_menu_programs"]:
            f.write(f"程序名称: {program['name']}\n")
            f.write(f"目标路径: {program['target_path']}\n")
            f.write(f"快捷方式: {program['shortcut_path']}\n")
            f.write("\n")

        # 目录扫描程序
        f.write(f"目录扫描程序 (共{len(programs_data['directory_programs'])}个):\n")
        f.write("-" * 30 + "\n")
        for program in programs_data["directory_programs"]:
            f.write(f"程序名称: {program['name']}\n")
            f.write(f"安装路径: {program['install_path']}\n")
            f.write("可执行文件:\n")
            for exe in program["executables"][:5]:  # 只显示前5个
                f.write(f"  - {exe}\n")
            if len(program["executables"]) > 5:
                f.write(f"  ... 还有{len(program['executables']) - 5}个可执行文件\n")
            f.write("\n")

        # 运行中进程
        f.write(f"运行中进程 (共{len(programs_data['running_processes'])}个):\n")
        f.write("-" * 30 + "\n")
        for process in programs_data["running_processes"][:50]:  # 只显示前50个
            f.write(f"进程名称: {process['name']}\n")
            f.write(f"进程ID: {process['pid']}\n")
            f.write(f"可执行路径: {process['exe_path']}\n")
            f.write("\n")

        if len(programs_data["running_processes"]) > 50:
            f.write(f"... 还有{len(programs_data['running_processes']) - 50}个进程\n")


def main():
    """
    主函数
    """
    print("开始扫描系统程序...")
    programs_data = scan_all_programs()

    print("\n扫描完成，结果统计:")
    print(f"已安装程序: {len(programs_data['installed_programs'])} 个")
    print(f"开始菜单程序: {len(programs_data['start_menu_programs'])} 个")
    print(f"目录扫描程序: {len(programs_data['directory_programs'])} 个")
    print(f"运行中进程: {len(programs_data['running_processes'])} 个")

    # 保存到文件
    save_programs_to_file(programs_data)
    print("\n结果已保存到 programs_list.txt 文件中")

    # 显示部分示例
    print("\n部分程序示例:")
    print("=" * 50)
    if programs_data["installed_programs"]:
        program = programs_data["installed_programs"][0]
        print(f"示例已安装程序: {program['name']}")
        print(f"  安装位置: {program['install_location']}")

    if programs_data["running_processes"]:
        process = programs_data["running_processes"][0]
        print(f"示例运行进程: {process['name']} (PID: {process['pid']})")
        print(f"  可执行路径: {process['exe_path']}")


if __name__ == "__main__":
    main()
