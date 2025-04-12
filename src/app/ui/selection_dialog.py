from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QDialog, QListWidget, QVBoxLayout, QListView, 
                            QAbstractItemView, QPushButton, QHBoxLayout, 
                            QListWidgetItem, QCheckBox, QApplication, 
                            QDialogButtonBox, QMenu, QAction)
from PyQt5.QtCore import (Qt, QStringListModel, QThread, pyqtSignal, QObject, 
                         QUrl, QModelIndex)
from PyQt5.QtGui import QDesktopServices, QBrush, QColor, QFont
from pathlib import Path
from app.utils.logger import logger

class ArticleSelectionDialog(QDialog):
    articles_selected = pyqtSignal(dict)  # 用于传递选中的文章和配置
    dialog_closed = pyqtSignal()  # 用于传递对话框关闭信号

    def __init__(self, article_list, config, browser_manager, parent=None):
        super().__init__(parent)
        self.article_list = article_list
        self.config = config
        self.browser_manager = browser_manager
        self.selected_articles = []
        self.setWindowTitle("选择要下载的文章")
        self.setModal(False)  # 设置为非模态
        self.resize(500, 600)  # 设置窗口大小

        self.list_view = QListView()
        self.list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_model = ArticleListModel(self.article_list)  # 使用自定义模型
        self.list_view.setModel(self.list_model)

        # 允许复选框
        self.list_view.setSelectionMode(QAbstractItemView.MultiSelection)

        # 添加全选/全不选按钮
        self.select_all_button = QPushButton("全选")
        self.select_all_button.clicked.connect(self.select_all)
        self.deselect_all_button = QPushButton("全不选")
        self.deselect_all_button.clicked.connect(self.deselect_all)

        # 添加反选按钮
        self.invert_selection_button = QPushButton("反选")
        self.invert_selection_button.clicked.connect(self.invert_selection)

        # 添加一个复选框，用于控制是否显示文章链接
        self.show_link_checkbox = QCheckBox("显示文章链接")
        self.show_link_checkbox.stateChanged.connect(self.update_list_display)
        self.show_link = False  # 初始状态不显示链接

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # 布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.deselect_all_button)
        button_layout.addWidget(self.invert_selection_button)
        button_layout.addWidget(self.show_link_checkbox)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.list_view)
        layout.addWidget(button_box)
        self.setLayout(layout)
        
        self.setAttribute(Qt.WA_DeleteOnClose)  # 重要：关闭时删除对话框

        # 初始显示文章数量
        self.setWindowTitle(f"选择要下载的文章 (共 {len(self.article_list)} 篇)")

        # 启用自定义上下文菜单
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)
        
        # 连接点击信号
        self.list_view.clicked.connect(self.on_item_clicked)

    def select_all(self):
        """全选所有文章"""
        self.list_view.selectAll()

    def deselect_all(self):
        """取消选择所有文章"""
        self.list_view.clearSelection()

    def invert_selection(self):
        """反选当前选择的文章"""
        for i in range(self.list_model.rowCount()):
            index = self.list_model.index(i)
            if index in self.list_view.selectedIndexes():
                self.list_view.selectionModel().select(index, QtCore.QItemSelectionModel.Deselect)
            else:
                self.list_view.selectionModel().select(index, QtCore.QItemSelectionModel.Select)

    def update_list_display(self, state):
        """根据复选框的状态更新列表显示"""
        self.show_link = state == Qt.Checked
        self.list_model.show_link = self.show_link  # 更新模型中的 show_link 标志
        self.list_model.update_data()  # 更新模型数据
        self.list_model.layoutChanged.emit()  # 触发视图更新

    def on_item_clicked(self, index):
        """处理项目点击事件"""
        if not self.show_link_checkbox.isChecked():
            return
            
        article = self.article_list[index.row()]
        if isinstance(article, dict) and 'link' in article:
            QDesktopServices.openUrl(QUrl(article['link']))
            
    def show_context_menu(self, pos):
        """显示右键上下文菜单"""
        if not self.show_link_checkbox.isChecked():
            return
            
        index = self.list_view.indexAt(pos)
        if not index.isValid():
            return
            
        article = self.article_list[index.row()]
        if not isinstance(article, dict) or 'link' not in article:
            return
            
        menu = QtWidgets.QMenu()
        
        # 添加"打开链接"动作
        open_action = QAction("打开链接", self)
        open_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(article['link'])))
        menu.addAction(open_action)
        
        # 添加"复制链接"动作
        copy_action = QAction("复制链接", self)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(article['link']))
        menu.addAction(copy_action)
        
        # 显示菜单
        menu.exec_(self.list_view.mapToGlobal(pos))

    def accept(self):
        """处理点击确定按钮"""
        selected_indexes = self.list_view.selectedIndexes()
        self.selected_articles = [self.article_list[index.row()] for index in selected_indexes]

        # 创建新的配置，并启动下载任务
        output_dir = Path(self.config['output_dir'])
        if self.config['mode'] == '合集':
            album_name = self.article_list[0]['album_name'] if isinstance(self.article_list[0], dict) and 'album_name' in self.article_list[0] else "合集"
            output_dir = output_dir / Path(album_name)

        total = len(self.selected_articles)

        # 创建一个 DownloadTask 实例，并传入选定的文章列表
        download_config = {
            "articles": self.selected_articles,
            "format_type": self.config["format_type"],
            "output_dir": str(output_dir),
            "total": total
        }

        if self.selected_articles:
            self.articles_selected.emit(download_config)  # 发射信号，传递配置
        else:
            self.articles_selected.emit(download_config) # 发射None，表示没有选择任何文章

        super().accept()
        # self.dialog_closed.emit()  # 添加这行

    def reject(self):
        """处理点击取消按钮"""
        super().reject()
        self.dialog_closed.emit()  # 添加这行

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        event.accept()
        self.dialog_closed.emit()  # 添加这行

class ArticleListModel(QtCore.QAbstractListModel):
    def __init__(self, article_list, show_link=False, parent=None):
        super().__init__(parent)
        self.article_list = article_list
        self.show_link = show_link

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.article_list)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        article = self.article_list[index.row()]
        
        if role == Qt.DisplayRole:
            # 显示文本
            if isinstance(article, dict):
                text = article['link'] if self.show_link and 'link' in article else article['title'] if 'title' in article else str(article)
            else:
                text = str(article)
            return f"{index.row() + 1}. {text}"
            
        elif role == Qt.ToolTipRole:
            # 鼠标悬停时显示完整链接
            if isinstance(article, dict) and 'link' in article:
                return article['link']
            return None
            
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter | Qt.AlignLeft
            
        elif role == Qt.ForegroundRole:
            # 如果是链接模式，将链接显示为蓝色带下划线
            if self.show_link and isinstance(article, dict) and 'link' in article:
                return QBrush(QColor(0, 0, 255))
            return None
            
        elif role == Qt.FontRole:
            # 如果是链接模式，添加下划线
            if self.show_link and isinstance(article, dict) and 'link' in article:
                font = QFont()
                font.setUnderline(True)
                return font
            return None
            
        return None

    def flags(self, index):
        flags = super().flags(index)
        if index.isValid() and self.show_link and isinstance(self.article_list[index.row()], dict) and 'link' in self.article_list[index.row()]:
            flags |= Qt.ItemIsDragEnabled  # 允许拖拽
        return flags

    def update_data(self):
        """更新数据"""
        self.layoutChanged.emit()