"""
开发说明：
- 作者：一元
- 创建时间：2026-06-08 14:17:23
- 最近修改：2026-06-08 14:17:23
- 文件用途：提供 jobs 任务脚本统一启动入口，集中设置项目根路径、工作目录和日志模式。
- 业务范围：适用于从项目根目录或外部调度器启动 jobs 目录下的单个 Python 任务脚本。
- 依赖入口：使用标准库 argparse、os、runpy、sys、pathlib；执行目标脚本前把项目根目录写入 sys.path。
- 验收方式：修改后执行 py_compile；使用 --help 验证参数；用安全样例或指定任务脚本验证路径解析和参数透传。
- 注意事项：必须在目标脚本导入 extra.logger_ 前设置 LOG_MODE；默认把工作目录切到项目根目录，避免旧脚本相对路径漂移。
"""

import argparse
import os
import runpy
import sys
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parent
VALID_LOG_MODES = {"file", "console", "both"}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """解析 runner 参数，并把未知参数原样留给目标任务脚本。"""
    parser = argparse.ArgumentParser(description="统一启动 jobs 任务脚本，自动设置项目根路径和日志模式。",)
    parser.add_argument(
        "job",
        help="任务脚本路径，建议使用 jobs 下的相对路径，也支持绝对路径。",
    )
    parser.add_argument(
        "--log-mode",
        choices=sorted(VALID_LOG_MODES),
        default=None,
        help="覆盖 LOG_MODE，可选 file、console、both；不传则保留现有环境变量或项目默认值。",
    )
    parser.add_argument(
        "--keep-cwd",
        action="store_true",
        help="保留当前工作目录；默认切换到项目根目录，兼容依赖相对路径的旧脚本。",
    )
    parser.add_argument(
        "--",
        dest="separator",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args, job_args = parser.parse_known_args(argv)
    args.job_args = job_args
    return args


def resolve_job_path(job: str) -> Path:
    """把用户输入的任务脚本路径解析为绝对路径，并限制在项目根目录内。"""
    raw_path = Path(job)
    job_path = raw_path if raw_path.is_absolute() else PROJECT_ROOT / raw_path
    job_path = job_path.resolve()

    try:
        job_path.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise SystemExit(f"任务脚本必须位于当前项目内：{job_path}") from exc

    if not job_path.exists():
        raise SystemExit(f"任务脚本不存在：{job_path}")
    if job_path.suffix.lower() != ".py":
        raise SystemExit(f"任务脚本必须是 Python 文件：{job_path}")

    return job_path


def setup_runtime(log_mode: str | None, keep_cwd: bool) -> None:
    """设置目标脚本启动环境，保证项目模块和日志配置优先稳定。"""
    project_root_text = str(PROJECT_ROOT)
    if project_root_text not in sys.path:
        sys.path.insert(0, project_root_text)

    if log_mode:
        os.environ["LOG_MODE"] = log_mode

    if not keep_cwd:
        os.chdir(PROJECT_ROOT)


def run_job(job_path: Path, job_args: Sequence[str]) -> None:
    """按脚本方式执行任务文件，并把后续参数伪装成目标脚本的命令行参数。"""
    old_argv = sys.argv[:]
    sys.argv = [str(job_path), *job_args]
    try:
        runpy.run_path(str(job_path), run_name="__main__")
    finally:
        sys.argv = old_argv


def main(argv: Sequence[str] | None = None) -> int:
    """命令行入口：解析参数、准备运行环境、执行目标任务。"""
    args = parse_args(argv)
    job_path = resolve_job_path(args.job)
    setup_runtime(args.log_mode, args.keep_cwd)
    run_job(job_path, args.job_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
