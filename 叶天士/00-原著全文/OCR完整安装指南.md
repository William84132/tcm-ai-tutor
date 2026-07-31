# Tesseract OCR 完整安装指南

## 📋 问题诊断结果

经过全面检测，发现以下问题：
- ✅ PyPDF2 已安装
- ✅ pytesseract 已安装  
- ❌ Tesseract 可执行文件未找到（未成功安装或未添加到PATH）
- ❌ 中文语言包未安装
- ❌ poppler 未安装（pdf2image 依赖）

---

## 🎯 解决方案

### 方案1：重新安装 Tesseract（推荐）

#### 步骤1：下载 Tesseract 安装程序

访问以下地址下载：

**主站（可能较慢）：**
- https://github.com/UB-Mannheim/tesseract/wiki

**备用地址：**
- 搜索 "tesseract-ocr-w64-setup" 

下载版本：**tesseract-ocr-w64-setup-5.5.0.x.xxx.exe**（64位）

#### 步骤2：运行安装程序

1. 双击安装程序
2. **安装路径**：选择 `C:\Program Files\Tesseract-OCR`（默认）
3. **重要**：✅ 勾选 "Add to system PATH"
4. 完成安装

#### 步骤3：下载中文语言包

下载链接（任选其一）：
- https://github.com/tesseract-ocr/tessdata_fast/raw/main/chi_sim.traineddata
- https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata

下载后，将文件复制到：
```
C:\Program Files\Tesseract-OCR\tessdata\chi_sim.traineddata
```

#### 步骤4：安装 poppler（PDF转图片依赖）

1. 下载地址：https://github.com/oschwartz10612/poppler-windows/releases
2. 下载 Latest release 的 "poppler-xx.x.xx.x.zip"
3. 解压到：`C:\poppler`
4. 将以下路径添加到系统 PATH：
   ```
   C:\poppler\Library\bin
   ```

#### 步骤5：测试

双击运行 `测试OCR.py` 验证安装

---

### 方案2：使用 Portable 版本

如果不想安装，可以使用 Portable 版本：

1. 下载 Portable 版 Tesseract
2. 解压到 `D:\Tesseract`
3. 将 `D:\Tesseract` 添加到 PATH
4. 下载中文语言包到 `D:\Tesseract\tessdata`

---

### 方案3：手动复制 PDF 内容（最简单）

如果以上方案都太复杂，最简单的方法是：

1. 打开 PDF 文件
2. 选择文本（Ctrl+A）
3. 复制（Ctrl+C）
4. 粘贴到文本文件
5. 保存为 `.txt` 文件

这样我就可以直接读取文本文件了！

---

## 🚀 快速开始

无论选择哪种方案，安装完成后：

1. 双击运行 `测试OCR.py` 验证
2. 如果通过，运行 `PDF转文本_OCR版.py` 转换医案PDF

---

## ❓ 遇到问题？

如果遇到任何问题，请告诉我：
1. 安装到了哪个目录？
2. 运行 `测试OCR.py` 的输出是什么？
3. 错误信息是什么？

我会帮您解决！
