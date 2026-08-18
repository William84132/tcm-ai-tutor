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
import tempfile
from datetime import datetime

# ==================== 配置区 ====================
# 路径配置
TESSERACT_PATH = _CFG.get('tesseract', '')
TESSDATA_PATH = _CFG.get('tessdata', '')
POPPLER_PATH = _CFG.get('poppler_bin', '')

# 添加Poppler到PATH
os.environ['PATH'] = POPPLER_PATH + os.pathsep + os.environ.get('PATH', '')
os.environ['TESSDATA_PREFIX'] = TESSDATA_PATH

# ==================== 依赖检查 ====================
def check_dependencies():
    """检查所有依赖项"""
    deps = {}
    
    # Python库检查
    try:
        import pdfplumber
        deps['pdfplumber'] = True
    except ImportError:
        deps['pdfplumber'] = False
    
    try:
        import pytesseract
        deps['pytesseract'] = True
    except ImportError:
        deps['pytesseract'] = False
    
    try:
        from PIL import Image
        deps['pillow'] = True
    except ImportError:
        deps['pillow'] = False
    
    try:
        from pdf2image import convert_from_path
        deps['pdf2image'] = True
    except ImportError:
        deps['pdf2image'] = False
    
    try:
        import cv2
        deps['opencv'] = True
    except ImportError:
        deps['opencv'] = False
    
    try:
        import requests
        deps['requests'] = True
    except ImportError:
        deps['requests'] = False
    
    # 可执行文件检查
    deps['tesseract'] = os.path.exists(TESSERACT_PATH)
    deps['poppler'] = os.path.exists(os.path.join(POPPLER_PATH, "pdftotext.exe"))
    
    return deps

def install_dependencies():
    """自动安装缺失的Python依赖"""
    print("[步骤0] 检查并安装Python依赖...")
    
    missing = []
    try:
        import pdfplumber
    except ImportError:
        missing.append('pdfplumber')
    
    try:
        import pytesseract
    except ImportError:
        missing.append('pytesseract')
    
    try:
        from PIL import Image
    except ImportError:
        missing.append('pillow')
    
    try:
        from pdf2image import convert_from_path
    except ImportError:
        missing.append('pdf2image')
    
    try:
        import requests
    except ImportError:
        missing.append('requests')
    
    if missing:
        print(f"[INFO] 缺少依赖: {', '.join(missing)}")
        print("[INFO] 正在安装...")
        
        for lib in missing:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', lib], 
                             check=True, capture_output=True)
                print(f"[OK] 安装成功: {lib}")
            except:
                print(f"[X] 安装失败: {lib}")
        
        return len(missing) == 0
    else:
        print("[OK] 所有Python依赖已安装")
        return True

# ==================== 核心功能 ====================

def method1_pdfplumber(pdf_path):
    """方法1：使用pdfplumber直接提取文本"""
    print("[方法1] 尝试使用pdfplumber提取文本...")
    
    try:
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    full_text += f"=== 第 {i} 页 ===\n{text}\n\n"
            
            char_count = len(full_text.replace(" ", "").replace("\n", ""))
            
            if char_count > 100:
                print(f"[OK] 成功提取文本，共 {char_count} 字符")
                return True, full_text
            else:
                print(f"[X] 文本过少（{char_count}字符），可能为扫描版")
                return False, None
                
    except Exception as e:
        print(f"[X] pdfplumber失败: {e}")
        return False, None

