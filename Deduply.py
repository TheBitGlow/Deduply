import os
import hashlib
from collections import defaultdict
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QProgressBar, QTextEdit,
                               QComboBox, QFileDialog, QMessageBox, QWidget)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont, QIcon
import sys

# 尝试导入 send2trash，不可用时回退到 os.remove
try:
    from send2trash import send2trash as _send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False


# ─── 资源路径（支持 PyInstaller 打包） ────────────────────────────
def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发和打包环境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)


# ─── 国际化翻译系统 ──────────────────────────────────────────────
TRANSLATIONS = {
    'zh': {
        'window_title': 'Deduply - 重复文件分析',
        'select_folder': '选择文件夹',
        'no_directory': '未选择目录',
        'selected_directory': '已选择目录: {}',
        'delete_strategy': '删除策略：',
        'keep_newest': '保留最新文件',
        'keep_oldest': '保留最旧文件',
        'scan_progress_fmt': '扫描进度：%v/%m',
        'analysis_progress_fmt': '分析进度：%v/%m',
        'start_scan': '开始扫描',
        'cancel_scan': '取消扫描',
        'delete_duplicates': '删除重复文件',
        'language': '语言',
        'error_no_directory': '错误：请先选择目录！',
        'error_no_duplicates': '错误：没有可删除的重复文件！',
        'confirm_delete_title': '确认删除',
        'confirm_delete_msg': '确定要删除重复文件吗？文件将被移入回收站。',
        'confirm_delete_msg_permanent': '确定要删除重复文件吗？此操作不可撤销！\n（建议安装 send2trash 库以支持回收站）',
        'scanning_directory': '正在扫描目录: {}',
        'analyzing_duplicates': '正在分析重复文件...',
        'no_duplicates_found': '未找到重复文件！',
        'report_title': '=== 重复文件分析报告 ===',
        'report_groups': '总共找到 {} 组重复文件',
        'hash_label': '哈希值: {}',
        'file_n': '文件 {}:',
        'path_label': '  路径: {}',
        'size_label': '  大小: {}',
        'mtime_label': '  修改时间: {}',
        'ctime_label': '  创建时间: {}',
        'space_saved': '总计可节省空间: {}',
        'keep_file': '保留文件: {}',
        'deleted_file': '已删除: {}',
        'recycled_file': '已移入回收站: {}',
        'delete_failed': '删除失败 {}: {}',
        'delete_complete': '删除完成！共删除 {} 个文件',
        'space_freed': '节省空间: {}',
        'scan_cancelled': '扫描已取消。',
        'scan_error': '扫描出错: {}',
        'file_read_error': '无法读取文件: {} ({})',
        'file_info_error': '无法获取文件信息: {} ({})',
        'select_folder_dialog': '选择文件夹',
        'zero_byte_skipped': '已跳过 {} 个零字节文件',
        'symlink_skipped': '已跳过符号链接: {}',
    },
    'en': {
        'window_title': 'Deduply - Duplicate File Analyzer',
        'select_folder': 'Select Folder',
        'no_directory': 'No directory selected',
        'selected_directory': 'Selected: {}',
        'delete_strategy': 'Strategy: ',
        'keep_newest': 'Keep Newest',
        'keep_oldest': 'Keep Oldest',
        'scan_progress_fmt': 'Scanning: %v/%m',
        'analysis_progress_fmt': 'Analyzing: %v/%m',
        'start_scan': 'Start Scan',
        'cancel_scan': 'Cancel',
        'delete_duplicates': 'Delete Duplicates',
        'language': 'Language',
        'error_no_directory': 'Error: Please select a directory first!',
        'error_no_duplicates': 'Error: No duplicate files to delete!',
        'confirm_delete_title': 'Confirm Delete',
        'confirm_delete_msg': 'Delete duplicate files? They will be sent to the Recycle Bin.',
        'confirm_delete_msg_permanent': 'Delete duplicate files? This cannot be undone!\n(Install send2trash for Recycle Bin support)',
        'scanning_directory': 'Scanning: {}',
        'analyzing_duplicates': 'Analyzing duplicates...',
        'no_duplicates_found': 'No duplicate files found!',
        'report_title': '=== Duplicate File Analysis Report ===',
        'report_groups': 'Found {} groups of duplicate files',
        'hash_label': 'Hash: {}',
        'file_n': 'File {}:',
        'path_label': '  Path: {}',
        'size_label': '  Size: {}',
        'mtime_label': '  Modified: {}',
        'ctime_label': '  Created: {}',
        'space_saved': 'Total space saveable: {}',
        'keep_file': 'Keeping: {}',
        'deleted_file': 'Deleted: {}',
        'recycled_file': 'Sent to Recycle Bin: {}',
        'delete_failed': 'Failed to delete {}: {}',
        'delete_complete': 'Done! Deleted {} files',
        'space_freed': 'Space freed: {}',
        'scan_cancelled': 'Scan cancelled.',
        'scan_error': 'Scan error: {}',
        'file_read_error': 'Cannot read file: {} ({})',
        'file_info_error': 'Cannot get file info: {} ({})',
        'select_folder_dialog': 'Select Folder',
        'zero_byte_skipped': 'Skipped {} zero-byte files',
        'symlink_skipped': 'Skipped symlink: {}',
    },
}

