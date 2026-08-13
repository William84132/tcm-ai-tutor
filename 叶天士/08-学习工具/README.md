# 学习工具

PDF / OCR 处理工具集（命令行使用）。

## 首次使用配置

编辑本目录 `工具配置.json`，填入本机实际路径：

```json
{
  "tesseract": "Tesseract OCR 可执行文件路径",
  "tessdata": "Tesseract 语言包目录",
  "ghostscript": "Ghostscript gswin64c.exe 路径",
  "poppler_bin": "Poppler Library/bin 目录"
}
```

不配置则 OCR 类功能不可用（文本类 PDF 提取不受影响）。

## 工具清单

- `扫描版PDF处理工具.py` —— 智能识别文本版/扫描版，OCR 提取（`-i` 单文件 / `-d` 批量 / `--check` 检查依赖）
- `全自动PDF处理工具.py` —— 全自动转换（`<PDF路径>` 单文件 / `--batch <目录>`）
- `Poppler文本提取工具.py` —— Poppler pdftotext 提取
- `OCR_space在线工具.py` / `OCR_space工具.py` —— OCR.Space 在线 API
- `Ghostscript_OCR工具.py` —— Ghostscript + Tesseract 管线
- `医案工具.py` / `医案处理工具.py` —— 医案文本处理
