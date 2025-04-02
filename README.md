# **Cons0leweb Utils - User Manual**  

**Version:** 2.0  
**Last Updated:** 2 April 2025

---

## **📌 Table of Contents**  
1. [Introduction](#-introduction)  
2. [Installation](#-installation)  
3. [User Interface Overview](#-user-interface-overview)  
4. [Features & Usage](#-features--usage)  
   - [Text Processing](#1-text-processing)  
   - [File Operations](#2-file-operations)  
   - [Batch Rename](#3-batch-rename)  
   - [Checksum Verification](#4-checksum-verification)  
   - [Log Viewer](#5-log-viewer)  
5. [Troubleshooting](#-troubleshooting)  
6. [FAQs](#-faqs)  

---

## **🌟 Introduction**  
**Cons0leweb Utils Pro** is a powerful file management tool that allows you to:  
✅ **Add text** to multiple files at once (start, end, or random position)  
✅ **Create & restore backups** before making changes  
✅ **Batch rename** files using customizable patterns  
✅ **Generate checksums** (MD5, SHA1, SHA256, SHA512)  
✅ **Create dummy files** for testing  
✅ **Find & delete duplicates**  
✅ **View logs** for all operations  

---

## **📥 Installation**  
### **Requirements**  
- **Python 3.8+**  
- **Tkinter** (usually included with Python)  

### **Steps**  
1. **Download the script** (`main.py`)  
2. **Run it** using:  
   ```bash
   python main.py
   ```
3. **No admin rights needed** – runs as a portable app!  

---

## **🖥️ User Interface Overview**  
The app has **5 main tabs**:  

| Tab | Description |
|-----|------------|
| **Text Processing** | Add text to files in bulk |
| **File Operations** | Create dummy files, delete empty files, find duplicates |
| **Batch Rename** | Rename files using patterns (`{n}`, `{d}`, `{r}`) |
| **Checksum** | Calculate file hashes (MD5, SHA1, etc.) |
| **Log Viewer** | View all operations in real-time |

---

## **🚀 Features & Usage**  

### **1️⃣ Text Processing**  
**Add custom text to multiple files at once.**  

#### **Steps:**  
1. **Select a folder** (click "Browse")  
2. **Enter text** to insert  
3. **Choose position**:  
   - **Start** (beginning of file)  
   - **End** (appended to file)  
   - **Random** (inserted at random line)  
4. **File extensions** (comma-separated, e.g., `.txt, .html`)  
5. **Max file size** (in MB, default: 10MB)  
6. **Options**:  
   - ☑️ **Include subfolders** (recursive)  
   - ☑️ **Create backups** (`.bak.cu` files)  
7. **Click "Process Files"**  

📌 **Example:**  
- Add `<!-- Copyright 2025  -->` to the **start** of all `.html` files.  

---

### **2️⃣ File Operations**  
**Create dummy files, delete empty files, find duplicates.**  

#### **A) Create Dummy Files**  
- **Folder**: Where files will be created  
- **Number of files**: How many to generate  
- **Extension**: `.txt`, `.log`, etc.  
- **Naming**:  
  - **Random** (e.g., `xYzqW123.txt`)  
  - **Sequential** (e.g., `dummy_1.txt`, `dummy_2.txt`)  

#### **B) Delete Empty Files**  
- Scans folder and removes 0-byte files.  

#### **C) Find Duplicates**  
- Compares files by **content** (checksum) and lists duplicates.  

---

### **3️⃣ Batch Rename**  
**Rename files using patterns.**  

#### **Pattern Placeholders:**  
| Placeholder | Meaning |
|-------------|---------|
| `{n}` | Original filename |
| `{d}` | Current date (YYYYMMDD) |
| `{t}` | Current time (HHMMSS) |
| `{r}` | Random 4-letter string |

📌 **Example:**  
- **Pattern:** `{n}_{d}_{r}`  
- **Result:** `document_20231115_AbCd.txt`  

#### **Steps:**  
1. **Select folder**  
2. **Enter pattern**  
3. **File extensions** (e.g., `.jpg, .png`)  
4. **☑️ Include subfolders** (if needed)  
5. **Preview** → **Execute**  

---

### **4️⃣ Checksum Verification**  
**Generate hashes to verify file integrity.**  

#### **Supported Algorithms:**  
- **MD5**  
- **SHA1**  
- **SHA256**  
- **SHA512**  

#### **Steps:**  
1. **Select folder**  
2. **Choose algorithm**  
3. **Click "Calculate Checksums"**  
4. **Results appear in the text box**  

📌 **Use Case:**  
- Verify if a file was modified by comparing checksums.  

---

### **5️⃣ Log Viewer**  
**View all operations in real-time.**  

#### **Features:**  
- **Refresh** (update logs)  
- **Clear Logs** (reset log file)  
- **Open Log File** (in default text editor)  

Logs are saved in `cons0leweb_utils.log`.  

---

## **⚠️ Troubleshooting**  

| Issue | Solution |
|-------|----------|
| **App crashes on startup** | Ensure Python 3.8+ is installed |
| **Files not processing** | Check file extensions & permissions |
| **Backups not restoring** | Ensure `.bak.cu` files exist |
| **Slow performance** | Reduce thread count (future update) |

---

## **❓ FAQs**  

**Q: Can I undo changes?**  
✅ **Yes!** Use **"Restore Backups"** to revert modified files.  

**Q: Does it work on Linux/Mac?**  
✅ **Yes**, if Python and Tkinter are installed.  

**Q: How do I process only specific files?**  
🔹 Use **file extensions** (e.g., `.txt, .csv`) to filter.  

**Q: Can I rename files in subfolders?**  
✅ **Yes**, enable **"Include subfolders"**.  

---

## **🎉 Conclusion**  
**Cons0leweb Utils Pro** is a **versatile file management tool** for bulk operations.  

🔹 **Use cases:**  
- **Web developers** (batch-edit HTML/CSS/JS)  
- **Data analysts** (clean up CSV/log files)  
- **System admins** (verify file integrity)  

🚀 **Happy file processing!** 🚀
