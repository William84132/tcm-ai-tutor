import os

import json as _json
def _load_cfg():
    _cfg = {}
    _p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '工具配置.json')
    if os.path.exists(_p):
        try:
            with open(_p, encoding='utf-8') as _f:
                _cfg = _json.load(_f)
        except Exception:
            pass
    return _cfg
_CFG = _load_cfg()

import sys
import subprocess

def check_and_convert_file_encoding(file_path, output_path=None):
    """检查并修复文件编码问题"""
    if output_path is None:
        output_path = file_path + "_fixed.txt"
    
    try:
        # 尝试多种编码读取
        encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
        content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    print(f"[OK] 使用 {encoding} 编码成功读取")
                    break
            except Exception:
                continue
        
        if content is None:
            print(f"[X] 无法识别文件编码: {file_path}")
            return False
        
        # 检查是否有乱码（包含不可打印字符）
        has_garbage = any(ord(c) > 0xFFFF or (ord(c) < 32 and c not in '\r\n\t') for c in content)
        
        if has_garbage:
            print("[WARN] 文件包含乱码字符，尝试修复...")
            # 过滤不可打印字符
            clean_content = ''.join(c for c in content if ord(c) < 0xFFFF and (ord(c) >= 32 or c in '\r\n\t'))
            content = clean_content
        
        # 保存为UTF-8编码
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[OK] 文件已保存为UTF-8编码: {output_path}")
        print(f"[OK] 文件大小: {len(content)} 字符")
        return True
        
    except Exception as e:
        print(f"[X] 处理文件时出错: {e}")
        return False

def extract_text_with_tesseract(pdf_path, output_path, pages=None):
    """使用Tesseract OCR提取扫描版PDF文本"""
    try:
        # 检查Tesseract是否可用
        tesseract_path = _CFG.get('tesseract', '')
        if not os.path.exists(tesseract_path):
            print(f"[X] Tesseract不存在: {tesseract_path}")
            return False
        
        # 检查是否已安装pdf2image依赖
        try:
            from pdf2image import convert_from_path
            HAS_PDF2IMAGE = True
        except ImportError:
            print("[X] pdf2image未安装")
            return False
        
        # 检查Poppler
        poppler_path = _CFG.get('poppler_bin', '')
        if not os.path.exists(poppler_path):
            print(f"[X] Poppler不存在: {poppler_path}")
            return False
        
        print(f"[INFO] 开始处理扫描版PDF: {pdf_path}")
        print(f"[INFO] 使用Poppler: {poppler_path}")
        
        # 转换PDF为图像
        try:
            images = convert_from_path(
                pdf_path,
                poppler_path=poppler_path,
                first_page=pages[0] if pages else None,
                last_page=pages[1] if pages else None,
                grayscale=True,
                dpi=300
            )
            print(f"[OK] 成功转换 {len(images)} 页")
        except Exception as e:
            print(f"[X] PDF转图像失败: {e}")
            return False
        
        # 使用Tesseract进行OCR
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        full_text = ""
        for i, img in enumerate(images, 1):
            try:
                print(f"[INFO] 正在识别第 {i}/{len(images)} 页...")
                text = pytesseract.image_to_string(img, lang='chi_sim')
                full_text += text + "\n\n"
            except Exception as e:
                print(f"[WARN] 第 {i} 页识别失败: {e}")
                continue
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"[OK] OCR完成!")
        print(f"[OK] 输出文件: {output_path}")
        print(f"[OK] 识别字符数: {len(full_text)}")
        return True
        
    except Exception as e:
        print(f"[X] OCR处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("完整OCR解决方案")
    print("=" * 60)
    
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python 完整OCR解决方案.py fix <输入文件> [输出文件]")
        print("  python 完整OCR解决方案.py ocr <PDF文件> <输出文件>")
        print("  python 完整OCR解决方案.py ocr <PDF文件> <输出文件> --pages 1-10")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "fix":
        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        check_and_convert_file_encoding(input_file, output_file)
    
    elif command == "ocr":
        pdf_file = sys.argv[2]
        output_file = sys.argv[3]
        
        # 检查是否指定页码范围
        pages = None
        if "--pages" in sys.argv:
            idx = sys.argv.index("--pages")
            if idx + 1 < len(sys.argv):
                page_range = sys.argv[idx + 1]
                if "-" in page_range:
                    start, end = page_range.split("-")
                    pages = (int(start), int(end))
        
        extract_text_with_tesseract(pdf_file, output_file, pages)
    
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()