def method2_poppler_text(pdf_path):
    """方法2：使用Poppler pdftotext提取文本"""
    print("[方法2] 尝试使用Poppler pdftotext...")
    
    pdftotext_path = os.path.join(POPPLER_PATH, "pdftotext.exe")
    
    if not os.path.exists(pdftotext_path):
        print("[X] Poppler未安装")
        return False, None
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name
        
        cmd = [pdftotext_path, "-layout", "-enc", "UTF-8", pdf_path, tmp_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(tmp_path):
            with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            char_count = len(text.replace(" ", "").replace("\n", ""))
            
            if char_count > 100:
                os.remove(tmp_path)
                print(f"[OK] 成功提取文本，共 {char_count} 字符")
                return True, text
            else:
                os.remove(tmp_path)
                print(f"[X] 文本过少")
                return False, None
        else:
            print(f"[X] pdftotext失败")
            return False, None
            
    except Exception as e:
        print(f"[X] pdftotext错误: {e}")
        return False, None

def method3_ocr_images(images):
    """方法3：使用Tesseract OCR识别图像"""
    print("[方法3] 使用Tesseract OCR识别...")
    
    if not os.path.exists(TESSERACT_PATH):
        print("[X] Tesseract未安装")
        return None
    
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter
        
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
        full_text = ""
        
        for i, img in enumerate(images, 1):
            print(f"[INFO] 正在识别第 {i}/{len(images)} 页...")
            
            # 图像预处理
            if img.mode != 'L':
                img = img.convert('L')
            
            # 增强对比度
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            # OCR识别
            text = pytesseract.image_to_string(img, lang='chi_sim')
            full_text += f"=== 第 {i} 页 ===\n{text}\n\n"
        
        char_count = len(full_text.replace(" ", "").replace("\n", ""))
        print(f"[OK] OCR识别完成，共 {char_count} 字符")
        
        return full_text
        
    except Exception as e:
        print(f"[X] OCR失败: {e}")
        return None

def method4_pdf2image_ocr(pdf_path):
    """方法4：PDF转图像 + OCR"""
    print("[方法4] 使用pdf2image + Tesseract OCR...")
    
    if not os.path.exists(os.path.join(POPPLER_PATH, "pdftotext.exe")):
        print("[X] Poppler未安装，无法转换PDF为图像")
        return None
    
    try:
        from pdf2image import convert_from_path
        
        print("[INFO] 正在将PDF转换为图像...")
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH, dpi=300)
        print(f"[INFO] 成功转换 {len(images)} 页")
        
        return method3_ocr_images(images)
        
    except Exception as e:
        print(f"[X] pdf2image失败: {e}")
        return None

def method5_online_ocr(pdf_path, api_key="helloworld"):
    """方法5：在线OCR API（备选方案）"""
    print("[方法5] 尝试在线OCR服务...")
    
    try:
        import requests
        
        # 检查是否有可用的图像文件（可能是之前的转换结果）
        # 由于需要PDF转图像，这里主要作为备选
        
        print("[INFO] 在线OCR需要先将PDF转为图像")
        print("[INFO] 如果前面方法失败，建议手动安装Poppler")
        return None
        
    except ImportError:
        print("[X] requests库未安装")
        return None

# ==================== 主处理流程 ====================

def process_pdf_fully_automated(pdf_path, output_path=None):
    """全自动PDF处理主函数"""
    
    print("=" * 70)
    print("                全自动PDF处理工具 v2.0")
    print("=" * 70)
    print(f"[时间] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[输入] {pdf_path}")
    print()
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"[X] 文件不存在: {pdf_path}")
        return False
    
    # 生成输出路径
    if output_path is None:
        output_path = pdf_path.rsplit('.', 1)[0] + '_识别结果.txt'
    
    # 步骤0：检查依赖
    deps = check_dependencies()
    
    if not all([deps['pdfplumber'], deps['requests']]):
        print("[INFO] 正在安装基础依赖...")
        install_dependencies()
    
    print()
    print("=" * 70)
    print("开始自动处理...")
    print("=" * 70)
    print()
    
    result_text = None
    method_used = None
    
    # 方法1：pdfplumber（最优先）
    success, text = method1_pdfplumber(pdf_path)
    if success:
        result_text = text
        method_used = "pdfplumber"
    print()
    
    # 方法2：Poppler pdftotext
    if result_text is None:
        success, text = method2_poppler_text(pdf_path)
        if success:
            result_text = text
            method_used = "Poppler pdftotext"
        print()
    
    # 方法3：pdf2image + Tesseract OCR
    if result_text is None:
        if deps['poppler'] and deps['tesseract']:
            text = method4_pdf2image_ocr(pdf_path)
            if text:
                result_text = text
                method_used = "pdf2image + Tesseract OCR"
            print()
        else:
            print("[X] 方法3需要Poppler和Tesseract")
            if not deps['poppler']:
                print("[提示] 请安装Poppler: https://github.com/oschwartz10612/poppler-windows/releases")
            if not deps['tesseract']:
                print("[提示] 请安装Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
            print()
    
    # 保存结果
    print("=" * 70)
    if result_text:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_text)
        
        char_count = len(result_text.replace(" ", "").replace("\n", ""))
        
        print("[成功] 处理完成！")
        print(f"[方法] 使用 {method_used}")
        print(f"[输出] {output_path}")
        print(f"[字符] 共 {char_count} 个字符")
        print("=" * 70)
        return True
    else:
        print("[失败] 所有方法均失败")
        print()
        print("建议解决方案：")
        print("1. 安装Poppler:")
        print("   下载: https://github.com/oschwartz10612/poppler-windows/releases")
        print("   解压到: 工具配置.json 中 poppler_bin 指定位置")
        print()
        print("2. 安装Tesseract:")
        print("   下载: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   安装时选择中文语言包")
        print("   配置路径: 工具配置.json 中 tesseract 指定位置")
        print()
        print("3. 或者使用在线OCR服务处理PDF")
        print("=" * 70)
        return False

