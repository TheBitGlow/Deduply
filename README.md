# Deduply

**Deduply** 是一款基于 PySide6 的桌面应用，用于快速查找并清理重复文件。

**Deduply** is a PySide6-based desktop app for finding and cleaning duplicate files.

---

## ✨ 功能特性 / Features

- 🔍 **分层哈希检测 / Layered Hash Detection** — 文件大小分组 → 前 64KB 快速哈希 → 全量哈希确认，大文件场景性能提升 10-100 倍  
  File size grouping → partial hash (first 64KB) → full hash verification, 10-100x faster on large files
- 🗑️ **安全删除 / Safe Deletion** — 通过 `send2trash` 将文件移入回收站，而非永久删除  
  Sends files to Recycle Bin via `send2trash` instead of permanent deletion
- 📂 **拖放支持 / Drag & Drop** — 直接拖入文件夹开始扫描  
  Drag and drop folders directly to start scanning
- 🌐 **中英双语 / Bilingual UI** — 界面支持中文/英文实时切换  
  Switch between Chinese and English on the fly
- ⏹️ **取消扫描 / Cancel Scan** — 随时中止进行中的扫描任务  
  Stop an in-progress scan at any time
- 📊 **智能策略 / Smart Strategy** — 可选保留最新或最旧文件  
  Choose to keep the newest or oldest file
- 🎨 **深色主题 / Dark Theme** — 护眼深色界面  
  Eye-friendly dark interface
- 🛡️ **健壮处理 / Robust Handling** — 自动跳过零字节文件和符号链接，异常文件记录日志  
  Auto-skips zero-byte files and symlinks, logs inaccessible files

---

## 📦 安装 / Installation

```bash
# 安装依赖 / Install dependencies
pip install PySide6 send2trash

# 或使用 requirements.txt / Or use requirements.txt
pip install -r requirements.txt
```

## 🚀 使用 / Usage

```bash
python Deduply.py
```

1. 点击「选择文件夹」或直接拖入文件夹 / Click "Select Folder" or drag-and-drop a folder
2. 选择删除策略（保留最新/最旧）/ Choose strategy (Keep Newest / Keep Oldest)
3. 点击「开始扫描」/ Click "Start Scan"
4. 查看报告，确认后点击「删除重复文件」/ Review report, then click "Delete Duplicates"

---

## 🛠️ 技术栈 / Tech Stack

| 组件 / Component | 技术 / Technology |
|---|---|
| GUI 框架 | PySide6 (Qt for Python) |
| 哈希算法 | SHA-256 |
| 安全删除 | send2trash |
| 语言 | Python 3.8+ |

## 📄 License

[MIT](LICENSE)
