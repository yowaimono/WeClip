from app.utils.logger import logger  # 导入你现有的 logger
import logging
from PyQt5.QtCore import QThread, pyqtSignal, QObject


class PyQt5Handler(logging.Handler, QObject):
    """
    自定义的 logging.Handler，用于将日志消息发送到 PyQt 信号。
    """
    emit_log = pyqtSignal(str)  # 定义一个 PyQt 信号

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(message)s]', datefmt='%H:%M:%S')

    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.emit_log.emit(log_entry)  # 发射信号
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)
