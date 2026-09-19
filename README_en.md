<div align="center">

<img src="./srch.ico" width="80" height="80" alt="Deduply Logo" />

# Deduply

**A lightweight, blazing-fast, and safe desktop duplicate file cleaner.**

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52.svg)](https://wiki.qt.io/Qt_for_Python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

[简体中文](README.md) · **English**

</div>

---

## 📌 Table of Contents

- [💡 Why Deduply?](#-why-deduply)
- [⚙️ How It Works: Progressive 3-Tier Hashing](#️-how-it-works-progressive-3-tier-hashing)
- [✨ Key Features](#-key-features)
- [📦 Installation](#-installation)
- [🚀 Quick Start](#-quick-start)
- [🛠️ Standalone Executable Packaging (PyInstaller)](#️-standalone-executable-packaging-pyinstaller)
- [🧩 Tech Stack & Architecture](#-tech-stack--architecture)
- [❓ Frequently Asked Questions (FAQ)](#-frequently-asked-questions-faq)
- [📄 License](#-license)

---

## 💡 Why Deduply?

Disk bloat caused by redundant media files, scattered downloads, and repeated folder backups is a common headache. Most traditional duplicate finders have two major flaws:
1. **Sluggish Performance & High I/O Overhead**: They calculate full cryptographic hashes across every single file. When dealing with tens of gigabytes of videos or archives, disk I/O thrashes and scans drag on painfully.
2. **High Risk of Data Loss**: Many tools permanently erase duplicates on disk, meaning a single misclick can cause irreversible data disasters.

**Deduply** was built from the ground up to solve both problems:
- 🚀 **10x to 100x Speedup**: A progressive pipeline (*Size Partitioning → 64KB Prefix Hash → Full SHA-256 Verification*) eliminates over 99% of pointless full-file disk reads.
- 🛡️ **Recycle Bin Safeguard**: Powered by `send2trash`, redundant files are safely routed to the OS Recycle Bin / Trash rather than permanently wiped, giving you total peace of mind.
- 🎨 **Sleek & Responsive Desktop UX**: Asynchronous multithreading keeps the UI 100% fluid even when traversing deep hierarchies with millions of files. Includes dark theme, folder drag-and-drop, and on-the-fly bilingual switching.

---

## ⚙️ How It Works: Progressive 3-Tier Hashing

Deduply divides duplicate identification into three progressive stages, filtering out non-duplicate candidates at each step to minimize disk read operations:

```
                      [ All Files to Scan ]
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────┐
 │ Tier 1: File Size Grouping                               │
 │ • Reads filesystem metadata only (Zero file-read I/O)     │
 │ • Immediately discards files with unique sizes           │
 └───────────────────────────┬──────────────────────────────┘
                             ▼ (Only for files with identical sizes)
 ┌──────────────────────────────────────────────────────────┐
 │ Tier 2: 64KB Prefix Hash (Partial SHA-256)               │
 │ • Reads only the first 64KB of candidate files           │
 │ • Rapidly discards 95%+ of false-positive size matches    │
 └───────────────────────────┬──────────────────────────────┘
                             ▼ (Only for files with matching prefixes)
 ┌──────────────────────────────────────────────────────────┐
 │ Tier 3: Full SHA-256 Cryptographic Verification          │
 │ • Reads full content to compute the final digest         │
 │ • Guarantees 100% cryptographic collision resistance     │
 └───────────────────────────┬──────────────────────────────┘
                             ▼
                 [ 🎯 Confirmed Duplicates ]
```

### Traditional Tools vs Deduply Performance

| Scenario | Traditional Full-Hash Tools | Deduply 3-Tier Engine | Performance Gain |
| :--- | :--- | :--- | :--- |
| **Large files with unique sizes** | Reads every byte from disk | Inspects metadata only (**0 file I/O**) | **Near-instantaneous (100x+)** |
| **Files sharing size but different content** | Reads 100% of all matching files | Reads first 64KB and immediately skips | **10x to 50x faster** |
| **Genuine duplicates** | Computes full hashes | Filters first, then verifies candidates | **100% precision with minimal I/O** |

---

## ✨ Key Features

- 🔍 **Progressive Hashing**: Size grouping + 64KB prefix pre-screening + full SHA-256 check, delivering unmatched efficiency for multimedia and large files.
- 🗑️ **Safe Recycle Bin Deletion**: Soft-deletes redundant copies to the system trash via `send2trash`, enabling safe inspection and recovery anytime.
- 📂 **Native Drag & Drop**: Simply drag and drop any folder straight into the application window to initialize scanning.
- 🌐 **Real-time Bilingual UI**: Switch between English and Simplified Chinese instantly from the top bar without needing to restart.
- ⏱️ **Smart Retention Policies**: Automatically sorts duplicate groups by file modification time—choose **"Keep Newest"** or **"Keep Oldest"** in one click.
- 🧵 **Asynchronous & Non-blocking**: Workflows run decoupled from the UI thread (`QThread` + `WorkerSignals`), providing responsive progress bars and one-click scan cancellation.
- 🎨 **Modern Dark Theme**: Ergonomic dark aesthetic featuring dual-stage progress feedback (file indexing vs duplicate analysis) and reclaimable space stats.
- 🛡️ **Robust Edge Case Handling**: Automatically ignores 0-byte empty files and symbolic links (`followlinks=False`), reporting inaccessible files gracefully without crashing.

---

## 📦 Installation

### Prerequisites
- **Python** 3.8 or higher
- Supported on Windows, macOS, and major Linux desktop environments

### Steps

1. **Clone or download the repository**:
   ```bash
   git clone https://github.com/TheBitGlow/Deduply.git
   cd Deduply
   ```

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Or install manually:*
   ```bash
   pip install PySide6>=6.5.0 send2trash>=1.8.0
   ```

---

## 🚀 Quick Start

1. **Launch the application**:
   ```bash
   python Deduply.py
   ```

2. **Standard Workflow**:
   1. **Select Directory**: Click **"Select Folder"** or simply **drag & drop** a directory into the window.
   2. **Set Policy**: Choose your preferred retention strategy (`Keep Newest` or `Keep Oldest`) from the dropdown.
   3. **Start Scan**: Click **"Start Scan"**. The dual-phase progress bar tracks indexing and hashing.
   4. **Inspect Report**: Review duplicate groups, file paths, timestamps, and total reclaimable space.
   5. **Clean Safely**: Click **"Delete Duplicates"**, confirm the prompt, and redundant copies will be safely sent to the Recycle Bin.

---

## 🛠️ Standalone Executable Packaging (PyInstaller)

Deduply includes built-in frozen resource path resolution (`resource_path`), making it seamless to package into a standalone single executable (`.exe` on Windows):

```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Package into a single executable without console window
pyinstaller --noconsole --onefile --icon=srch.ico --add-data "srch.ico;." Deduply.py
```

The resulting `Deduply.exe` will be located inside the `dist/` folder, completely self-contained and ready to run.

---

## 🧩 Tech Stack & Architecture

### Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **GUI Framework** | [PySide6](https://wiki.qt.io/Qt_for_Python) | Modern Qt6 Python bindings providing native performance, event loops, and widgets |
| **Hashing Engine** | Python `hashlib` (SHA-256) | Balanced computational efficiency with cryptographic anti-collision security |
| **Safe Deletion** | [Send2Trash](https://github.com/arsenetar/send2trash) | Cross-platform native Recycle Bin / Trash API (Windows, macOS, Linux FreeDesktop) |
| **Filesystem Access** | Python standard `os` / `stat` | Directory traversal, metadata caching, and timestamp parsing |

### Class Architecture

- `DuplicateFileFinder`: The core detection engine implementing 3-tier filtering, stats caching, and report generation.
- `DuplicateFinderWorker`: `QThread`-based worker executing background scans and emitting thread-safe Qt signals.
- `DuplicateFileFinderApp`: The primary `QMainWindow` handling UI layout, drag & drop events, dynamic localization, and user interactions.

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>Q1: Can I recover files after deleting duplicates?</b></summary>
Yes. Deduply sends redundant files directly to your operating system's Recycle Bin / Trash via <code>send2trash</code>. You can easily inspect and restore them at any time.
</details>

<details>
<summary><b>Q2: Why weren't two files of the exact same size flagged as duplicates?</b></summary>
Deduply relies on cryptographic content verification. If two files differ by even a single byte, their 64KB prefix or full SHA-256 hashes will be entirely distinct. Deduply will never falsely flag files based solely on matching sizes or names.
</details>

<details>
<summary><b>Q3: Will it delete symbolic links or system shortcuts?</b></summary>
No. Deduply explicitly ignores symbolic links (<code>followlinks=False</code> and checks <code>islink</code>) and skips 0-byte empty files. However, scanning sensitive system directories (like <code>C:\Windows</code>) is still discouraged.
</details>

<details>
<summary><b>Q4: What happens if I want to stop an ongoing scan?</b></summary>
You can click "Cancel" at any time. Because tasks run asynchronously inside a dedicated <code>QThread</code>, the UI remains fully responsive and terminates the search safely.
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). Contributions, issues, and feature requests are welcome!
