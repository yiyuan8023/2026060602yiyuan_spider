# run_programs_sequential.py
import subprocess
import time
from typing import List, Dict
from extra.logger_ import logger


def run_programs_sequentially(programs: List[Dict]) -> List[Dict]:
    """
    顺序执行多个程序

    Args:
        programs: 程序列表

    Returns:
        List[Dict]: 执行结果列表
    """
    results = []

    logger.info(f"开始顺序执行 {len(programs)} 个程序")

    for i, program in enumerate(programs):
        try:
            name = program.get('name', f'程序{i + 1}')
            command = program['command']
            timeout = program.get('timeout', 3600)
            cwd = program.get('cwd')

            logger.info(f"[{i + 1}/{len(programs)}] 开始执行 {name}")

            start_time = time.time()
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            end_time = time.time()

            execution_time = end_time - start_time

            if result.returncode == 0:
                logger.info(f"{name} 执行成功，耗时 {execution_time:.2f} 秒")
                results.append({
                    'name': name,
                    'status': 'success',
                    'output': result.stdout,
                    'execution_time': execution_time,
                    'index': i
                })
            else:
                logger.error(f"{name} 执行失败: {result.stderr}")
                results.append({
                    'name': name,
                    'status': 'failed',
                    'error': result.stderr,
                    'execution_time': execution_time,
                    'index': i
                })

        except subprocess.TimeoutExpired:
            logger.error(f"{program.get('name', f'程序{i + 1}')} 执行超时")
            results.append({
                'name': program.get('name', f'程序{i + 1}'),
                'status': 'timeout',
                'execution_time': timeout,
                'index': i
            })
        except Exception as e:
            logger.error(f"执行 {program.get('name', f'程序{i + 1}')} 时出错: {e}")
            results.append({
                'name': program.get('name', f'程序{i + 1}'),
                'status': 'error',
                'error': str(e),
                'index': i
            })

    # 统计结果
    success_count = sum(1 for result in results if result['status'] == 'success')
    logger.info(f"顺序执行完成: 总计 {len(programs)} 个，成功 {success_count} 个")

    return results


def main():
    """
    主函数
    """
    # 定义程序列表
    programs = [
        {
            'name': '数据采集脚本',
            'command': ['python', 'select_shop_date.py'],
            'cwd': r'C:\Users\admin\Desktop\yiyuan_spider',
            'timeout': 1800
        },
        {
            'name': '数据处理脚本',
            'command': ['python', 'data_processor.py'],
            'cwd': r'C:\Users\admin\Desktop\yiyuan_spider',
            'timeout': 3600
        },
        {
            'name': '数据上传脚本',
            'command': ['python', 'data_uploader.py'],
            'cwd': r'C:\Users\admin\Desktop\yiyuan_spider',
            'timeout': 1200
        }
    ]

    # 顺序执行
    results = run_programs_sequentially(programs)

    # 输出结果
    logger.info("=" * 50)
    logger.info("执行结果:")
    for result in results:
        status_text = {
            'success': '✅ 成功',
            'failed': '❌ 失败',
            'timeout': '⏰ 超时',
            'error': '💥 错误'
        }.get(result['status'], result['status'])

        logger.info(f"{status_text} {result['name']} ({result['execution_time']:.2f}秒)")


if __name__ == "__main__":
    main()
