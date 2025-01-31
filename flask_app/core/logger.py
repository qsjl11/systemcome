import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(name: str) -> logging.Logger:
    """设置日志记录器

    Args:
        name: 日志记录器名称（通常是类名）

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 创建logs目录（如果不存在）
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # 创建日志文件名（使用当前日期）
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(logs_dir, f'{name}_{current_date}.log')

    # 创建文件处理器（每个文件最大10MB，保留5个备份）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
