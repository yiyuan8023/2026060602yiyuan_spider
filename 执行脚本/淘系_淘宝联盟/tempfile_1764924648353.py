from extra.logger_ import logger,error_logs, error_logs2

try:
    A = 1/0
except Exception as e:
    # logger.info("cookie为空或者已失效")
    logger.error("cookie为空或者已失效")
    # logger.error(f"捕获异常: {str(e)}")  # 这会被收集到 error_logs
    error_logs.append (f"捕获异常: {str(e)}")
    print(error_logs)
