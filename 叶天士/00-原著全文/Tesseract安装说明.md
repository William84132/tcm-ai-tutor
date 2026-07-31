# Tesseract OCR 自动安装脚本

这个脚本会：
1. 创建 Tesseract 数据目录
2. 下载中文语言包
3. 配置环境变量
4. 测试 OCR 功能

## 需要手动操作的部分

由于网络限制，您需要手动下载以下文件：

### 1. 下载 Tesseract Portable 版（如果还没有安装程序）

访问：https://github.com/UB-Mannheim/tesseract/wiki

下载 Windows 安装程序（tesseract-ocr-w64-setup-5.5.0.x.xxx.exe）

### 2. 安装 Tesseract

运行安装程序，安装到默认路径 `C:\Program Files\Tesseract-OCR`

**重要**：安装时勾选 "Add to system PATH"

### 3. 下载中文语言包

从以下任一链接下载：
- https://github.com/tesseract-ocr/tessdata_fast/raw/main/chi_sim.traineddata
- https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata

下载后，将 `chi_sim.traineddata` 复制到：
`C:\Program Files\Tesseract-OCR\tessdata\`

### 4. 运行测试

安装完成后，双击 `测试OCR.py` 验证是否正常工作

---

## 如果 GitHub 无法访问

可以尝试以下镜像源：
- Gitee 镜像
- 其他 CDN 加速

或者使用在线 OCR 服务作为替代方案。

---

## 替代方案

如果 Tesseract 安装仍然困难，可以考虑：

1. **使用百度 OCR API** - 需要申请 API Key
2. **使用腾讯 OCR API** - 需要申请 API Key
3. **使用在线 OCR 网站** - 如 SmallPDF, iLovePDF
4. **手动复制 PDF 内容** - 最简单但需要人工操作
