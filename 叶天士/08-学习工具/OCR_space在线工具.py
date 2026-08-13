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
import base64
import requests
import time

def convert_pdf_to_images_pypdf2(pdf_path, output_dir):
    """使用PyPDF2将PDF的每一页转换为图像"""
    try:
        from PIL import Image
        import io
        
        try:
            import pypdf
            HAS_PYPDF = True
        except ImportError:
            try:
                import PyPDF2
                HAS_PYPDF = True
            except ImportError:
                HAS_PYPDF = False
        
        if not HAS_PYPDF:
            print("[X] PyPDF2/PyPDF未安装")
            return []
        
        print(f"[INFO] 使用PyPDF2处理PDF...")
        
        # 尝试导入pdf2image（需要Poppler）
        try:
            from pdf2image import convert_from_path
            HAS_PDF2IMAGE = True
        except ImportError:
            HAS_PDF2IMAGE = False
        
        if HAS_PDF2IMAGE:
            # 检查Poppler
            poppler_path = _CFG.get('poppler_bin', '')
            if os.path.exists(poppler_path):
                images = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=200)
                return images
            else:
                print("[X] Poppler未安装，无法使用pdf2image")
                return []
        else:
            print("[X] pdf2image未安装")
            return []
        
    except Exception as e:
        print(f"[X] PDF转图像失败: {e}")
        return []

def extract_text_from_image_ocr_space(image_path, api_key="helloworld", language="chs"):
    """使用OCR.space API从图像提取文本"""
    try:
        with open(image_path, "rb") as image_file:
            img_base64 = base64.b64encode(image_file.read()).decode()
        
        payload = {
            "base64Image": f"data:image/png;base64,{img_base64}",
            "language": language,
            "isOverlayRequired": False,
            "filetype": "PNG",
            "detectOrientation": True,
            "scale": True,
            "OCREngine": 2
        }
        
        headers = {
            "apikey": api_key
        }
        
        response = requests.post(
            "https://api.ocr.space/parse/image",
            data=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("IsErroredOnProcessing"):
                error_message = result.get("ErrorMessage", ["Unknown error"])
                print(f"[X] OCR错误: {error_message}")
                return None
            
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                text = parsed_results[0].get("ParsedText", "")
                return text
        
        print(f"[X] API请求失败: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"[X] OCR.space API调用失败: {e}")
        return None

def process_pdf_with_ocr_space(pdf_path, output_path, api_key="helloworld"):
    """处理PDF文件并提取文本"""
    try:
        print("=" * 60)
        print("OCR.space 在线OCR处理工具")
        print("=" * 60)
        print(f"[INFO] 输入PDF: {pdf_path}")
        print(f"[INFO] API Key: {api_key}")
        print()
        
        # 步骤1：使用PyPDF2转换PDF为图像
        print("[步骤1] 转换PDF为图像...")
        images = convert_pdf_to_images_pypdf2(pdf_path, os.path.dirname(output_path))
        
        if not images:
            print("[X] 无法将PDF转换为图像")
            print("[提示] 请安装Poppler或使用其他方法先将PDF转换为图像")
            return False
        
        print(f"[OK] 成功转换 {len(images)} 页")
        print()
        
        # 步骤2：对每页进行OCR
        print("[步骤2] 开始OCR识别...")
        full_text = ""
        
        for i, img in enumerate(images, 1):
            print(f"[INFO] 处理第 {i}/{len(images)} 页...")
            
            # 保存临时图像
            temp_img_path = os.path.join(os.path.dirname(output_path), f"temp_page_{i}.png")
            img.save(temp_img_path, "PNG")
            
            # 调用OCR.space API
            text = extract_text_from_image_ocr_space(temp_img_path, api_key)
            
            if text:
                full_text += f"=== 第 {i} 页 ===\n\n"
                full_text += text + "\n\n"
                print(f"[OK] 第 {i} 页识别成功 ({len(text)} 字符)")
            else:
                print(f"[X] 第 {i} 页识别失败")
            
            # 删除临时图像
            try:
                os.remove(temp_img_path)
            except:
                pass
            
            # 避免API限流
            time.sleep(1)
        
        print()
        
        # 步骤3：保存结果
        print("[步骤3] 保存结果...")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"[OK] 处理完成!")
        print(f"[OK] 输出文件: {output_path}")
        print(f"[OK] 总字符数: {len(full_text)}")
        
        return True
        
    except Exception as e:
        print(f"[X] 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 3:
        print("=" * 60)
        print("OCR.space 在线OCR处理工具")
        print("=" * 60)
        print()
        print("使用方法:")
        print("  python OCR_space在线工具.py <PDF文件> <输出文件> [API_KEY]")
        print()
        print("参数说明:")
        print("  <PDF文件>   - 输入的PDF文件路径")
        print("  <输出文件>  - 输出的TXT文件路径")
        print("  [API_KEY]   - OCR.space API密钥（可选，默认使用测试密钥）")
        print()
        print("说明:")
        print("  - 此工具需要Poppler支持（用于PDF转图像）")
        print("  - 测试API密钥每天限制100次调用")
        print("  - 如需更多调用，请到 https://ocr.space 免费注册获取API密钥")
        print()
        sys.exit(0)
    
    pdf_file = sys.argv[1]
    output_file = sys.argv[2]
    api_key = sys.argv[3] if len(sys.argv) > 3 else "helloworld"
    
    if not os.path.exists(pdf_file):
        print(f"[X] PDF文件不存在: {pdf_file}")
        sys.exit(1)
    
    process_pdf_with_ocr_space(pdf_file, output_file, api_key)

if __name__ == "__main__":
    main()
