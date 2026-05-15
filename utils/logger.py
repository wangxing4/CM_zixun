import logging
import os

def get_logger():
    logger = logging.getLogger("api_test")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # 👉 获取项目根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    log_dir = os.path.join(base_dir, "logs")

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    log_file = os.path.join(log_dir, "api.log")

    # 控制台
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 文件
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger