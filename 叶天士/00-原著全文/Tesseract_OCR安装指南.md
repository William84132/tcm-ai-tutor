# Tesseract OCR 安装指南（Windows）

## 步骤1：下载Tesseract OCR

### 方法1：从UB Mannheim下载（推荐）
1. 访问下载地址：https://github.com/UB-Mannheim/tesseract/wiki
2. 下载最新的Windows安装程序（tesseract-ocr-w64-setup-xx.x.x.exe）
3. 运行安装程序

### 方法2：直接下载
从GitHub releases页面下载：
https://github.com/UB-Mannheim/tesseract/releases

---

## 步骤2：安装Tesseract

1. 运行下载的安装程序
2. 选择安装路径（建议使用默认路径）：
   ```
   C:\Program Files\Tesseract-OCR
   ```
3. 完成安装

---

## 步骤3：下载中文语言包

Tesseract默认只支持英语，需要下载中文语言包才能识别中文。

### 下载语言包
1. 访问：https://github.com/tesseract-ocr/tessdata
2. 下载以下文件：
   - `chi_sim.traineddata`（简体中文）
   - `chi_tra.traineddata`（繁体中文）
   - `eng.traineddata`（英语，已包含在安装中）

### 安装语言包
将下载的语言包文件复制到Tesseract安装目录的`tessdata`文件夹中：
```
C:\Program Files\Tesseract-OCR\tessdata\
```

---

## 步骤4：配置系统PATH环境变量

### 手动配置步骤：

1. **打开系统属性**
   - 按 `Win + R`，输入 `sysdm.cpl`，回车
   - 或右键"此电脑" → "属性" → "高级系统设置"

2. **打开环境变量设置**
   - 点击"高级"选项卡
   - 点击"环境变量"按钮

3. **编辑PATH变量**
   - 在"系统变量"中找到 `Path`，双击编辑
   - 点击"新建"
   - 添加路径：`C:\Program Files\Tesseract-OCR`
   - 点击"确定"

4. **验证配置**
   - 打开新的命令提示符（CMD）
   - 输入：`tesseract --version`
   - 应该显示版本信息

---

## 步骤5：安装Python依赖库

在命令提示符中运行：

```bash
pip install pytesseract
pip install pillow
pip install pdf2image
pip install PyMuPDF
```

---

## 步骤6：验证安装

### 测试Tesseract
```bash
tesseract --version
```

应该显示类似：
```
tesseract 5.x.x
leptonica-1.x.x
libjpeg ... etc.
```

### 测试语言包
```bash
tesseract --list-langs
```

应该显示包含：
```
eng
chi_sim
chi_tra
```

---

## 步骤7：测试中文OCR

创建一个测试脚本 `测试中文OCR.py`：

```python
"""测试Tesseract中文OCR"""
import pytesseract
from PIL import Image
import os

# 设置Tesseract路径（如果不在默认位置）
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 测试图片（可以是截图或扫描件）
test_image = r"test.png"

if os.path.exists(test_image):
    # 识别中文
    text = pytesseract.image_to_string(Image.open(test_image), lang='chi_sim')
    print("识别的文字：")
    print(text)
else:
    print("测试图片不存在，请先创建一个包含中文的图片文件")
```

---

## 常见问题

### 问题1：tesseract命令找不到
**解决**：检查PATH环境变量是否正确添加，重启命令提示符

### 问题2：识别结果为空或乱码
**解决**：
1. 确认语言包已正确安装到tessdata文件夹
2. 使用正确的语言参数：`lang='chi_sim'`
3. 检查图片质量，确保文字清晰

### 问题3：识别准确率低
**解决**：
1. 提高图片分辨率和清晰度
2. 使用图像预处理（去噪、二值化等）
3. 调整Tesseract参数

---

## 下一步

安装完成后，运行 `pdf转txt工具_OCR版.py` 来转换您的医案PDF。