_current_lang = 'zh'


def tr(key, *args):
    """获取当前语言的翻译文本"""
    text = TRANSLATIONS.get(_current_lang, TRANSLATIONS['zh']).get(key, key)
    if args:
        return text.format(*args)
    return text


def set_language(lang):
    """切换当前语言"""
    global _current_lang
    _current_lang = lang


def format_size(size_bytes):
    """将字节数转换为人类可读格式"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 / 1024:.2f} MB"
    else:
        return f"{size_bytes / 1024 / 1024 / 1024:.2f} GB"


# ─── 工作线程信号类 ──────────────────────────────────────────────
class WorkerSignals(QObject):
    progress_updated = Signal(int)       # 文件扫描进度
    analysis_progress = Signal(int, int) # 重复分析进度 (当前值, 最大值)
    log_signal = Signal(str)
    error = Signal(str)                  # 线程异常信号
    finished = Signal()


# ─── 重复文件扫描工作线程 ────────────────────────────────────────
class DuplicateFinderWorker(QThread):
    def __init__(self, finder, signals):
        super().__init__()
        self.finder = finder
        self.signals = signals
        self._cancelled = False

    def cancel(self):
        """请求取消扫描"""
        self._cancelled = True

    def run(self):
        try:
            self.finder.scan_files(self.signals, lambda: self._cancelled)
            if not self._cancelled:
                self.finder.find_duplicates(self.signals, lambda: self._cancelled)
            if self._cancelled:
                self.signals.log_signal.emit(tr('scan_cancelled'))
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


# ─── 重复文件查找类 ──────────────────────────────────────────────
class DuplicateFileFinder:
    def __init__(self, directory):
        self.directory = directory
        self.size_groups = defaultdict(list)
        self.file_info_cache = {}
        self.hash_duplicates = defaultdict(list)
        self.total_files = 0
        self.zero_byte_count = 0

    def reset(self):
        """重置所有状态，用于重新扫描"""
        self.size_groups = defaultdict(list)
        self.file_info_cache = {}
        self.hash_duplicates = defaultdict(list)
        self.total_files = 0
        self.zero_byte_count = 0

    def calculate_hash(self, file_path, signals=None, block_size=65536, partial=False):
        """
        计算文件哈希值。
        partial=True 时只读取前 block_size 字节（快速预筛）。
        partial=False 时读取完整文件（最终确认）。
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                if partial:
                    data = f.read(block_size)
                    if data:
                        sha256.update(data)
                else:
                    while True:
                        data = f.read(block_size)
                        if not data:
                            break
                        sha256.update(data)
            return sha256.hexdigest()
        except Exception as e:
            if signals:
                signals.log_signal.emit(
                    f"<span style='color:orange'>{tr('file_read_error', file_path, e)}</span>")
            return None

    def get_file_info(self, file_path, signals=None):
        """获取文件信息，带缓存"""
        if file_path in self.file_info_cache:
            return self.file_info_cache[file_path]
        try:
            stats = os.stat(file_path)
            info = {
                'path': file_path,
                'size': stats.st_size,
                'mtime': datetime.fromtimestamp(stats.st_mtime),
                'ctime': datetime.fromtimestamp(stats.st_ctime),
            }
            self.file_info_cache[file_path] = info
            return info
        except Exception as e:
            if signals:
                signals.log_signal.emit(
                    f"<span style='color:orange'>{tr('file_info_error', file_path, e)}</span>")
            return None

    def scan_files(self, signals, is_cancelled):
        """扫描目录，按文件大小分组"""
        signals.log_signal.emit(tr('scanning_directory', self.directory))
        for root, dirs, files in os.walk(self.directory, followlinks=False):
            for filename in files:
                if is_cancelled():
                    return
                file_path = os.path.join(root, filename)

                # 跳过符号链接
                if os.path.islink(file_path):
                    signals.log_signal.emit(
                        f"<span style='color:gray'>{tr('symlink_skipped', file_path)}</span>")
                    continue

                file_info = self.get_file_info(file_path, signals)
                if file_info:
                    # 跳过零字节文件
                    if file_info['size'] == 0:
                        self.zero_byte_count += 1
                        continue
                    self.size_groups[file_info['size']].append(file_path)
                    self.total_files += 1
                    signals.progress_updated.emit(self.total_files)

        if self.zero_byte_count > 0:
            signals.log_signal.emit(tr('zero_byte_skipped', self.zero_byte_count))

    def find_duplicates(self, signals, is_cancelled):
        """
        分层哈希策略查找重复文件：
        第1层：按文件大小分组（scan_files 已完成）
        第2层：对同大小文件计算前 64KB 的快速哈希
        第3层：对快速哈希相同的文件计算完整哈希
        """
        signals.log_signal.emit(tr('analyzing_duplicates'))

        # 只处理有多个同大小文件的组
        candidate_groups = {
            size: files for size, files in self.size_groups.items() if len(files) > 1
        }
        total_groups = len(candidate_groups)
        current_group = 0

        for size, files in candidate_groups.items():
            if is_cancelled():
                return
            current_group += 1

            # 第2层：快速哈希（前 64KB）
            partial_hash_groups = defaultdict(list)
            for file_path in files:
                if is_cancelled():
                    return
                partial_hash = self.calculate_hash(
                    file_path, signals=signals, partial=True)
                if partial_hash:
                    partial_hash_groups[partial_hash].append(file_path)

            # 第3层：仅对快速哈希相同的文件做全量哈希
            for partial_hash, matching_files in partial_hash_groups.items():
                if len(matching_files) > 1:
                    full_hash_groups = defaultdict(list)
                    for file_path in matching_files:
                        if is_cancelled():
                            return
                        full_hash = self.calculate_hash(
                            file_path, signals=signals, partial=False)
                        if full_hash:
                            full_hash_groups[full_hash].append(file_path)

                    for hash_value, file_list in full_hash_groups.items():
                        if len(file_list) > 1:
                            self.hash_duplicates[hash_value] = [
                                self.get_file_info(f, signals) for f in file_list
                            ]

            signals.analysis_progress.emit(current_group, total_groups)

    def generate_report(self):
        """生成重复文件分析报告"""
        if not self.hash_duplicates:
            return tr('no_duplicates_found')

        report = f"<b>{tr('report_title')}</b><br>"
        report += tr('report_groups', len(self.hash_duplicates)) + "<br>"

        total_size = 0
        for hash_value, files in self.hash_duplicates.items():
            report += f"<br>{tr('hash_label', hash_value[:16] + '...')}<br>"
            valid_files = [f for f in files if f is not None]
            if not valid_files:
                continue
            group_size = valid_files[0]['size']
            total_size += group_size * (len(valid_files) - 1)

            for i, file in enumerate(valid_files, 1):
                report += f"{tr('file_n', i)}<br>"
                report += f"{tr('path_label', file['path'])}<br>"
                report += f"{tr('size_label', format_size(file['size']))}<br>"
                report += f"{tr('mtime_label', file['mtime'])}<br>"
                report += f"{tr('ctime_label', file['ctime'])}<br>"

        report += f"<br>{tr('space_saved', format_size(total_size))}"
        return report

    def delete_duplicates(self, keep='newest'):
        """删除重复文件，优先移入回收站"""
        deleted_count = 0
        saved_space = 0
        log = ""

        for hash_value, files in self.hash_duplicates.items():
            valid_files = [f for f in files if f is not None]
            if len(valid_files) <= 1:
                continue

            sorted_files = sorted(valid_files, key=lambda x: x['mtime'],
                                  reverse=(keep == 'newest'))
            keep_file = sorted_files[0]
            log += f"<br>{tr('keep_file', keep_file['path'])}<br>"

            for file in sorted_files[1:]:
                try:
                    if HAS_SEND2TRASH:
                        _send2trash(file['path'])
                        log += f"{tr('recycled_file', file['path'])}<br>"
                    else:
                        os.remove(file['path'])
                        log += f"{tr('deleted_file', file['path'])}<br>"
                    deleted_count += 1
                    saved_space += file['size']
                except Exception as e:
                    log += (f"<span style='color:red'>"
                            f"{tr('delete_failed', file['path'], e)}"
                            f"</span><br>")

        log += f"<br><b>{tr('delete_complete', deleted_count)}</b><br>"
        log += tr('space_freed', format_size(saved_space))
        return log


