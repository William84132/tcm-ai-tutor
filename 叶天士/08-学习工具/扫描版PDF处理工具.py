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
import traceback
import shutil

# 配置Tesseract路径
TESSERACT_PATH = _CFG.get('tesseract', '')
TESSDATA_PATH = _CFG.get('tessdata', '')
os.environ['TESSDATA_PREFIX'] = TESSDATA_PATH

# 配置Poppler路径（pdf2image依赖）
POPPLER_PATH = _CFG.get('poppler_bin', '')
os.environ['PATH'] = POPPLER_PATH + os.pathsep + os.environ.get('PATH', '')

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    from PIL import Image, ImageEnhance, ImageFilter
    from pdf2image import convert_from_path
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

def preprocess_image(image):
    """图像预处理：增强对比度、去噪、二值化"""
    try:
        # 转换为灰度图
        img = image.convert('L')
        
        # 增强对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # 应用中值滤波去噪
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # 二值化处理
        threshold = 128
        img = img.point(lambda p: p > threshold and 255)
        
        return img
    except Exception as e:
        print(f"图像预处理失败: {e}")
        return image

def preprocess_image_opencv(image):
    """使用OpenCV进行高级图像预处理"""
    if not HAS_OPENCV:
        return image
    
    try:
        # 转换为OpenCV格式
        open_cv_image = np.array(image)
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        
        # 转换为灰度图
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        
        # 使用自适应阈值进行二值化
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # 去除噪声
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # 转换回PIL图像
        return Image.fromarray(cleaned)
    except Exception as e:
        print(f"OpenCV预处理失败: {e}")
        return image

def extract_text_with_ocr(image, lang='chi_sim+eng'):
    """使用OCR提取图像中的文本"""
    try:
        # 预处理图像
        processed_img = preprocess_image(image)
        
        # 尝试使用预处理后的图像进行OCR
        text = pytesseract.image_to_string(processed_img, lang=lang)
        
        # 如果结果不理想，尝试OpenCV预处理
        if len(text.strip()) < 50:
            processed_img = preprocess_image_opencv(image)
            text = pytesseract.image_to_string(processed_img, lang=lang)
        
        return text
    except Exception as e:
        print(f"OCR提取失败: {e}")
        return ""

def extract_text_from_pdf(pdf_path, use_ocr_only=False):
    """智能提取PDF文本，支持扫描版PDF"""
    text = ""
    file_size = os.path.getsize(pdf_path)
    print(f"PDF文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    # 如果不是强制OCR，先尝试使用pdfplumber提取文本
    if not use_ocr_only and HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"\r处理第 {page_num}/{len(pdf.pages)} 页 (pdfplumber)...", end="")
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) > 0:
                        text += page_text + "\n\n"
            
            # 如果提取到了有效文本（超过500字符且不是乱码）
            if len(text.strip()) > 500:
                # 检查是否是有效文本（中文字符比例）
                chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
                if chinese_chars > len(text) * 0.1:  # 至少10%是中文
                    print(f"\n[OK] 使用pdfplumber成功提取文本，共 {len(text.strip())} 字符")
                    return text
        except Exception as e:
            print(f"\n[X] pdfplumber提取失败: {e}")
    
    # 使用OCR提取
    if HAS_OCR:
        try:
            print("\n使用OCR提取文本...")
            pages = convert_from_path(pdf_path)
            total_pages = len(pages)
            
            for page_num, page in enumerate(pages, 1):
                print(f"\r处理第 {page_num}/{total_pages} 页 (OCR)...", end="")
                page_text = extract_text_with_ocr(page)
                if page_text:
                    text += page_text + "\n\n"
            
            if len(text.strip()) > 100:
                print(f"\n[OK] 使用OCR成功提取文本，共 {len(text.strip())} 字符")
                return text
            else:
                print(f"\n[!] OCR提取结果较少: {len(text.strip())} 字符")
        except Exception as e:
            print(f"\n[X] OCR提取失败: {e}")
            traceback.print_exc()
    
    return None

def process_single_pdf(pdf_path, output_path=None):
    """处理单个PDF文件"""
    if not os.path.exists(pdf_path):
        print(f"[X] 文件不存在: {pdf_path}")
        return None
    
    print(f"=" * 60)
    print(f"正在处理: {os.path.basename(pdf_path)}")
    print(f"路径: {pdf_path}")
    print("=" * 60)
    
    text = extract_text_from_pdf(pdf_path)
    
    if text:
        if output_path is None:
            output_path = pdf_path.replace('.pdf', '.txt')
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[OK] 已保存到: {output_path}")
        print(f"[OK] 文件大小: {os.path.getsize(output_path) / 1024:.2f} KB")
        return output_path
    else:
        print(f"[X] 无法提取文本")
        return None

