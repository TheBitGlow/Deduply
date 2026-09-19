# Deduply

> **Deduply** 是一款轻量、高效且安全的开源桌面端重复文件清理工具。基于 PySide6 (Qt for Python) 构建，采用创新的「分层渐进式哈希校验」算法，秒级定位冗余文件；内置系统回收站安全防护，让磁盘清理既飞速又安心。
>
> **Deduply** is a fast, safe, and modern open-source desktop duplicate file cleaner built with PySide6. Powered by an innovative progressive 3-tier hash engine, it pinpoints redundant files in seconds while safeguarding your data with Recycle Bin deletion.

---

## 📖 项目简介 / Introduction

### 🇨🇳 中文
**Deduply** 致力于解决日常使用与数据备份中常见的存储膨胀与文件冗余痛点。传统查重工具要么全盘读取耗时漫长，要么直接永久销毁文件存在误删风险。Deduply 围绕 **极致性能** 与 **数据安全** 进行了全新设计：

- **分层渐进式哈希引擎**：通过「文件大小初筛 → 64KB 快速前缀哈希 → 全量 SHA-256 校验」三层递进过滤，无需对所有文件做全量读取，大文件与多媒体场景下提速 **10~100 倍**。
- **安全防误删保障**：集成 `send2trash` 安全组件，重复文件默认移入系统回收站而非直接物理抹除，保留恢复余地。
- **现代桌面交互**：多线程异步处理杜绝界面卡顿，支持文件夹拖放、中英文界面实时无缝切换，以及基于修改时间的智能保留策略（保留最新/最旧）。

### 🇬🇧 English
**Deduply** is designed to tackle disk bloat caused by redundant downloads, multiple backups, and duplicated media files. Traditional duplicate detectors often suffer from sluggish full-disk reads or hazardous permanent deletion. Deduply re-engineers the workflow with a focus on **speed** and **data integrity**:

- **Progressive 3-Tier Hash Engine**: Employs a three-stage pipeline (*file size grouping → 64KB prefix hash → full SHA-256 verification*). Only true duplicate candidates undergo full cryptographic hashing, delivering **10x to 100x speedups** on large files.
- **Recycle Bin Safeguard**: Integrates `send2trash` to send cleaned duplicates directly to your operating system's Recycle Bin / Trash rather than irreversibly wiping them.
- **Modern Desktop Experience**: Asynchronous multithreading (`QThread`) prevents UI freezing, with native drag-and-drop folder support, live Chinese/English UI switching, and smart retention rules (Keep Newest / Keep Oldest).

---

## ⚙️ 工作原理 / How It Works

```
[ 所有文件 / All Files ]
         │
         ▼
[ 第 1 层 / Tier 1 ]  文件大小分组 (File Size Grouping)
         │           └─ 过滤掉绝大多数独一无二大小的文件（零 I/O 消耗）
         ▼
[ 第 2 层 / Tier 2 ]  64KB 快速前缀哈希 (Partial Hash)
         │           └─ 仅读取前 64KB 数据，低 I/O 快速剔除 95%+ 的假性重合
         ▼
[ 第 3 层 / Tier 3 ]  全量 SHA-256 确认 (Full Hash Verification)
         │           └─ 仅对前缀相同的疑似候选文件执行全量校验，保证 100% 准确
         ▼
[ 🎯 命中重复文件 / Duplicates Confirmed ]
```

---

## ✨ 功能特性 / Features

- 🔍 **分层哈希检测 / Layered Hash Detection** — 文件大小分组 → 前 64KB 快速哈希 → 全量哈希确认，大文件场景性能提升 10-100 倍  
  File size grouping → partial hash (first 64KB) → full hash verification, 10-100x faster on large files
- 🗑️ **安全删除 / Safe Deletion** — 通过 `send2trash` 将文件移入回收站，而非永久删除  
  Sends files to Recycle Bin via `send2trash` instead of permanent deletion
- 📂 **拖放支持 / Drag & Drop** — 直接拖入文件夹开始扫描  
  Drag and drop folders directly to start scanning
- 🌐 **中英双语 / Bilingual UI** — 界面支持中文/英文实时切换，无需重启  
  Switch between Chinese and English on the fly without restart
- ⏹️ **取消扫描 / Cancel Scan** — 随时中止进行中的扫描任务  
  Stop an in-progress scan at any time
- 📊 **智能策略 / Smart Strategy** — 可选保留最新或最旧文件（按修改时间排序）  
  Choose to keep the newest or oldest file based on modification time
- 🎨 **深色主题 / Dark Theme** — 护眼深色界面与双阶段独立进度指示  
  Eye-friendly dark interface with dual-stage progress tracking
- 🛡️ **健壮处理 / Robust Handling** — 自动跳过零字节文件和符号链接，异常文件记录日志并展示节省空间统计  
  Auto-skips zero-byte files and symlinks, logs inaccessible files with reclaimable space stats

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

| 组件 / Component | 技术 / Technology | 说明 / Note |
|---|---|---|
| GUI 框架 | PySide6 (Qt for Python) | 原生跨平台桌面 GUI / Multi-threaded desktop UI |
| 哈希算法 | SHA-256 | 兼顾安全性与防碰撞性 / Cryptographic integrity |
| 安全删除 | send2trash | 跨平台回收站支持 / Native Recycle Bin integration |
| 编程语言 | Python 3.8+ | 跨平台运行 / Cross-platform support |

---

## 📄 License

[MIT](LICENSE)