# ─── 主窗口类 ────────────────────────────────────────────────────
class DuplicateFileFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.finder = None
        self.worker = None
        self.is_running = False
        self.initUI()
        self.setAcceptDrops(True)  # 启用拖放支持

    def initUI(self):
        self.setWindowTitle(tr('window_title'))

        # 设置窗口图标
        icon_path = resource_path('./srch.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 设置窗口位置 - 屏幕居中靠下
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_width = 800
        window_height = 600
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) * 3 // 4
        self.setGeometry(x, y, window_width, window_height)

        self.setStyleSheet("""
            QWidget { background-color: #2E2E2E; color: #FFFFFF; font-family: '微软雅黑'; font-size: 10pt; }
            QPushButton { background-color: #4CAF50; border: none; color: white; padding: 10px 24px; font-size: 14px; margin: 4px 2px; border-radius: 4px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #666666; color: #999999; }
            QTextEdit, QProgressBar, QComboBox { background-color: #404040; color: #FFFFFF; border: 1px solid #606060; border-radius: 4px; padding: 5px; }
            QProgressBar::chunk { background-color: #4CAF50; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 文件选择布局
        file_layout = QHBoxLayout()
        self.btn_select_dir = QPushButton(tr('select_folder'))
        self.btn_select_dir.setFixedWidth(150)
        self.btn_select_dir.clicked.connect(self.select_directory)
        self.lbl_selected = QLabel(tr('no_directory'))
        file_layout.addWidget(self.btn_select_dir)
        file_layout.addSpacing(4)
        file_layout.addWidget(self.lbl_selected)
        layout.addLayout(file_layout)

        # 删除策略 + 语言切换
        method_layout = QHBoxLayout()
        self.lbl_strategy = QLabel(tr('delete_strategy'))
        self.combo_keep = QComboBox()
        self.combo_keep.addItems([tr('keep_newest'), tr('keep_oldest')])
        method_layout.addWidget(self.lbl_strategy)
        method_layout.addWidget(self.combo_keep)
        method_layout.addStretch()
        self.lbl_language = QLabel(tr('language') + ': ')
        self.combo_language = QComboBox()
        self.combo_language.addItems(['中文', 'English'])
        self.combo_language.setFixedWidth(100)
        self.combo_language.currentIndexChanged.connect(self.change_language)
        method_layout.addWidget(self.lbl_language)
        method_layout.addWidget(self.combo_language)
        layout.addLayout(method_layout)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setFormat(tr('scan_progress_fmt'))
        self.progress.setAlignment(Qt.AlignCenter)
        self.is_scanning = True
        layout.addWidget(self.progress)

        # 日志框
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton(tr('start_scan'))
        self.btn_start.clicked.connect(self.toggle_scan)
        self.btn_delete = QPushButton(tr('delete_duplicates'))
        self.btn_delete.clicked.connect(self.delete_duplicates)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

    # ── 语言切换 ─────────────────────────────────────────────────
    def change_language(self, index):
        """切换界面语言"""
        lang = 'zh' if index == 0 else 'en'
        set_language(lang)
        self.update_texts()

    def update_texts(self):
        """刷新所有静态 UI 文本为当前语言"""
        self.setWindowTitle(tr('window_title'))
        self.btn_select_dir.setText(tr('select_folder'))

        if self.finder is None:
            self.lbl_selected.setText(tr('no_directory'))
        else:
            self.lbl_selected.setText(tr('selected_directory', self.finder.directory))

        self.lbl_strategy.setText(tr('delete_strategy'))
        current_keep_idx = self.combo_keep.currentIndex()
        self.combo_keep.clear()
        self.combo_keep.addItems([tr('keep_newest'), tr('keep_oldest')])
        self.combo_keep.setCurrentIndex(current_keep_idx)

        self.lbl_language.setText(tr('language') + ': ')

        if self.is_running:
            self.btn_start.setText(tr('cancel_scan'))
        else:
            self.btn_start.setText(tr('start_scan'))

        self.btn_delete.setText(tr('delete_duplicates'))

        if self.is_scanning:
            self.progress.setFormat(tr('scan_progress_fmt'))
        else:
            self.progress.setFormat(tr('analysis_progress_fmt'))

    # ── 拖放事件 ─────────────────────────────────────────────────
    def dragEnterEvent(self, event):
        """处理拖入事件，仅接受文件夹"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
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
                self.lbl_selected.setText(tr('selected_directory', dir_path))
                self.btn_start.setEnabled(True)
                self.btn_delete.setEnabled(False)
                self.log.clear()
                self.progress.setValue(0)
                event.acceptProposedAction()
                return
        event.ignore()

    # ── 目录选择 ─────────────────────────────────────────────────
    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, tr('select_folder_dialog'))
        if dir_path:
            self.finder = DuplicateFileFinder(dir_path)
            self.lbl_selected.setText(tr('selected_directory', dir_path))
            self.btn_start.setEnabled(True)
            self.btn_delete.setEnabled(False)
            self.log.clear()
            self.progress.setValue(0)

    # ── 扫描控制 ─────────────────────────────────────────────────
    def toggle_scan(self):
        """切换扫描/取消状态"""
        if self.is_running:
            self.cancel_scan()
        else:
            self.start_scan()

    def start_scan(self):
        if not self.finder:
            self.log.append(
                f"<span style='color:red'>{tr('error_no_directory')}</span>")
            return

        # 重新扫描前重置状态
        self.finder.reset()

        self.is_running = True
        self.btn_start.setText(tr('cancel_scan'))
        self.btn_delete.setEnabled(False)

        self.signals = WorkerSignals()
        self.signals.progress_updated.connect(self.update_progress)
        self.signals.analysis_progress.connect(self.update_analysis_progress)
        self.signals.log_signal.connect(self.append_log)
        self.signals.error.connect(self.scan_error)
        self.signals.finished.connect(self.scan_finished)
        self.is_scanning = True
        self.progress.setFormat(tr('scan_progress_fmt'))
        self.progress.setValue(0)

        self.worker = DuplicateFinderWorker(self.finder, self.signals)
        self.worker.start()

    def cancel_scan(self):
        """请求取消当前扫描"""
        if self.worker:
            self.worker.cancel()

    # ── 进度更新 ─────────────────────────────────────────────────
    def update_progress(self, value):
        if self.is_scanning:
            self.progress.setMaximum(self.finder.total_files)
            self.progress.setValue(value)

    def update_analysis_progress(self, current, total):
        if self.is_scanning:
            self.is_scanning = False
            self.progress.setFormat(tr('analysis_progress_fmt'))
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    # ── 日志与错误 ───────────────────────────────────────────────
    def append_log(self, message):
        self.log.append(message)

    def scan_error(self, error_msg):
        self.log.append(
            f"<span style='color:red'>{tr('scan_error', error_msg)}</span>")

    # ── 扫描完成 ─────────────────────────────────────────────────
    def scan_finished(self):
        self.is_running = False
        self.btn_start.setText(tr('start_scan'))
        self.btn_start.setEnabled(True)
        self.btn_delete.setEnabled(
            bool(self.finder and self.finder.hash_duplicates))
        self.progress.setValue(self.progress.maximum())
        if self.finder and self.finder.hash_duplicates:
            self.log.append(self.finder.generate_report())

    # ── 删除操作 ─────────────────────────────────────────────────
    def delete_duplicates(self):
        if not self.finder or not self.finder.hash_duplicates:
            self.log.append(
                f"<span style='color:red'>{tr('error_no_duplicates')}</span>")
            return

        msg = tr('confirm_delete_msg') if HAS_SEND2TRASH else tr('confirm_delete_msg_permanent')
        reply = QMessageBox.question(
            self, tr('confirm_delete_title'), msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            keep = 'newest' if self.combo_keep.currentIndex() == 0 else 'oldest'
            log = self.finder.delete_duplicates(keep=keep)
            self.log.append(log)
            self.btn_delete.setEnabled(False)


# ─── 入口 ────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont('微软雅黑', 10))
    window = DuplicateFileFinderApp()
    window.show()
    sys.exit(app.exec())