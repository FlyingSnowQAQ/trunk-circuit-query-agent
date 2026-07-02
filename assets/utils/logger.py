"""
日志工具
"""
import logging
import sys


def setup_logger(log_file: str = None) -> logging.Logger:
    """配置日志"""
    logger = logging.getLogger("circuit_query")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(console)

    # 文件输出
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        ))
        logger.addHandler(fh)

    return logger
