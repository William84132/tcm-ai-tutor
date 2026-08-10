# 全自动扫描版PDF处理工具

## 工具说明
这是一个全自动的扫描版PDF文字识别工具，可以自动将PDF文件转换为可读取的文本格式，支持批量处理和图像增强OCR识别。

## 核心功能
1. **智能识别**：自动判断PDF是文本版还是扫描版
2. **OCR识别**：使用Tesseract进行光学字符识别（需先配置）
3. **图像预处理**：增强对比度、去噪、二值化提高识别准确率
4. **批量处理**：支持批量转换多个PDF文件
5. **完全自动化**：您只需提供PDF路径，工具自动完成所有步骤

## 使用方法

### 方法一：单文件处理
```
python "{仓库根}\叶天士\10-学习工具\全自动PDF处理工具.py" <PDF文件路径>
```

示例：
```bash
python "{仓库根}\叶天士\10-学习工具\全自动PDF处理工具.py" "{仓库根}\叶天士\00-原著全文\伤寒论.pdf"
```

### 方法二：批量处理目录
```bash
python "{仓库根}\叶天士\10-学习工具\全自动PDF处理工具.py" --batch "PDF文件夹路径"
```

示例：
```bash
python "{仓库根}\叶天士\10-学习工具\全自动PDF处理工具.py" --batch "{仓库根}\叶天士\00-原著全文"
```

## 工作流程

### 第一步：检测PDF类型
```
[1] 尝试使用pdfplumber提取文本
[2] 如果文本层字符数>100，使用文本提取模式
[3] 否则，自动切换到OCR识别模式
```

### 第二步：自动处理
```
[文本PDF] → 直接提取文本 → 保存为TXT
[扫描PDF] → 转换为图像 → OCR识别 → 保存为TXT
```

### 第三步：输出结果
```
[成功] 输出文件路径 + 字符数统计
[失败] 显示错误信息 + 解决方案建议
```

## 依赖项（按优先级）

### 必须项
1. **Python 3.8+**
2. **pdfplumber**：`pip install pdfplumber`
   - 用途：文本PDF提取、PDF信息获取

### OCR功能（可选）
3. **Tesseract**：下载链接 https://github.com/UB-Mannheim/tesseract/wiki
   - 用途：扫描版PDF的OCR识别
   - 需安装中文语言包 chi_sim

4. **Poppler**（PDF转图像）：下载链接 https://github.com/oschwartz10612/poppler-windows/releases
   - 用途：pdf2image的底层依赖
   - 路径：解压到 `E:\360Downloads\poppler`

5. **pytesseract**：`pip install pytesseract`
   - 用途：Tesseract的Python接口

6. **pdf2image**：`pip install pdf2image`
   - 用途：将PDF页面转换为图像

7. **Pillow**：`pip install pillow`
   - 用途：图像处理和预处理

### 高级功能（可选）
8. **OpenCV**：`pip install opencv-python`
   - 用途：高级图像增强处理

## 配置文件路径
```python
TESSERACT_PATH = r"E:\360Downloads\tesseract.exe"
TESSDATA_PATH = r"{TESSDATA路径}"
POPPLER_PATH = r"E:\360Downloads\poppler\poppler-26.02.0\Library\bin"
```

## 故障排除

### 问题1：显示"Unable to get page count"
**原因**：Poppler未安装或未配置正确
**解决**：
1. 下载Poppler：https://github.com/oschwartz10612/poppler-windows/releases
2. 解压到 `E:\360Downloads\poppler`
3. 确保 `E:\360Downloads\poppler\poppler-xx.xx\Library\bin` 存在

### 问题2：OCR识别结果为空
**原因**：Tesseract未安装或语言包缺失
**解决**：
1. 下载Tesseract：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装时勾选 "Additional language data" → 选择 "Chinese Simplified"
3. 安装后确保 `tessdata` 文件夹中有 `chi_sim.traineddata`

### 问题3：提示"依赖项缺失"
**解决**：运行以下命令安装缺失的依赖
```bash
pip install pdfplumber pytesseract pillow pdf2image opencv-python
```

## 输出格式
```
============================================================
全自动PDF处理工具 v2.0
============================================================
输入文件: e:\path\to\document.pdf
输出文件: e:\path\to\document.txt
处理状态: 成功
识别页数: 50
总字符数: 15000
完成时间: 2024-01-01 12:00:00
============================================================
```

## 注意事项
1. **扫描质量**：PDF扫描分辨率越高，识别准确率越好（建议300DPI）
2. **中文识别**：确保安装了 chi_sim 中文语言包
3. **大文件处理**：处理大型PDF可能需要几分钟，请耐心等待
4. **批量处理**：建议每次批量处理不超过10个文件

## 版权说明
此工具仅供个人学习研究使用。
