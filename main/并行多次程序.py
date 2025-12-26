# run_multiple_programs.py
import subprocess
import threading
import time
from typing import List, Dict
from extra.logger_ import logger


def run_single_program(program_info: Dict, results: Dict, index: int):
    """
    运行单个程序

    Args:
        program_info: 程序信息字典
        results: 结果存储字典
        index: 程序索引
    """
    try:
        name = program_info.get('name', f'程序{index}')
        command = program_info['command']
        timeout = program_info.get('timeout', 600)

        logger.info(f"开始执行 {name}: {' '.join(command)}")

        start_time = time.time()
        # 修复编码问题：显式指定编码为 utf-8
        result = subprocess.run(
            command,
            capture_output=True,  # 捕获输出，但是不显示输出
            text=True,
            timeout=timeout,
            cwd=program_info.get('cwd'),  # 工作目录
            encoding='utf-8',  # 指定编码
            errors='ignore'  # 忽略编码错误
        )
        end_time = time.time()

        execution_time = end_time - start_time

        if result.returncode == 0:
            logger.info(f"{name} 执行成功，耗时 {execution_time:.2f} 秒")
            results[index] = {
                'name': name,
                'status': 'success',
                'output': result.stdout,
                'execution_time': execution_time
            }
        else:
            logger.error(f"{name} 执行失败: {result.stderr}")
            results[index] = {
                'name': name,
                'status': 'failed',
                'error': result.stderr,
                'execution_time': execution_time
            }

    except subprocess.TimeoutExpired:
        logger.error(f"{program_info.get('name', f'程序{index}')} 执行超时")
        results[index] = {
            'name': program_info.get('name', f'程序{index}'),
            'status': 'timeout',
            'execution_time': timeout
        }
    except Exception as e:
        logger.error(f"执行 {program_info.get('name', f'程序{index}')} 时出错: {e}")
        results[index] = {
            'name': program_info.get('name', f'程序{index}'),
            'status': 'error',
            'error': str(e)
        }


def run_multiple_programs(programs: List[Dict]) -> Dict:
    """
    并行执行多个程序
    programs: 程序列表，每个元素包含命令和其他配置
    Dict: 执行结果
    """
    logger.info(f"开始并行执行 {len(programs)} 个程序")

    # 存储执行结果
    results = {}
    threads = []

    # 为每个程序创建线程
    for i, program in enumerate(programs):
        thread = threading.Thread(
            target=run_single_program,
            args=(program, results, i)
        )
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 统计结果
    success_count = sum(1 for result in results.values() if result['status'] == 'success')
    failed_count = len(programs) - success_count

    logger.info(f"执行完成: 成功 {success_count} 个，失败 {failed_count} 个")

    return results


def main():
    """
    主函数 - 执行多个程序示例
    """
    # 定义要执行的程序列表
    programs_to_run = [
        {
            'name': '淘宝联盟CPS订单明细',
            'command': ['python', 'tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505.py'],
            'cwd': r'C:\Users\admin\Desktop\yiyuan_spider\执行脚本\淘系_淘宝联盟',
            'timeout': 3600
        },
        {
            'name': '淘宝联盟商品分析',
            'command': ['python', 'tb_tk_淘宝联盟_商品分析_202504.py'],
            'cwd': r'C:\Users\admin\Desktop\yiyuan_spider\执行脚本\淘系_淘宝联盟',
            'timeout': 1800
        },
        {
            'name': '我报名的商品',
            'command': ['python', 'tb_tk_淘宝联盟_服务商合作_普通招商_我报名的活动_报名的商品_202509.py'],
            'cwd': r'C:\Users\admin\Desktop\yiyuan_spider\执行脚本\淘系_淘宝联盟',
            'timeout': 1800
        },
        {
            'name': 'tb_tk_淘宝联盟_数据分析_定向计划报表_分天明细_202509',
            'command': ['python', 'tb_tk_淘宝联盟_数据分析_定向计划报表_分天明细_202509.py'],
            'cwd': r'C:\Users\admin\Desktop\yiyuan_spider\执行脚本\淘系_淘宝联盟',
            'timeout': 600
        }
    ]

    # 执行所有程序
    results = run_multiple_programs(programs_to_run)

    # 输出详细结果
    logger.info("=" * 50)
    logger.info("执行结果汇总:")
    for i, result in results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        logger.info(f"{status_icon} {result['name']}: {result['status']} "
                    f"({result['execution_time']:.2f}秒)")


if __name__ == "__main__":
    main()