def process_all_pdfs(input_dir, output_dir):
    """批量处理所有PDF文件"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    pdf_files = []
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if f.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, f))
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    success_count = 0
    fail_count = 0
    
    for pdf_file in pdf_files:
        # 计算相对路径，保持目录结构
        rel_path = os.path.relpath(pdf_file, input_dir)
        output_path = os.path.join(output_dir, rel_path.replace('.pdf', '.txt'))
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"\n处理: {rel_path}")
        
        result = process_single_pdf(pdf_file, output_path)
        if result:
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n" + "=" * 60)
    print(f"处理完成！")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print("=" * 60)

def check_dependencies():
    """检查依赖项"""
    print("=" * 60)
    print("依赖项检查")
    print("=" * 60)
    print(f"pdfplumber: {'OK 已安装' if HAS_PDFPLUMBER else 'X 未安装'}")
    print(f"pytesseract: {'OK 已安装' if HAS_OCR else 'X 未安装'}")
    print(f"pillow: {'OK 已安装' if HAS_OCR else 'X 未安装'}")
    print(f"pdf2image: {'OK 已安装' if HAS_OCR else 'X 未安装'}")
    print(f"OpenCV: {'OK 已安装' if HAS_OPENCV else 'X 未安装'}")
    
    # 检查Poppler
    poppler_check = os.path.exists(os.path.join(_CFG.get('poppler_bin', ''), 'pdfinfo.exe'))
    print(f"Poppler: {'OK 已安装' if poppler_check else 'X 未安装'}")
    
    # 检查Tesseract
    if HAS_OCR:
        try:
            version = pytesseract.get_tesseract_version()
            print(f"Tesseract版本: {version}")
            
            # 检查语言包
            langs = pytesseract.get_languages()
            print(f"可用语言包: {', '.join(langs)}")
            if 'chi_sim' not in langs:
                print("警告: 未找到中文语言包(chi_sim)")
        except Exception as e:
            print(f"Tesseract检查失败: {e}")
    
    print("=" * 60)

def show_help():
    """显示帮助信息"""
    help_text = """
扫描版PDF处理工具 - 使用说明

功能：
  - 自动识别PDF类型（文本版或扫描版）
  - 对扫描版PDF进行OCR识别
  - 支持中文、英文等多语言识别
  - 图像预处理提高识别准确率
  - 批量处理多个PDF文件

使用方法：
  1. 确保已安装依赖：
     pip install pdfplumber pytesseract pillow pdf2image opencv-python
     
  2. 配置Tesseract路径（在代码中修改）
     TESSERACT_PATH = r"你的tesseract.exe路径"
     TESSDATA_PATH = r"你的tessdata路径"

  3. 运行方式：
     python 扫描版PDF处理工具.py -i <输入PDF路径> -o <输出TXT路径>
     python 扫描版PDF处理工具.py -d <输入目录> -o <输出目录>
     python 扫描版PDF处理工具.py --check  # 检查依赖

参数：
  -i, --input     单个PDF文件路径
  -o, --output    输出文件/目录路径
  -d, --dir       输入目录（批量处理）
  --check         检查依赖项
  --ocr-only      强制使用OCR模式
  -h, --help      显示此帮助信息

示例：
  python 扫描版PDF处理工具.py -i "中医古籍.pdf" -o "中医古籍.txt"
  python 扫描版PDF处理工具.py -d "<你的PDF文件夹>" -o "<你的文本文件夹>"
  python 扫描版PDF处理工具.py --check
    """
    print(help_text)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='扫描版PDF处理工具', add_help=False)
    parser.add_argument('-i', '--input', help='单个PDF文件路径')
    parser.add_argument('-o', '--output', help='输出文件/目录路径')
    parser.add_argument('-d', '--dir', help='输入目录（批量处理）')
    parser.add_argument('--check', action='store_true', help='检查依赖项')
    parser.add_argument('--ocr-only', action='store_true', help='强制使用OCR模式')
    parser.add_argument('-h', '--help', action='store_true', help='显示帮助信息')
    
    args = parser.parse_args()
    
    if args.help:
        show_help()
        sys.exit(0)
    
    if args.check:
        check_dependencies()
        sys.exit(0)
    
    if args.input:
        output_path = args.output if args.output else None
        process_single_pdf(args.input, output_path)
    elif args.dir:
        output_dir = args.output if args.output else args.dir + "_文本版"
        process_all_pdfs(args.dir, output_dir)
    else:
        print("请指定输入文件或目录！")
        print("使用 -h 参数查看帮助")