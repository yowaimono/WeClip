import logging
import sys

# 创建一个日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建一个控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# 创建一个格式器
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(message)s]', datefmt='%H:%M:%S')  # 添加 datefmt
console_handler.setFormatter(formatter)

# 将处理器添加到日志记录器
# logger.addHandler(console_handler)
