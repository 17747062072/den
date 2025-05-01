# Dir Scanner

![Banner](screenshot.png)

一款跨平台目录扫描工具，支持本地文件系统与Web目录扫描

## 功能特性
- 双模式扫描（本地/Web）
- 多线程并发处理
- 智能结果过滤
- 多格式导出支持（TXT/JSON/CSV）

## 快速开始
```bash
git clone https://github.com/yourname/dir-scanner.git
pip install -r requirements.txt

# 本地扫描
python dir_scanner.py local ./test_dir -e .py

# Web扫描
python dir_scanner.py web http://example.com -d paths.txt