def process_directory_fully_automated(dir_path):
    """批量处理目录中的所有PDF"""
    
    print("=" * 70)
    print("              全自动批量PDF处理工具")
    print("=" * 70)
    print(f"[目录] {dir_path}")
    print()
    
    # 查找所有PDF文件
    pdf_files = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                pdf_files.append(pdf_path)
    
    if not pdf_files:
        print("[X] 未找到PDF文件")
        return
    
    print(f"[发现] 共 {len(pdf_files)} 个PDF文件")
    print()
    print("=" * 70)
    
    success_count = 0
    fail_count = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] 正在处理...")
        
        # 生成输出路径
        output_path = pdf_path.rsplit('.', 1)[0] + '_识别结果.txt'
        
        if process_pdf_fully_automated(pdf_path, output_path):
            success_count += 1
        else:
            fail_count += 1
    
    print()
    print("=" * 70)
    print("批量处理完成")
    print(f"[成功] {success_count} 个文件")
    print(f"[失败] {fail_count} 个文件")
    print("=" * 70)

# ==================== 程序入口 ====================

def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print("                全自动PDF处理工具 v2.0")
        print("=" * 70)
        print()
        print("使用方法:")
        print()
        print("  单文件处理:")
        print(f'    python "{os.path.basename(__file__)}" "PDF文件路径"')
        print()
        print("  示例:")
        print(f'    python "{os.path.basename(__file__)}" "<你的古籍PDF路径>/伤寒论.pdf"')
        print()
        print("  批量处理:")
        print(f'    python "{os.path.basename(__file__)}" --batch "文件夹路径"')
        print()
        print("=" * 70)
        print()
        print("功能说明:")
        print("  - 自动识别PDF类型（文本版/扫描版）")
        print("  - 自动选择最佳处理方法")
        print("  - 支持OCR识别扫描版PDF")
        print("  - 完全自动化，无需手动操作")
        print()
        print("依赖项:")
        print("  - pdfplumber: PDF文本提取（必需）")
        print("  - Poppler: PDF转图像（处理扫描版必需）")
        print("  - Tesseract: OCR识别（处理扫描版必需）")
        print()
        print("安装提示:")
        print("  Poppler: https://github.com/oschwartz10612/poppler-windows/releases")
        print("  Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        print("=" * 70)
        sys.exit(0)
    
    arg1 = sys.argv[1]
    
    if arg1 == "--batch":
        if len(sys.argv) < 3:
            print("[X] 请指定文件夹路径")
            sys.exit(1)
        dir_path = sys.argv[2]
        process_directory_fully_automated(dir_path)
    else:
        pdf_path = arg1
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        process_pdf_fully_automated(pdf_path, output_path)

if __name__ == "__main__":
    main()
