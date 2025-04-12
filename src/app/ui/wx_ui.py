from pathlib import Path
from typing import Dict, Optional
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QApplication, QDialog, QVBoxLayout, QListView, QAbstractItemView, QDialogButtonBox
from PyQt5.QtCore import Qt, QStringListModel, QThread, pyqtSignal, QObject
import os
import logging
import sys
import asyncio

from app.utils.logger import logger
from app.browser import BrowserManager
from .async_worker import ParseAlbumTask,DownloadTask,ArticleDownloadTask
from .selection_dialog import ArticleSelectionDialog

# 定义一个信号类，用于传递日志消息
class LogSignal(QtCore.QObject):
    log_message = QtCore.pyqtSignal(str)

class PyQt5Handler(logging.Handler):
    """
    A handler class which allows the logger to push records to a PyQt5 list view.
    """

    def __init__(self, list_view, log_signal):
        super().__init__()
        self.list_view = list_view
        self.log_signal = log_signal

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.log_message.emit(msg)  # 发射信号，传递日志消息

class Ui_Window(QObject):
    # 类级别信号定义（只需要定义一次）
    show_selection_dialog_signal = pyqtSignal(list, dict)  # 用于传递文章列表和配置

    def __init__(self):
        # 首先初始化QObject
        super().__init__()

        # 初始化成员变量
        self.manager = BrowserManager()
        self.download_task = None
        self.selected_path = ""
        self.default_dir = Path.home().joinpath("Desktop", "微信公众号文章")
        self.log_signal = LogSignal()
        self.selection_dialog = None
        self.article_list = []
        self.is_downloading = False  # 添加一个标志来跟踪下载状态

        # 连接信号
        self.show_selection_dialog_signal.connect(self.show_selection_dialog)

    def setupUi(self, Window):
        Window.setObjectName("Window")
        Window.resize(600, 400)
        self.verticalLayout = QtWidgets.QVBoxLayout(Window)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.linklabel = QtWidgets.QLabel(Window)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.linklabel.setFont(font)
        self.linklabel.setObjectName("linklabel")
        self.gridLayout_2.addWidget(self.linklabel, 0, 0, 1, 1)
        self.lineEdit = QtWidgets.QLineEdit(Window)
        self.lineEdit.setMaxLength(65535)
        self.lineEdit.setDragEnabled(False)
        self.lineEdit.setReadOnly(False)
        self.lineEdit.setClearButtonEnabled(False)
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout_2.addWidget(self.lineEdit, 0, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_2)
        self.logView = QtWidgets.QListWidget(Window)
        self.logView.setObjectName("logView")
        self.logView.setWordWrap(True)

        self.verticalLayout.addWidget(self.logView)

        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")

        # 创建一个子水平布局来包含 label 和 selectMode
        left_group_layout = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(Window)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName("label")
        left_group_layout.addWidget(self.label)

        self.selectMode = QtWidgets.QComboBox(Window)
        self.selectMode.setObjectName("selectMode")
        self.selectMode.addItems(["markdown", "pdf", "html"])
        left_group_layout.addWidget(self.selectMode)

        # 将包含 label 和 selectMode 的子布局添加到主布局
        self.horizontalLayout_3.addLayout(left_group_layout)

        # 中间的弹簧
        spacerItemMiddle1 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding,
                                                    QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItemMiddle1)

        self.clearLogButton = QtWidgets.QPushButton(Window)
        self.clearLogButton.setObjectName("clearLogButton")
        self.horizontalLayout_3.addWidget(self.clearLogButton)

        # 中间的弹簧
        spacerItemMiddle2 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding,
                                                    QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItemMiddle2)

        self.openDir = QtWidgets.QPushButton(Window)
        self.openDir.setObjectName("openDir")
        self.horizontalLayout_3.addWidget(self.openDir)

        # 中间的弹簧
        spacerItemMiddle3 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding,
                                                    QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItemMiddle3)

        self.importButton = QtWidgets.QPushButton(Window)
        self.importButton.setObjectName("importButton")
        self.horizontalLayout_3.addWidget(self.importButton)

        # 设置弹簧的伸缩因子，让它们均匀分布
        self.horizontalLayout_3.setStretch(0, 0)  # left_group_layout (包含 label 和 selectMode)
        self.horizontalLayout_3.setStretch(1, 1)  # spacerItemMiddle1
        self.horizontalLayout_3.setStretch(2, 0)  # clearLogButton
        self.horizontalLayout_3.setStretch(3, 1)  # spacerItemMiddle2
        self.horizontalLayout_3.setStretch(4, 0)  # openDir
        self.horizontalLayout_3.setStretch(5, 1)  # spacerItemMiddle3
        self.horizontalLayout_3.setStretch(6, 0)  # importButton


        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(Window)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.selectType = QtWidgets.QComboBox(Window)
        self.selectType.setObjectName("selectType")
        self.selectType.addItems(["文章", "合集", "批量"])
        self.horizontalLayout_2.addWidget(self.selectType)
        self.pathLine = QtWidgets.QLineEdit(Window)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.pathLine.setFont(font)
        self.pathLine.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.pathLine.setAutoFillBackground(False)
        self.pathLine.setReadOnly(True)
        self.pathLine.setObjectName("pathLine")

        self.horizontalLayout_2.addWidget(self.pathLine)
        self.selectPathButton = QtWidgets.QPushButton(Window)
        self.selectPathButton.setObjectName("selectPathButton")
        self.horizontalLayout_2.addWidget(self.selectPathButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        # 进度条
        self.progressBar = QtWidgets.QProgressBar(Window)
        self.progressBar.setObjectName("progressBar")

        self.progressBar.setRange(0, 10000)  # 将范围扩大100倍以支持小数
        self.progressBar.setFormat("%p%")  # 注意这里不带%()格式
        self.progressBar.hide()  # 初始时隐藏进度条


        self.verticalLayout.addWidget(self.progressBar)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.startButton = QtWidgets.QPushButton(Window)
        self.startButton.setObjectName("startButton")
        self.horizontalLayout.addWidget(self.startButton)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Window)
        QtCore.QMetaObject.connectSlotsByName(Window)

        self.selectPathButton.clicked.connect(self.open_file_dialog)
        self.openDir.clicked.connect(self.open_directory)
        self.clearLogButton.clicked.connect(self.clear_log)
        self.startButton.clicked.connect(self.start_download)
        self.importButton.clicked.connect(self.import_link)
        # 连接信号和槽
        self.log_signal.log_message.connect(self.update_log_view)

        self.selected_path = self.default_dir

        self.setup_logging()

    @QtCore.pyqtSlot(str)
    def update_log_view(self, msg):
        """Updates the QListWidget with the log message (runs in the main thread)."""
        item = QListWidgetItem(msg)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsSelectable)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.logView.addItem(item)
        self.logView.scrollToBottom()

    def retranslateUi(self, Window):
        _translate = QtCore.QCoreApplication.translate
        Window.setWindowTitle(_translate("Window", "微信公众号文章下载"))
        self.linklabel.setText(_translate("Window", "链接："))
        self.lineEdit.setPlaceholderText(_translate("Window", "输入文章或合集链接"))
        self.label.setText(_translate("Window", "下载类型"))
        self.clearLogButton.setText(_translate("Window", "清空日志"))
        self.openDir.setText(_translate("Window", "打开目录"))
        self.label_2.setText(_translate("Window", "导出类型"))
        self.importButton.setText(_translate("Window", "导入链接"))
        self.pathLine.setText(_translate("Window", ""))
        self.selectPathButton.setText(_translate("Window", "选择路径"))
        self.startButton.setText(_translate("Window", "开始下载"))
        self.pathLine.setText(_translate("Window", str(self.default_dir)))

    def setup_logging(self):
        """Sets up logging to the QListWidget."""
        self.log_handler = PyQt5Handler(self.logView, self.log_signal)
        self.log_handler.setLevel(logging.INFO)

        # Create a formatter
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(message)s]', datefmt='%H:%M:%S')
        self.log_handler.setFormatter(formatter)

        # Add the handler to your existing logger (imported from app.utils.logger)
        logger.addHandler(self.log_handler)

    def start_download(self):
        
        config = self.get_config()
        logger.info(f"--------------\n\n {config} \n\n----------------")

        # Disable the start button to prevent multiple clicks
        self.startButton.setEnabled(False)
        self.progressBar.setValue(0)  # Reset progress bar
        self.progressBar.hide()  # 初始时隐藏进度条

        # 新增代码
        if config['mode'] == '合集':
            self.parse_album_task = ParseAlbumTask(config, self.manager)
            self.parse_album_task.articles_parsed.connect(self.show_selection_dialog_signal.emit)  # 连接信号
            self.parse_album_task.finished.connect(lambda: logger.info("合集解析任务完成"))
            self.parse_album_task.error.connect(self.on_parse_album_error)
            self.parse_album_task.start()
        elif config['mode'] == '批量':
            self.article_list = [u.strip() for u in config['url'].split('\n') if u.strip()]
            self.show_selection_dialog_signal.emit(self.article_list, config)  # 直接发射信号
        else:
            # 直接下载文章
            self.start_article_download(config)

    def start_article_download(self, config):
        """启动单篇文章下载任务"""
        should_report_progress = config['mode'] in ['合集', '批量']
        self.download_task = DownloadTask(config, self.manager, should_report_progress)
        self.download_task.finished.connect(self.on_download_finished)
        self.download_task.progress.connect(self.update_progress)  # 连接进度信号

        # 启动下载任务
        self.progressBar.show()  # 显示进度条
        self.download_task.start()

    def on_parse_album_error(self, error):
        """处理合集解析任务的错误"""
        logger.error(f"合集解析任务出错: {error}")
        self.startButton.setEnabled(True)  # 重新启用开始按钮
        self.progressBar.hide()  # 隐藏进度条
        self.progressBar.setValue(0)  # 重置进度条值

    @QtCore.pyqtSlot(list, dict)
    def show_selection_dialog(self, article_list, config):
        """显示文章选择对话框"""
        self.selection_dialog = ArticleSelectionDialog(article_list, config, self.manager, QApplication.activeWindow())
        self.selection_dialog.articles_selected.connect(self.start_download_task)
        self.selection_dialog.dialog_closed.connect(self.on_selection_dialog_closed)
        self.selection_dialog.show()

    def on_selection_dialog_closed(self):
        """统一处理对话框关闭"""
        print("对话框已关闭")  # 调试用
        # 执行清理操作
        if hasattr(self, 'selection_dialog'):
            self.selection_dialog.deleteLater()
            del self.selection_dialog


    def start_download_task(self, config):
        """启动下载任务"""
        if config and config.get('articles'):
            
            self.download_task = ArticleDownloadTask(config, self.manager)
            self.download_task.finished.connect(self.on_download_finished)
            self.download_task.progress.connect(self.update_progress)
            self.download_task.start()
            self.progressBar.show()  # 显示进度条
            self.startButton.setEnabled(False)  # 禁用开始按钮
        else:
            logger.warning("没有选择任何文章，取消下载。")
            self.startButton.setEnabled(True)  # 重新启用开始按钮
            self.progressBar.hide()  # 隐藏进度条
            self.progressBar.setValue(0)  # 重置进度条值

    def on_download_finished(self):
        """
        Called when the download task finishes.
        """
        logger.info("下载完成")
        self.startButton.setEnabled(True)
        self.progressBar.hide()  # 下载完成后隐藏进度条
        self.progressBar.setValue(0)  # 重置进度条值

    def update_progress(self, value):
        """
        Updates the progress bar.
        """
        self.progressBar.setValue(value)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dir_path = QFileDialog.getExistingDirectory(None, "Select Directory")
        if dir_path:
            self.selected_path = dir_path
            self.pathLine.setText(self.selected_path)

    def open_directory(self):
        if self.selected_path:
            if os.path.exists(self.selected_path):
                os.startfile(self.selected_path)  # Windows
            else:
                logger.warning("Directory does not exist.")  # Use the imported logger
        else:
            logger.warning("No directory selected.")  # Use the imported logger

    def import_link(self):
        """打开文件选择框，选择一个文本文件，
        将文本文件的内容去除空行后赋值给 lineEdit。
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(QApplication.activeWindow(), "选择包含链接的文本文件", "",
                                                    "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as file:
                    links = [line.strip() for line in file if line.strip()]
                self.lineEdit.setText('\n'.join(links))  # 将链接以换行符分隔显示在 lineEdit 中
            except FileNotFoundError:
                # 可以添加错误处理，例如显示一个消息框告知用户文件未找到
                print(f"错误：文件未找到: {file_name}")
            except Exception as e:
                # 可以添加更详细的错误处理
                print(f"读取文件时发生错误: {e}")

    def clear_log(self):
        self.logView.clear()

    def get_config(self) -> Dict[str, str]:
        config = {
            "url": self.lineEdit.text(),
            "mode": self.selectType.currentText(),
            "format_type": self.selectMode.currentText(),
            "output_dir": self.pathLine.text()
        }

        return config

    def handle_start(self):
        config = self.get_config()
        logger.info("开始任务...")
        logger.info(
            f"下载链接：{config['url']}, 下载类型：{config['mode']}, 保存类型: {config['format_type']}, 保存路径: {config['output_dir']}")

    @QtCore.pyqtSlot()
    def on_selection_dialog_closed(self):
        """当选择对话框关闭时调用"""
        # 只有在没有下载任务运行时才启用开始按钮
        if not self.is_downloading:
            self.startButton.setEnabled(True)  # 重新启用开始按钮
            self.progressBar.hide()  # 隐藏进度条
            self.progressBar.setValue(0)  # 重置进度条值





if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()  # 创建 QMainWindow 实例
    from app.ui import Ui_Window
    ui = Ui_Window()
    ui.setupUi(window)  # 将 UI 设置到 QMainWindow 中

    window.show()
    sys.exit(app.exec_())

# 7. `app/parse_album_task.py` (合集解析任务)
