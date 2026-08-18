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
TESSERACT_PATH = _CFG.get('tesseract', '')
TESSDATA_PATH = _CFG.get('tessdata', '')
POPPLER_PATH = _CFG.get('poppler_bin', '')

os.environ['PATH'] = POPPLER_PATH + os.pathsep + os.environ.get('PATH', '')
os.environ['TESSDATA_PREFIX'] = TESSDATA_PATH

def check_and_fix_pdf(pdf_path):
    """检查并尝试修复PDF文件"""
    print("[INFO] 检查PDF文件...")
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"[X] 文件不存在: {pdf_path}")
        return None
    
    # 检查文件大小
    file_size = os.path.getsize(pdf_path)
    if file_size < 100:
        print(f"[X] 文件过小: {file_size} 字节")
        return None
    
    print(f"[OK] 文件大小: {file_size/1024/1024:.2f} MB")
    return pdf_path

def method_pdfplumber(pdf_path):
    """方法1：pdfplumber"""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    full_text += f"=== 第 {i} 页 ===\n{text}\n\n"
            
            if len(full_text.replace(" ", "")) > 100:
                return True, full_text
            return False, None
    except Exception as e:
        print(f"[X] pdfplumber失败: {str(e)[:50]}")
        return None, None

def method_poppler(pdf_path):
    """方法2：Poppler pdftotext"""
    pdftotext_path = os.path.join(POPPLER_PATH, "pdftotext.exe")
    
    if not os.path.exists(pdftotext_path):
        print("[X] Poppler未安装")
        return None, None
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name
        
        cmd = [pdftotext_path, "-layout", "-enc", "UTF-8", pdf_path, tmp_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=os.environ.copy())
        
        if result.returncode == 0 and os.path.exists(tmp_path):
            with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            os.remove(tmp_path)
            
            if len(text.replace(" ", "")) > 100:
                return True, text
            else:
                return False, None
        else:
            print(f"[X] Poppler失败，退出码: {result.returncode}")
            return None, None
            
    except subprocess.TimeoutExpired:
        print("[X] Poppler超时")
        return None, None
    except Exception as e:
        print(f"[X] Poppler错误: {str(e)[:50]}")
        return None, None

def method_ocr(pdf_path):
    """方法3：PDF转图像 + OCR"""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
        print("[INFO] PDF转图像...")
        images = convert_from_path(
            pdf_path,
            poppler_path=POPPLER_PATH,
            dpi=300,
            grayscale=True,
            timeout=120
        )
        
        print(f"[OK] 转换 {len(images)} 页")
        
        full_text = ""
        for i, img in enumerate(images, 1):
            print(f"[INFO] OCR第 {i} 页...")
            text = pytesseract.image_to_string(img, lang='chi_sim')
            full_text += f"=== 第 {i} 页 ===\n{text}\n\n"
        
        if len(full_text.replace(" ", "")) > 100:
            return True, full_text
        return False, None
        
    except Exception as e:
        print(f"[X] OCR失败: {str(e)[:50]}")
        return None, None

def process_pdf(pdf_path, output_path=None):
    """处理PDF文件"""
    print("=" * 70)
    print("          全自动PDF处理工具（增强版）")
    print("=" * 70)
    print(f"[时间] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[输入] {pdf_path}")
    print()
    
    # 检查PDF
    if not check_and_fix_pdf(pdf_path):
        return False
    
    # 生成输出路径
    if output_path is None:
        output_path = pdf_path.rsplit('.', 1)[0] + '_识别结果.txt'
    
    methods = [
        ("pdfplumber", method_pdfplumber),
        ("Poppler pdftotext", method_poppler),
        ("OCR识别", method_ocr)
    ]
    
    result_text = None
    success_method = None
    
    for method_name, method_func in methods:
        print(f"\n[方法] 尝试 {method_name}...")
        
        success, text = method_func(pdf_path)
        
        if success:
            result_text = text
            success_method = method_name
            print(f"[OK] {method_name} 成功")
            break
        elif success is False:
            print(f"[INFO] {method_name} 返回文本过少")
        else:
            print(f"[INFO] {method_name} 无法处理")
    
    # 保存结果
    print("\n" + "=" * 70)
    if result_text:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_text)
        
        char_count = len(result_text.replace(" ", "").replace("\n", ""))
        
        print("[成功] 处理完成！")
        print(f"[方法] {success_method}")
        print(f"[输出] {output_path}")
        print(f"[字符] {char_count:,} 个")
        print("=" * 70)
        return True
    else:
        print("[失败] 所有方法均失败")
        print()
        print("可能原因:")
        print("  1. PDF文件是加密或损坏的")
        print("  2. PDF是扫描版但缺少OCR组件")
        print("  3. 文件路径包含特殊字符")
        print()
        print("建议方案:")
        print("  1. 检查PDF文件是否可以正常打开")
        print("  2. 确保Tesseract已安装中文语言包")
        print("  3. 尝试使用在线OCR服务")
        print("=" * 70)
        return False

def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print("          全自动PDF处理工具（增强版）")
        print("=" * 70)
        print()
        print("使用方法:")
        print(f'  python "{os.path.basename(__file__)}" "PDF文件路径"')
        print()
        print("示例:")
        print(f'  python "{os.path.basename(__file__)}" "<你的古籍PDF路径>/伤寒论.pdf"')
        print()
        print("功能:")
        print("  - 自动检测PDF类型")
        print("  - 支持text PDF和扫描版PDF")
        print("  - 多方法自动尝试")
        print("=" * 70)
        sys.exit(0)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_pdf(pdf_path, output_path)

if __name__ == "__main__":
    main()