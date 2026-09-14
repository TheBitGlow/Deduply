import os
import hashlib
import time
from collections import defaultdict
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QProgressBar, QTextEdit, 
                               QComboBox, QCheckBox, QFileDialog, QMessageBox, QWidget)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont, QIcon, QScreen
import sys

# 处理打包环境下的路径
def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发和打包环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包时的临时路径
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

# 工作线程信号类
class WorkerSignals(QObject):
    progress_updated = Signal(int)  # 文件扫描进度
    analysis_progress = Signal(int, int)  # 重复分析进度 (当前值, 最大值)
    log_signal = Signal(str)
    finished = Signal()

# 重复文件扫描工作线程
class DuplicateFinderWorker(QThread):
    def __init__(self, finder, signals):
        super().__init__()
        self.finder = finder
        self.signals = signals

    def run(self):
        self.finder.scan_files(self.signals)
        self.finder.find_duplicates(self.signals)
        self.signals.finished.emit()

# 重复文件查找类
class DuplicateFileFinder:
    def __init__(self, directory):
        self.directory = directory
        self.size_groups = defaultdict(list)
        self.hash_duplicates = defaultdict(list)
        self.total_files = 0

    def calculate_hash(self, file_path, block_size=65536):
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest()
        except Exception as e:
            return None

    def get_file_info(self, file_path):
        try:
            stats = os.stat(file_path)
            return {
                'path': file_path,
                'size': stats.st_size,
                'mtime': datetime.fromtimestamp(stats.st_mtime),
                'ctime': datetime.fromtimestamp(stats.st_ctime)
            }
        except Exception:
            return None

    def scan_files(self, signals):
        signals.log_signal.emit(f"正在扫描目录: {self.directory}")
        for root, _, files in os.walk(self.directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                file_info = self.get_file_info(file_path)
                if file_info:
                    self.size_groups[file_info['size']].append(file_path)
                    self.total_files += 1
                    signals.progress_updated.emit(self.total_files)

    def find_duplicates(self, signals):
        signals.log_signal.emit("正在分析重复文件...")
        total_groups = len([size for size, files in self.size_groups.items() if len(files) > 1])
        current_group = 0
        
        for size, files in self.size_groups.items():
            if len(files) > 1:
                current_group += 1
                temp_hash_dict = defaultdict(list)
                for file_path in files:
                    file_hash = self.calculate_hash(file_path)
                    if file_hash:
                        temp_hash_dict[file_hash].append(file_path)
                for hash_value, file_list in temp_hash_dict.items():
                    if len(file_list) > 1:
                        self.hash_duplicates[hash_value] = [
                            self.get_file_info(f) for f in file_list
                        ]
                signals.analysis_progress.emit(current_group, total_groups)

    def generate_report(self):
        if not self.hash_duplicates:
            return "未找到重复文件！"
        
        report = "<b>=== 重复文件分析报告 ===</b><br>"
        report += f"总共找到 {len(self.hash_duplicates)} 组重复文件<br>"
        
        total_size = 0
        for hash_value, files in self.hash_duplicates.items():
            report += f"<br>哈希值: {hash_value}<br>"
            group_size = files[0]['size']
            total_size += group_size * (len(files) - 1)
            
            for i, file in enumerate(files, 1):
                report += f"文件 {i}:<br>"
                report += f"  路径: {file['path']}<br>"
                report += f"  大小: {file['size']} bytes<br>"
                report += f"  修改时间: {file['mtime']}<br>"
                report += f"  创建时间: {file['ctime']}<br>"
        
        report += f"<br>总计可节省空间: {total_size / 1024 / 1024:.2f} MB"
        return report

    def delete_duplicates(self, keep='newest'):
        deleted_count = 0
        saved_space = 0
        log = ""
        
        for hash_value, files in self.hash_duplicates.items():
            if len(files) <= 1:
                continue
                
            sorted_files = sorted(files, key=lambda x: x['mtime'], 
                                reverse=(keep == 'newest'))
            keep_file = sorted_files[0]
            log += f"<br>保留文件: {keep_file['path']}<br>"
            
            for file in sorted_files[1:]:
                try:
                    os.remove(file['path'])
                    log += f"已删除: {file['path']}<br>"
                    deleted_count += 1
                    saved_space += file['size']
                except Exception as e:
                    log += f"<span style='color:red'>删除失败 {file['path']}: {e}</span><br>"

        log += f"<br><b>删除完成！共删除 {deleted_count} 个文件</b><br>"
        log += f"节省空间: {saved_space / 1024 / 1024:.2f} MB"
        return log

# 主窗口类
class DuplicateFileFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.finder = None
        self.setAcceptDrops(True)  # 启用拖放支持

    def initUI(self):
        self.setWindowTitle('Gearify - 重复文件分析')
        
        # 设置窗口图标 - 使用 resource_path 处理打包环境
        icon_path = resource_path('./srch.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"警告：图标文件未找到 - {icon_path}")
        
        # 设置窗口位置 - 屏幕居中靠下
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_width = 800
        window_height = 600
        x = (screen_geometry.width() - window_width) // 2  # 水平居中
        y = (screen_geometry.height() - window_height) * 3 // 4  # 垂直方向居中后向下偏移至3/4位置
        self.setGeometry(x, y, window_width, window_height)
        
        self.setStyleSheet("""
            QWidget { background-color: #2E2E2E; color: #FFFFFF; font-family: '微软雅黑'; font-size: 10pt; }
            QPushButton { background-color: #4CAF50; border: none; color: white; padding: 10px 24px; font-size: 14px; margin: 4px 2px; border-radius: 4px; }
            QPushButton:hover { background-color: #45a049; }
            QTextEdit, QProgressBar, QComboBox { background-color: #404040; color: #FFFFFF; border: 1px solid #606060; border-radius: 4px; padding: 5px; }
            QProgressBar::chunk { background-color: #4CAF50; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 文件选择布局
        file_layout = QHBoxLayout()
        self.btn_select_dir = QPushButton('选择文件夹')
        self.btn_select_dir.setFixedWidth(150)
        self.btn_select_dir.clicked.connect(self.select_directory)
        self.lbl_selected = QLabel('未选择目录')
        file_layout.addWidget(self.btn_select_dir)
        file_layout.addSpacing(4)
        file_layout.addWidget(self.lbl_selected)
        layout.addLayout(file_layout)

        # 删除策略选择
        method_layout = QHBoxLayout()
        self.combo_keep = QComboBox()
        self.combo_keep.addItems(["保留最新文件", "保留最旧文件"])
        method_layout.addWidget(QLabel("删除策略："))
        method_layout.addWidget(self.combo_keep)
        layout.addLayout(method_layout)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setFormat("扫描进度：%v/%m")
        self.progress.setAlignment(Qt.AlignCenter)
        self.is_scanning = True
        layout.addWidget(self.progress)

        # 日志框
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton('开始扫描')
        self.btn_start.clicked.connect(self.start_scan)
        self.btn_delete = QPushButton('删除重复文件')
        self.btn_delete.clicked.connect(self.delete_duplicates)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

    # 拖放事件处理
    def dragEnterEvent(self, event):
        """处理拖入事件，仅接受文件夹"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):  # 检查是否为目录
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """处理放下事件，设置拖入的文件夹"""
        urls = event.mimeData().urls()
        for url in urls:
            dir_path = url.toLocalFile()
            if os.path.isdir(dir_path):
                self.finder = DuplicateFileFinder(dir_path)
                self.lbl_selected.setText(f'已选择目录: {dir_path}')
                self.btn_start.setEnabled(True)
                self.btn_delete.setEnabled(False)
                self.log.clear()
                self.progress.setValue(0)
                event.acceptProposedAction()
                return
        event.ignore()

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_path:
            self.finder = DuplicateFileFinder(dir_path)
            self.lbl_selected.setText(f'已选择目录: {dir_path}')
            self.btn_start.setEnabled(True)
            self.btn_delete.setEnabled(False)
            self.log.clear()
            self.progress.setValue(0)

    def start_scan(self):
        if not self.finder:
            self.log.append("<span style='color:red'>错误：请先选择目录！</span>")
            return

        self.btn_start.setEnabled(False)
        self.signals = WorkerSignals()
        self.signals.progress_updated.connect(self.update_progress)
        self.signals.analysis_progress.connect(self.update_analysis_progress)
        self.signals.log_signal.connect(self.append_log)
        self.signals.finished.connect(self.scan_finished)
        self.is_scanning = True
        self.progress.setFormat("扫描进度：%v/%m")
        self.progress.setValue(0)

        self.worker = DuplicateFinderWorker(self.finder, self.signals)
        self.worker.start()

    def update_progress(self, value):
        if self.is_scanning:
            self.progress.setMaximum(self.finder.total_files)
            self.progress.setValue(value)

    def update_analysis_progress(self, current, total):
        if self.is_scanning:
            self.is_scanning = False
            self.progress.setFormat("分析进度：%v/%m")
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    def append_log(self, message):
        self.log.append(message)

    def scan_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_delete.setEnabled(bool(self.finder.hash_duplicates))
        self.progress.setValue(self.progress.maximum())
        self.log.append(self.finder.generate_report())

    def delete_duplicates(self):
        if not self.finder.hash_duplicates:
            self.log.append("<span style='color:red'>错误：没有可删除的重复文件！</span>")
            return

        reply = QMessageBox.question(self, "确认删除",
                                     "确定要删除重复文件吗？此操作不可撤销！",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            keep = 'newest' if self.combo_keep.currentText() == "保留最新文件" else 'oldest'
            log = self.finder.delete_duplicates(keep=keep)
            self.log.append(log)
            self.btn_delete.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont('微软雅黑', 10))
    window = DuplicateFileFinderApp()
    window.show()
    sys.exit(app.exec())