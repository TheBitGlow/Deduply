import os
import sys
import hashlib
import csv
import subprocess
from collections import defaultdict
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit,
    QComboBox, QFileDialog, QMessageBox, QWidget,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu,
    QTabWidget, QCheckBox, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QUrl
from PySide6.QtGui import QFont, QIcon, QAction, QDesktopServices, QCursor

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


# ─── 平台通用文件操作 ─────────────────────────────────────────────
def reveal_in_file_manager(file_path):
    """在文件管理器中定位并选中文件"""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return
    if sys.platform == 'win32':
        subprocess.run(['explorer', f'/select,{os.path.normpath(abs_path)}'], check=False)
    elif sys.platform == 'darwin':
        subprocess.run(['open', '-R', abs_path], check=False)
    else:
        subprocess.run(['xdg-open', os.path.dirname(abs_path)], check=False)


def open_file_with_default_app(file_path):
    """使用系统默认应用打开文件"""
    abs_path = os.path.abspath(file_path)
    if os.path.exists(abs_path):
        QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))


# ─── 国际化翻译系统 ──────────────────────────────────────────────
TRANSLATIONS = {
    'zh': {
        'window_title': 'Deduply - 重复文件分析清理工具',
        'select_folder': '选择文件夹',
        'no_directory': '未选择目录',
        'selected_directory': '已选目录: {}',
        'delete_strategy': '默认策略：',
        'keep_newest': '保留最新文件',
        'keep_oldest': '保留最旧文件',
        'filter_min_size': '最小大小：',
        'filter_size_all': '不限',
        'filter_size_10k': '> 10 KB',
        'filter_size_100k': '> 100 KB',
        'filter_size_1m': '> 1 MB',
        'filter_size_10m': '> 10 MB',
        'filter_skip_hidden': '跳过隐藏/系统目录',
        'tab_duplicates': '📋 重复文件列表',
        'tab_log': '📝 运行日志',
        'tree_header_file': '文件名 / 重复组',
        'tree_header_size': '大小',
        'tree_header_mtime': '修改时间',
        'tree_header_path': '完整路径',
        'btn_select_all': '全选待删项',
        'btn_deselect_all': '全部取消',
        'btn_export': '导出报告',
        'start_scan': '开始扫描',
        'cancel_scan': '取消扫描',
        'delete_duplicates': '删除勾选文件',
        'delete_duplicates_count': '删除勾选文件 ({})',
        'language': '语言',
        'error_no_directory': '错误：请先选择扫描目录！',
        'error_no_duplicates': '错误：未找到可删除的重复文件！',
        'no_items_checked': '提示：请至少勾选一个需要删除的文件！',
        'confirm_delete_title': '确认删除',
        'confirm_delete_msg': '确定要将选中的 {} 个文件移入回收站吗？\n总计将释放空间: {}',
        'confirm_delete_msg_permanent': '确定要永久删除选中的 {} 个文件吗？此操作不可撤销！\n（建议安装 send2trash 库支持回收站）\n总计将释放空间: {}',
        'scanning_directory': '正在扫描目录: {}',
        'indexing_progress_fmt': '正在索引文件... 已发现 {} 个',
        'analyzing_duplicates': '正在分析重复文件（分层哈希计算）...',
        'analysis_progress_fmt': '分析进度：%v/%m 组 (%p%)',
        'no_duplicates_found': '扫描完成，未发现重复文件！',
        'report_title': '=== 重复文件分析报告 ===',
        'report_groups': '总共找到 {} 组重复文件',
        'hash_label': '哈希值: {}',
        'file_n': '文件 {}:',
        'path_label': '  路径: {}',
        'size_label': '  大小: {}',
        'mtime_label': '  修改时间: {}',
        'space_saved': '总计可节省空间: {}',
        'group_title': '重复组 #{} ({} 个文件，单文件大小: {})',
        'group_reclaimable': '可释放: {}',
        'keep_file': '保留文件: {}',
        'deleted_file': '已永久删除: {}',
        'recycled_file': '已移入回收站: {}',
        'delete_failed': '删除失败 {}: {}',
        'delete_complete': '删除完成！成功清理 {} 个文件',
        'space_freed': '共释放空间: {}',
        'scan_cancelled': '扫描已由用户取消。',
        'scan_error': '扫描出错: {}',
        'file_read_error': '无法读取文件: {} ({})',
        'file_info_error': '无法获取文件信息: {} ({})',
        'dir_access_error': '跳过无法访问的目录: {} ({})',
        'select_folder_dialog': '选择要扫描的文件夹',
        'zero_byte_skipped': '已跳过 {} 个零字节文件',
        'symlink_skipped': '已跳过符号链接: {}',
        'status_summary': '共 {} 组重复文件 | 已勾选 {} 个文件待清理 (释放 {})',
        'menu_open_file': '打开文件',
        'menu_reveal': '在资源管理器中显示',
        'menu_copy_path': '复制完整路径',
        'export_dialog_title': '保存重复文件分析报告',
        'export_csv_filter': 'CSV 文件 (*.csv);;文本文件 (*.txt)',
        'export_success': '报告已成功导出至: {}',
        'export_failed': '导出报告失败: {}',
    },
    'en': {
        'window_title': 'Deduply - Duplicate File Cleaner',
        'select_folder': 'Select Folder',
        'no_directory': 'No directory selected',
        'selected_directory': 'Selected: {}',
        'delete_strategy': 'Default Strategy: ',
        'keep_newest': 'Keep Newest',
        'keep_oldest': 'Keep Oldest',
        'filter_min_size': 'Min Size: ',
        'filter_size_all': 'All',
        'filter_size_10k': '> 10 KB',
        'filter_size_100k': '> 100 KB',
        'filter_size_1m': '> 1 MB',
        'filter_size_10m': '> 10 MB',
        'filter_skip_hidden': 'Skip Hidden/System Folders',
        'tab_duplicates': '📋 Duplicate Files',
        'tab_log': '📝 Scan Log',
        'tree_header_file': 'Filename / Group',
        'tree_header_size': 'Size',
        'tree_header_mtime': 'Modified Time',
        'tree_header_path': 'Path',
        'btn_select_all': 'Select All Deletables',
        'btn_deselect_all': 'Deselect All',
        'btn_export': 'Export Report',
        'start_scan': 'Start Scan',
        'cancel_scan': 'Cancel',
        'delete_duplicates': 'Delete Checked',
        'delete_duplicates_count': 'Delete Checked ({})',
        'language': 'Language',
        'error_no_directory': 'Error: Please select a directory first!',
        'error_no_duplicates': 'Error: No duplicate files found to delete!',
        'no_items_checked': 'Notice: Please check at least one file to delete!',
        'confirm_delete_title': 'Confirm Deletion',
        'confirm_delete_msg': 'Move {} selected file(s) to Recycle Bin?\nSpace to be freed: {}',
        'confirm_delete_msg_permanent': 'Permanently delete {} selected file(s)? This cannot be undone!\n(Install send2trash for Recycle Bin support)\nSpace to be freed: {}',
        'scanning_directory': 'Scanning directory: {}',
        'indexing_progress_fmt': 'Indexing files... Found {}',
        'analyzing_duplicates': 'Analyzing duplicates (layered hashing)...',
        'analysis_progress_fmt': 'Analyzing: %v/%m groups (%p%)',
        'no_duplicates_found': 'Scan complete. No duplicate files found!',
        'report_title': '=== Duplicate File Analysis Report ===',
        'report_groups': 'Found {} groups of duplicate files',
        'hash_label': 'Hash: {}',
        'file_n': 'File {}:',
        'path_label': '  Path: {}',
        'size_label': '  Size: {}',
        'mtime_label': '  Modified: {}',
        'space_saved': 'Total space saveable: {}',
        'group_title': 'Group #{} ({} files, each: {})',
        'group_reclaimable': 'Reclaimable: {}',
        'keep_file': 'Keeping: {}',
        'deleted_file': 'Deleted: {}',
        'recycled_file': 'Sent to Recycle Bin: {}',
        'delete_failed': 'Failed to delete {}: {}',
        'delete_complete': 'Done! Cleaned {} files',
        'space_freed': 'Space freed: {}',
        'scan_cancelled': 'Scan cancelled by user.',
        'scan_error': 'Scan error: {}',
        'file_read_error': 'Cannot read file: {} ({})',
        'file_info_error': 'Cannot get file info: {} ({})',
        'dir_access_error': 'Skipped inaccessible directory: {} ({})',
        'select_folder_dialog': 'Select folder to scan',
        'zero_byte_skipped': 'Skipped {} zero-byte files',
        'symlink_skipped': 'Skipped symlink: {}',
        'status_summary': '{} duplicate groups | {} files checked for deletion (freed: {})',
        'menu_open_file': 'Open File',
        'menu_reveal': 'Show in File Explorer',
        'menu_copy_path': 'Copy Full Path',
        'export_dialog_title': 'Save Duplicate Analysis Report',
        'export_csv_filter': 'CSV Files (*.csv);;Text Files (*.txt)',
        'export_success': 'Report exported successfully to: {}',
        'export_failed': 'Failed to export report: {}',
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


def parse_datetime(dt):
    """确保返回 datetime 对象，支持时间戳数值与 datetime 实例"""
    if isinstance(dt, (int, float)):
        return datetime.fromtimestamp(dt)
    if isinstance(dt, datetime):
        return dt
    return datetime.min


def format_datetime(dt):
    """安全格式化日期时间，兼容 datetime 与数值时间戳"""
    if isinstance(dt, (int, float)):
        dt = datetime.fromtimestamp(dt)
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)


# ─── 工作线程信号类 ──────────────────────────────────────────────
class WorkerSignals(QObject):
    indexing_count = Signal(int)         # 阶段 1：已发现文件数量
    analysis_progress = Signal(int, int) # 阶段 2/3：分析进度 (当前组, 总候选组)
    log_signal = Signal(str)             # 运行日志信号
    error = Signal(str)                  # 异常报错信号
    finished = Signal()                  # 完成信号


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
    PARTIAL_BLOCK_SIZE = 65536     # 64 KB 前缀哈希块大小
    FULL_HASH_BUFFER = 1048576     # 1 MB 全量哈希大块读取缓冲区

    def __init__(self, directory, min_size=0, skip_hidden=True):
        self.directory = directory
        self.min_size = min_size
        self.skip_hidden = skip_hidden
        self.size_groups = defaultdict(list)
        self.file_info_cache = {}
        self.small_file_hashes = {}  # 记录 <= 64KB 文件的完整哈希，避免二次重读
        self.hash_duplicates = defaultdict(list)
        self.total_files = 0
        self.zero_byte_count = 0

    def reset(self):
        """重置所有状态，用于重新扫描"""
        self.size_groups = defaultdict(list)
        self.file_info_cache = {}
        self.small_file_hashes = {}
        self.hash_duplicates = defaultdict(list)
        self.total_files = 0
        self.zero_byte_count = 0

    def calculate_hash(self, file_path, signals=None, partial=False):
        """
        计算文件哈希值。
        partial=True: 只读取前 PARTIAL_BLOCK_SIZE (64KB) 字节（快速预筛）。
        partial=False: 采用 FULL_HASH_BUFFER (1MB) 大块读取完整文件（最终确认）。
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                if partial:
                    data = f.read(self.PARTIAL_BLOCK_SIZE)
                    if data:
                        sha256.update(data)
                else:
                    while True:
                        data = f.read(self.FULL_HASH_BUFFER)
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
        """获取文件信息，带内存缓存"""
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
        """扫描目录，按文件大小分组，带目录异常捕获与过滤"""
        signals.log_signal.emit(tr('scanning_directory', self.directory))

        def handle_walk_error(err):
            signals.log_signal.emit(
                f"<span style='color:orange'>{tr('dir_access_error', getattr(err, 'filename', ''), str(err))}</span>"
            )

        for root, dirs, files in os.walk(self.directory, followlinks=False, onerror=handle_walk_error):
            if is_cancelled():
                return

            # 跳过隐藏或系统保留目录
            if self.skip_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('$')]

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

                    # 检查最小文件大小过滤
                    if file_info['size'] < self.min_size:
                        continue

                    self.size_groups[file_info['size']].append(file_path)
                    self.total_files += 1
                    signals.indexing_count.emit(self.total_files)

        if self.zero_byte_count > 0:
            signals.log_signal.emit(tr('zero_byte_skipped', self.zero_byte_count))

    def find_duplicates(self, signals, is_cancelled):
        """
        分层哈希策略查找重复文件：
        第 1 层：按文件大小初筛（scan_files 已完成）
        第 2 层：同大小文件计算 64KB 快速前缀哈希（<=64KB 文件直接记录为全量哈希）
        第 3 层：对前缀相同的候选文件执行全量哈希确认（复用 <=64KB 结果，避免二次读取）
        """
        signals.log_signal.emit(tr('analyzing_duplicates'))

        candidate_groups = {
            size: files for size, files in self.size_groups.items() if len(files) > 1
        }
        total_groups = len(candidate_groups)
        current_group = 0

        for size, files in candidate_groups.items():
            if is_cancelled():
                return
            current_group += 1

            # 第 2 层：快速哈希（前 64KB）
            partial_hash_groups = defaultdict(list)
            for file_path in files:
                if is_cancelled():
                    return
                partial_hash = self.calculate_hash(file_path, signals=signals, partial=True)
                if partial_hash:
                    partial_hash_groups[partial_hash].append(file_path)
                    # 性能关键优化：如果文件本身 <= 64KB，前缀哈希就是完整哈希
                    if size <= self.PARTIAL_BLOCK_SIZE:
                        self.small_file_hashes[file_path] = partial_hash

            # 第 3 层：仅对前缀相同的候选文件计算全量哈希
            for partial_hash, matching_files in partial_hash_groups.items():
                if len(matching_files) > 1:
                    full_hash_groups = defaultdict(list)
                    for file_path in matching_files:
                        if is_cancelled():
                            return
                        # 若已预计算（<=64KB），直接复用内存哈希，彻底消除二次磁盘 I/O
                        if file_path in self.small_file_hashes:
                            full_hash = self.small_file_hashes[file_path]
                        else:
                            full_hash = self.calculate_hash(file_path, signals=signals, partial=False)

                        if full_hash:
                            full_hash_groups[full_hash].append(file_path)

                    for hash_value, file_list in full_hash_groups.items():
                        if len(file_list) > 1:
                            self.hash_duplicates[hash_value] = [
                                self.get_file_info(f, signals) for f in file_list
                            ]

            signals.analysis_progress.emit(current_group, total_groups)

    def export_to_csv(self, file_path):
        """将重复文件分析结果导出为 UTF-8 BOM CSV 文件（适配 Excel）"""
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Group ID', 'File Index', 'Path', 'Size (Bytes)', 'Formatted Size',
                'Modified Time', 'Created Time', 'SHA-256 Hash'
            ])
            for group_idx, (hash_value, files) in enumerate(self.hash_duplicates.items(), 1):
                valid_files = [f for f in files if f is not None]
                for file_idx, file_info in enumerate(valid_files, 1):
                    writer.writerow([
                        group_idx,
                        file_idx,
                        file_info['path'],
                        file_info['size'],
                        format_size(file_info['size']),
                        format_datetime(file_info['mtime']),
                        format_datetime(file_info['ctime']),
                        hash_value
                    ])


# ─── 主窗口类 ────────────────────────────────────────────────────
class DuplicateFileFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.finder = None
        self.worker = None
        self.is_running = False
        self.is_indexing = True
        self.initUI()
        self.setAcceptDrops(True)

    def initUI(self):
        self.setWindowTitle(tr('window_title'))

        # 设置窗口图标
        icon_path = resource_path('./srch.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 居中显示，尺寸扩大为 960x680
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_width = 960
        window_height = 680
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)
        self.setMinimumSize(800, 560)

        # 现代暗色主题样式
        self.setStyleSheet("""
            QWidget {
                background-color: #252526;
                color: #D4D4D4;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #0E639C;
                border: none;
                color: #FFFFFF;
                padding: 7px 18px;
                font-size: 13px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #0D5280;
            }
            QPushButton:disabled {
                background-color: #3E3E42;
                color: #707070;
            }
            QPushButton#deleteBtn {
                background-color: #D32F2F;
            }
            QPushButton#deleteBtn:hover {
                background-color: #E53935;
            }
            QPushButton#deleteBtn:disabled {
                background-color: #3E3E42;
                color: #707070;
            }
            QPushButton#actionBtn {
                background-color: #3E3E42;
                padding: 5px 12px;
                font-size: 12px;
            }
            QPushButton#actionBtn:hover {
                background-color: #505054;
            }
            QTextEdit, QProgressBar, QComboBox, QTreeWidget {
                background-color: #1E1E1E;
                color: #CCCCCC;
                border: 1px solid #3E3E42;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #2A2D2E;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #2D2D30;
                color: #CCCCCC;
                padding: 5px;
                border: 1px solid #3E3E42;
                font-weight: bold;
            }
            QProgressBar {
                text-align: center;
                border: 1px solid #3E3E42;
                border-radius: 4px;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #0E639C;
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #3E3E42;
                border-radius: 4px;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D30;
                color: #969696;
                padding: 7px 18px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border-top: 2px solid #0E639C;
            }
            QCheckBox {
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ── 1. 文件夹选择行 ──────────────────────────────────────────
        file_layout = QHBoxLayout()
        self.btn_select_dir = QPushButton(tr('select_folder'))
        self.btn_select_dir.setFixedWidth(130)
        self.btn_select_dir.clicked.connect(self.select_directory)
        self.lbl_selected = QLabel(tr('no_directory'))
        self.lbl_selected.setStyleSheet("color: #AAAAAA; padding-left: 6px;")
        file_layout.addWidget(self.btn_select_dir)
        file_layout.addWidget(self.lbl_selected, stretch=1)
        main_layout.addLayout(file_layout)

        # ── 2. 控制项与过滤配置行 ────────────────────────────────────
        ctrl_layout = QHBoxLayout()

        # 留存策略
        self.lbl_strategy = QLabel(tr('delete_strategy'))
        self.combo_keep = QComboBox()
        self.combo_keep.addItems([tr('keep_newest'), tr('keep_oldest')])
        self.combo_keep.currentIndexChanged.connect(self.on_strategy_changed)
        ctrl_layout.addWidget(self.lbl_strategy)
        ctrl_layout.addWidget(self.combo_keep)

        ctrl_layout.addSpacing(15)

        # 最小大小过滤
        self.lbl_min_size = QLabel(tr('filter_min_size'))
        self.combo_min_size = QComboBox()
        self.combo_min_size.addItems([
            tr('filter_size_all'),
            tr('filter_size_10k'),
            tr('filter_size_100k'),
            tr('filter_size_1m'),
            tr('filter_size_10m'),
        ])
        ctrl_layout.addWidget(self.lbl_min_size)
        ctrl_layout.addWidget(self.combo_min_size)

        ctrl_layout.addSpacing(15)

        # 忽略隐藏目录
        self.chk_skip_hidden = QCheckBox(tr('filter_skip_hidden'))
        self.chk_skip_hidden.setChecked(True)
        ctrl_layout.addWidget(self.chk_skip_hidden)

        ctrl_layout.addStretch()

        # 语言切换
        self.lbl_language = QLabel(tr('language') + ': ')
        self.combo_language = QComboBox()
        self.combo_language.addItems(['简体中文', 'English'])
        self.combo_language.setFixedWidth(100)
        self.combo_language.currentIndexChanged.connect(self.change_language)
        ctrl_layout.addWidget(self.lbl_language)
        ctrl_layout.addWidget(self.combo_language)

        main_layout.addLayout(ctrl_layout)

        # ── 3. 两阶段进度条 ──────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setFormat(tr('indexing_progress_fmt', 0))
        self.progress.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.progress)

        # ── 4. 中心标签页（重复列表 + 运行日志） ────────────────────
        self.tabs = QTabWidget()

        # Tab 1: 重复文件树形列表
        tree_widget_container = QWidget()
        tree_layout = QVBoxLayout(tree_widget_container)
        tree_layout.setContentsMargins(6, 6, 6, 6)
        tree_layout.setSpacing(6)

        # 快捷勾选工具条
        tree_tools_layout = QHBoxLayout()
        self.btn_select_all = QPushButton(tr('btn_select_all'))
        self.btn_select_all.setObjectName("actionBtn")
        self.btn_select_all.clicked.connect(self.select_all_deletable)

        self.btn_deselect_all = QPushButton(tr('btn_deselect_all'))
        self.btn_deselect_all.setObjectName("actionBtn")
        self.btn_deselect_all.clicked.connect(self.deselect_all)

        self.btn_export = QPushButton(tr('btn_export'))
        self.btn_export.setObjectName("actionBtn")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)

        tree_tools_layout.addWidget(self.btn_select_all)
        tree_tools_layout.addWidget(self.btn_deselect_all)
        tree_tools_layout.addWidget(self.btn_export)
        tree_tools_layout.addStretch()

        # 统计提示标签
        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet("color: #4EC9B0; font-weight: bold;")
        tree_tools_layout.addWidget(self.lbl_summary)

        tree_layout.addLayout(tree_tools_layout)

        # 树形视图
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            tr('tree_header_file'),
            tr('tree_header_size'),
            tr('tree_header_mtime'),
            tr('tree_header_path'),
        ])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.itemChanged.connect(self.on_tree_item_changed)
        tree_layout.addWidget(self.tree)

        self.tabs.addTab(tree_widget_container, tr('tab_duplicates'))

        # Tab 2: 日志文本框
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.tabs.addTab(self.log, tr('tab_log'))

        main_layout.addWidget(self.tabs, stretch=1)

        # ── 5. 底部操作按钮 ──────────────────────────────────────────
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton(tr('start_scan'))
        self.btn_start.setMinimumHeight(38)
        self.btn_start.clicked.connect(self.toggle_scan)

        self.btn_delete = QPushButton(tr('delete_duplicates'))
        self.btn_delete.setObjectName("deleteBtn")
        self.btn_delete.setMinimumHeight(38)
        self.btn_delete.clicked.connect(self.delete_duplicates)
        self.btn_delete.setEnabled(False)

        btn_layout.addWidget(self.btn_start, stretch=1)
        btn_layout.addWidget(self.btn_delete, stretch=1)
        main_layout.addLayout(btn_layout)

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
        cur_keep = self.combo_keep.currentIndex()
        self.combo_keep.blockSignals(True)
        self.combo_keep.clear()
        self.combo_keep.addItems([tr('keep_newest'), tr('keep_oldest')])
        self.combo_keep.setCurrentIndex(cur_keep)
        self.combo_keep.blockSignals(False)

        self.lbl_min_size.setText(tr('filter_min_size'))
        cur_min = self.combo_min_size.currentIndex()
        self.combo_min_size.blockSignals(True)
        self.combo_min_size.clear()
        self.combo_min_size.addItems([
            tr('filter_size_all'),
            tr('filter_size_10k'),
            tr('filter_size_100k'),
            tr('filter_size_1m'),
            tr('filter_size_10m'),
        ])
        self.combo_min_size.setCurrentIndex(cur_min)
        self.combo_min_size.blockSignals(False)

        self.chk_skip_hidden.setText(tr('filter_skip_hidden'))
        self.lbl_language.setText(tr('language') + ': ')

        self.tabs.setTabText(0, tr('tab_duplicates'))
        self.tabs.setTabText(1, tr('tab_log'))

        self.btn_select_all.setText(tr('btn_select_all'))
        self.btn_deselect_all.setText(tr('btn_deselect_all'))
        self.btn_export.setText(tr('btn_export'))

        self.tree.setHeaderLabels([
            tr('tree_header_file'),
            tr('tree_header_size'),
            tr('tree_header_mtime'),
            tr('tree_header_path'),
        ])

        if self.is_running:
            self.btn_start.setText(tr('cancel_scan'))
        else:
            self.btn_start.setText(tr('start_scan'))

        self.update_checked_stats()

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
                self.set_active_directory(dir_path)
                event.acceptProposedAction()
                return
        event.ignore()

    # ── 目录选择 ─────────────────────────────────────────────────
    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, tr('select_folder_dialog'))
        if dir_path:
            self.set_active_directory(dir_path)

    def set_active_directory(self, dir_path):
        self.finder = DuplicateFileFinder(dir_path)
        self.lbl_selected.setText(tr('selected_directory', dir_path))
        self.btn_start.setEnabled(True)
        self.btn_delete.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.tree.clear()
        self.log.clear()
        self.lbl_summary.setText("")
        self.progress.setValue(0)
        self.progress.setFormat(tr('indexing_progress_fmt', 0))

    # ── 扫描控制 ─────────────────────────────────────────────────
    def get_min_size_bytes(self):
        """根据下拉框计算最小字节数"""
        idx = self.combo_min_size.currentIndex()
        mapping = {0: 0, 1: 10 * 1024, 2: 100 * 1024, 3: 1024 * 1024, 4: 10 * 1024 * 1024}
        return mapping.get(idx, 0)

    def toggle_scan(self):
        """切换扫描/取消状态"""
        if self.is_running:
            self.cancel_scan()
        else:
            self.start_scan()

    def start_scan(self):
        if not self.finder:
            self.log.append(f"<span style='color:red'>{tr('error_no_directory')}</span>")
            self.tabs.setCurrentIndex(1)
            return

        # 配置参数并重置
        self.finder.min_size = self.get_min_size_bytes()
        self.finder.skip_hidden = self.chk_skip_hidden.isChecked()
        self.finder.reset()

        self.is_running = True
        self.is_indexing = True
        self.btn_start.setText(tr('cancel_scan'))
        self.btn_delete.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.tree.clear()
        self.lbl_summary.setText("")

        # 进度条重置为阶段 1 跑马灯
        self.progress.setRange(0, 0)
        self.progress.setFormat(tr('indexing_progress_fmt', 0))

        self.signals = WorkerSignals()
        self.signals.indexing_count.connect(self.update_indexing_progress)
        self.signals.analysis_progress.connect(self.update_analysis_progress)
        self.signals.log_signal.connect(self.append_log)
        self.signals.error.connect(self.scan_error)
        self.signals.finished.connect(self.scan_finished)

        self.worker = DuplicateFinderWorker(self.finder, self.signals)
        self.worker.start()

    def cancel_scan(self):
        """请求取消当前扫描"""
        if self.worker:
            self.worker.cancel()

    # ── 进度更新 ─────────────────────────────────────────────────
    def update_indexing_progress(self, count):
        if self.is_indexing:
            self.progress.setFormat(tr('indexing_progress_fmt', count))

    def update_analysis_progress(self, current, total):
        if self.is_indexing:
            self.is_indexing = False
            self.progress.setRange(0, total)
            self.progress.setFormat(tr('analysis_progress_fmt'))
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    # ── 日志与错误 ───────────────────────────────────────────────
    def append_log(self, message):
        self.log.append(message)

    def scan_error(self, error_msg):
        self.log.append(f"<span style='color:red'>{tr('scan_error', error_msg)}</span>")

    # ── 扫描完成与构建树 ─────────────────────────────────────────
    def scan_finished(self):
        self.is_running = False
        self.btn_start.setText(tr('start_scan'))
        self.btn_start.setEnabled(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)

        if self.finder and self.finder.hash_duplicates:
            self.populate_tree()
            self.btn_export.setEnabled(True)
            self.tabs.setCurrentIndex(0)  # 自动切到列表页
        else:
            self.tree.clear()
            self.lbl_summary.setText(tr('no_duplicates_found'))
            self.btn_export.setEnabled(False)

    def populate_tree(self):
        """将重复文件数据加载到 QTreeWidget"""
        self.tree.blockSignals(True)
        self.tree.clear()

        keep_rule = 'newest' if self.combo_keep.currentIndex() == 0 else 'oldest'

        for group_idx, (hash_value, files) in enumerate(self.finder.hash_duplicates.items(), 1):
            valid_files = [f for f in files if f is not None]
            if len(valid_files) <= 1:
                continue

            # 按修改时间排序（降序为 newest 优先）
            sorted_files = sorted(valid_files, key=lambda x: parse_datetime(x.get('mtime')), reverse=(keep_rule == 'newest'))
            group_size = sorted_files[0]['size']
            reclaimable_size = group_size * (len(sorted_files) - 1)

            # 父节点：重复组
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, tr('group_title', group_idx, len(sorted_files), format_size(group_size)))
            group_item.setText(1, tr('group_reclaimable', format_size(reclaimable_size)))
            group_item.setFlags(Qt.ItemIsEnabled)

            # 子节点：具体文件
            for idx, file_info in enumerate(sorted_files):
                child_item = QTreeWidgetItem(group_item)
                child_item.setText(0, os.path.basename(file_info['path']))
                child_item.setText(1, format_size(file_info['size']))
                child_item.setText(2, format_datetime(file_info['mtime']))
                child_item.setText(3, file_info['path'])
                child_item.setData(0, Qt.UserRole, file_info)

                # 第一项保留，其余项默认勾选待删除
                child_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                if idx == 0:
                    child_item.setCheckState(0, Qt.Unchecked)
                else:
                    child_item.setCheckState(0, Qt.Checked)

            group_item.setExpanded(True)

        self.tree.blockSignals(False)
        self.update_checked_stats()

    # ── 树形交互与策略同步 ───────────────────────────────────────
    def on_tree_item_changed(self, item, column):
        """文件勾选状态改变时重新计算统计与按钮状态"""
        if column == 0:
            self.update_checked_stats()

    def update_checked_stats(self):
        """统计当前勾选的文件数量与释放容量"""
        checked_count = 0
        freed_bytes = 0

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group = root.child(i)
            for j in range(group.childCount()):
                child = group.child(j)
                if child.checkState(0) == Qt.Checked:
                    checked_count += 1
                    file_info = child.data(0, Qt.UserRole)
                    if file_info:
                        freed_bytes += file_info['size']

        total_groups = root.childCount()
        if total_groups > 0:
            self.lbl_summary.setText(
                tr('status_summary', total_groups, checked_count, format_size(freed_bytes))
            )
            self.btn_delete.setText(tr('delete_duplicates_count', checked_count))
            self.btn_delete.setEnabled(checked_count > 0)
        else:
            self.lbl_summary.setText("")
            self.btn_delete.setText(tr('delete_duplicates'))
            self.btn_delete.setEnabled(False)

    def on_strategy_changed(self):
        """留存策略切换时，重新智能自动勾选"""
        if self.tree.topLevelItemCount() == 0:
            return
        self.select_all_deletable()

    def select_all_deletable(self):
        """根据当前策略重新勾选每组的所有待清理副本"""
        self.tree.blockSignals(True)
        keep_rule = 'newest' if self.combo_keep.currentIndex() == 0 else 'oldest'

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group = root.child(i)
            children = group.takeChildren()
            # 获取各子项文件信息并重新排序
            children.sort(
                key=lambda x: parse_datetime(x.data(0, Qt.UserRole).get('mtime')) if x.data(0, Qt.UserRole) else datetime.min,
                reverse=(keep_rule == 'newest')
            )
            for idx, child in enumerate(children):
                child.setCheckState(0, Qt.Unchecked if idx == 0 else Qt.Checked)
            group.addChildren(children)

        self.tree.blockSignals(False)
        self.update_checked_stats()

    def deselect_all(self):
        """取消勾选全部文件"""
        self.tree.blockSignals(True)
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group = root.child(i)
            for j in range(group.childCount()):
                group.child(j).setCheckState(0, Qt.Unchecked)
        self.tree.blockSignals(False)
        self.update_checked_stats()

    # ── 双击与右键菜单 ───────────────────────────────────────────
    def on_item_double_clicked(self, item, column):
        """双击具体文件直接调用默认应用打开"""
        file_info = item.data(0, Qt.UserRole)
        if file_info and 'path' in file_info:
            open_file_with_default_app(file_info['path'])

    def show_context_menu(self, pos):
        """显示右键快捷操作菜单"""
        item = self.tree.itemAt(pos)
        if not item:
            return
        file_info = item.data(0, Qt.UserRole)
        if not file_info or 'path' not in file_info:
            return

        file_path = file_info['path']
        menu = QMenu(self)

        action_open = QAction(tr('menu_open_file'), self)
        action_open.triggered.connect(lambda: open_file_with_default_app(file_path))
        menu.addAction(action_open)

        action_reveal = QAction(tr('menu_reveal'), self)
        action_reveal.triggered.connect(lambda: reveal_in_file_manager(file_path))
        menu.addAction(action_reveal)

        action_copy = QAction(tr('menu_copy_path'), self)
        action_copy.triggered.connect(lambda: QApplication.clipboard().setText(file_path))
        menu.addAction(action_copy)

        menu.exec(QCursor.pos())

    # ── 导出报告 ─────────────────────────────────────────────────
    def export_report(self):
        """将重复文件分析结果导出为 CSV"""
        if not self.finder or not self.finder.hash_duplicates:
            return

        default_name = f"Deduply_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self, tr('export_dialog_title'), default_name, tr('export_csv_filter')
        )
        if file_path:
            try:
                self.finder.export_to_csv(file_path)
                QMessageBox.information(self, tr('window_title'), tr('export_success', file_path))
                self.log.append(f"<span style='color:lightgreen'>{tr('export_success', file_path)}</span>")
            except Exception as e:
                QMessageBox.warning(self, tr('window_title'), tr('export_failed', str(e)))
                self.log.append(f"<span style='color:red'>{tr('export_failed', str(e))}</span>")

    # ── 删除操作 ─────────────────────────────────────────────────
    def delete_duplicates(self):
        """删除树中当前勾选的文件"""
        # 搜集所有已勾选的文件项
        checked_items = []
        root = self.tree.invisibleRootItem()
        freed_space = 0

        for i in range(root.childCount()):
            group = root.child(i)
            for j in range(group.childCount()):
                child = group.child(j)
                if child.checkState(0) == Qt.Checked:
                    checked_items.append(child)
                    info = child.data(0, Qt.UserRole)
                    if info:
                        freed_space += info['size']

        if not checked_items:
            QMessageBox.information(self, tr('confirm_delete_title'), tr('no_items_checked'))
            return

        msg = tr('confirm_delete_msg', len(checked_items), format_size(freed_space)) if HAS_SEND2TRASH \
            else tr('confirm_delete_msg_permanent', len(checked_items), format_size(freed_space))

        reply = QMessageBox.question(
            self, tr('confirm_delete_title'), msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        deleted_count = 0
        actual_freed = 0
        items_to_remove = []

        for item in checked_items:
            info = item.data(0, Qt.UserRole)
            if not info or 'path' not in info:
                continue
            path = info['path']
            try:
                if HAS_SEND2TRASH:
                    _send2trash(path)
                    self.log.append(f"{tr('recycled_file', path)}")
                else:
                    os.remove(path)
                    self.log.append(f"{tr('deleted_file', path)}")
                deleted_count += 1
                actual_freed += info['size']
                items_to_remove.append(item)
            except Exception as e:
                self.log.append(
                    f"<span style='color:red'>{tr('delete_failed', path, str(e))}</span>"
                )

        # 从树中动态移除已删除的项
        self.tree.blockSignals(True)
        for item in items_to_remove:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
                # 若组内仅剩 1 个或 0 个文件，已无重复意义，直接移除该组
                if parent.childCount() <= 1:
                    root.removeChild(parent)
        self.tree.blockSignals(False)

        self.update_checked_stats()
        summary_msg = f"{tr('delete_complete', deleted_count)} ({tr('space_freed', format_size(actual_freed))})"
        self.log.append(f"<b><span style='color:lightgreen'>{summary_msg}</span></b>")
        QMessageBox.information(self, tr('confirm_delete_title'), summary_msg)


# ─── 程序入口 ────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 10))
    window = DuplicateFileFinderApp()
    window.show()
    sys.exit(app.exec())