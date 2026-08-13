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

def extract_text_with_ghostscript(pdf_path, output_path, pages=None):
    """使用Ghostscript+Tesseract提取扫描版PDF文本"""
    try:
        # 检查Ghostscript
        gs_path = None
        gs_candidates = [
            _CFG.get('ghostscript', ''),
            r"C:\Program Files\gs\gs10.xx\bin\gswin64c.exe"
        ]
        
        for candidate in gs_candidates:
            if os.path.exists(candidate):
                gs_path = candidate
                break
        
        if gs_path is None:
            print("[X] 未找到Ghostscript")
            return False
        
        print(f"[OK] 找到Ghostscript: {gs_path}")
        
        # 检查Tesseract
        tesseract_path = _CFG.get('tesseract', '')
        if not os.path.exists(tesseract_path):
            print(f"[X] Tesseract不存在: {tesseract_path}")
            return False
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"[INFO] 使用临时目录: {temp_dir}")
            
            # 使用Ghostscript将PDF转换为PNG图像
            output_pattern = os.path.join(temp_dir, "page_%04d.png")
            
            gs_command = [
                gs_path,
                "-dNOPAUSE",
                "-dBATCH",
                "-sDEVICE=png16m",
                "-r300",
                "-dTextAlphaBits=4",
                "-dGraphicsAlphaBits=4"
            ]
            
            if pages:
                gs_command.append(f"-dFirstPage={pages[0]}")
                gs_command.append(f"-dLastPage={pages[1]}")
            
            gs_command.extend([
                f"-sOutputFile={output_pattern}",
                pdf_path
            ])
            
            print(f"[INFO] 执行Ghostscript转换...")
            result = subprocess.run(
                gs_command,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"[X] Ghostscript转换失败")
                print(f"错误: {result.stderr}")
                return False
            
            print(f"[OK] Ghostscript转换成功")
            
            # 检查生成的图像文件
            page_files = sorted([f for f in os.listdir(temp_dir) if f.startswith("page_")])
            if not page_files:
                print("[X] 未生成任何图像文件")
                return False
            
            print(f"[OK] 生成 {len(page_files)} 页图像")
            
            # 使用Tesseract进行OCR
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            full_text = ""
            for page_file in page_files:
                img_path = os.path.join(temp_dir, page_file)
                page_num = int(page_file.split("_")[1].replace(".png", ""))
                
                try:
                    print(f"[INFO] 正在识别第 {page_num} 页...")
                    text = pytesseract.image_to_string(img_path, lang='chi_sim')
                    full_text += f"=== 第 {page_num} 页 ===\n\n"
                    full_text += text + "\n\n"
                except Exception as e:
                    print(f"[WARN] 第 {page_num} 页识别失败: {e}")
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
    print("Ghostscript OCR工具")
    print("=" * 60)
    
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python Ghostscript_OCR工具.py <PDF文件> <输出文件>")
        print("  python Ghostscript_OCR工具.py <PDF文件> <输出文件> --pages 1-10")
        sys.exit(0)
    
    pdf_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 检查是否指定页码范围
    pages = None
    if "--pages" in sys.argv:
        idx = sys.argv.index("--pages")
        if idx + 1 < len(sys.argv):
            page_range = sys.argv[idx + 1]
            if "-" in page_range:
                start, end = page_range.split("-")
                pages = (int(start), int(end))
    
    extract_text_with_ghostscript(pdf_file, output_file, pages)

if __name__ == "__main__":
    main()