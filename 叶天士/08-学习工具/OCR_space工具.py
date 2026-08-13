import os
import sys
import base64
import requests
import time

def check_pdf_text_layer(pdf_path):
    """检查PDF是否包含可提取的文本层"""
    try:
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            total_chars = 0
            sample_texts = []
            
            for i, page in enumerate(pdf.pages[:3]):  # 只检查前3页
                text = page.extract_text()
                if text:
                    total_chars += len(text)
                    if len(sample_texts) < 3:
                        sample_texts.append(text[:200])
            
            if total_chars > 100:
                print(f"[OK] PDF包含文本层，可直接提取")
                print(f"[INFO] 前3页字符数: {total_chars}")
                return True, sample_texts
            
        print("[X] PDF为扫描版，没有可提取的文本")
        return False, []
        
    except ImportError:
        print("[X] pdfplumber未安装")
        return None, []
    except Exception as e:
        print(f"[X] 检查PDF失败: {e}")
        return None, []

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
        
        headers = {"apikey": api_key}
        
        response = requests.post(
            "https://api.ocr.space/parse/image",
            data=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("IsErroredOnProcessing"):
                return None
            
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                return parsed_results[0].get("ParsedText", "")
        
        return None
        
    except Exception as e:
        print(f"[X] API调用失败: {e}")
        return None

def process_scanned_pdf_with_images(image_folder, output_path, api_key="helloworld"):
    """处理图像文件夹中的图片"""
    try:
        # 获取所有PNG/JPG文件
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp']:
            image_files.extend([f for f in os.listdir(image_folder) if f.lower().endswith(ext.split('.')[1])])
        
        image_files = sorted(image_files)
        
        if not image_files:
            print("[X] 图像文件夹为空")
            return False
        
        print(f"[INFO] 找到 {len(image_files)} 张图片")
        print()
        
        full_text = ""
        
        for i, img_file in enumerate(image_files, 1):
            img_path = os.path.join(image_folder, img_file)
            print(f"[INFO] 处理第 {i}/{len(image_files)} 张图片: {img_file}")
            
            text = extract_text_from_image_ocr_space(img_path, api_key)
            
            if text:
                full_text += f"=== 第 {i} 页 ===\n\n"
                full_text += text + "\n\n"
                print(f"[OK] 识别成功 ({len(text)} 字符)")
            else:
                print(f"[X] 识别失败")
            
            time.sleep(1)  # 避免API限流
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print()
        print(f"[OK] 处理完成!")
        print(f"[OK] 输出文件: {output_path}")
        print(f"[OK] 总字符数: {len(full_text)}")
        
        return True
        
    except Exception as e:
        print(f"[X] 处理失败: {e}")
        return False

def main():
    print("=" * 60)
    print("OCR.space 在线OCR工具")
    print("=" * 60)
    print()
    print("使用方法:")
    print()
    print("选项1 - 处理图像文件夹:")
    print("  python OCR_space工具.py images <图像文件夹> <输出文件>")
    print("  示例: python OCR_space工具.py images \"E:\\PDF图片\" output.txt")
    print()
    print("选项2 - 检查PDF是否有文本:")
    print("  python OCR_space工具.py check <PDF文件>")
    print()
    print("说明:")
    print("  - 此工具使用OCR.space免费API")
    print("  - 测试API每天限制100次调用")
    print("  - 如需更多调用，请到 https://ocr.space 免费注册")
    print()
    
    if len(sys.argv) < 3:
        print("=" * 60)
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "images":
        image_folder = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else "output.txt"
        api_key = sys.argv[4] if len(sys.argv) > 4 else "helloworld"
        
        if not os.path.exists(image_folder):
            print(f"[X] 图像文件夹不存在: {image_folder}")
            sys.exit(1)
        
        process_scanned_pdf_with_images(image_folder, output_file, api_key)
    
    elif command == "check":
        pdf_file = sys.argv[2]
        
        if not os.path.exists(pdf_file):
            print(f"[X] PDF文件不存在: {pdf_file}")
            sys.exit(1)
        
        print(f"[INFO] 检查PDF: {pdf_file}")
        has_text, samples = check_pdf_text_layer(pdf_file)
        
        if samples:
            print()
            print("[样本文本预览]")
            print("-" * 60)
            for i, sample in enumerate(samples, 1):
                print(f"第{i}页: {sample[:100]}...")
    
    else:
        print(f"[X] 未知命令: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
