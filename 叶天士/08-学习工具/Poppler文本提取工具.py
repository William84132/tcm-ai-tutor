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

import subprocess

# Poppler路径配置
POPPLER_BIN = _CFG.get('poppler_bin', '')
PDFTOTEXT = os.path.join(POPPLER_BIN, "pdftotext.exe")

def extract_text_with_pdftotext(pdf_path, output_path):
    """使用pdftotext提取PDF文本"""
    try:
        # 检查pdftotext是否存在
        if not os.path.exists(PDFTOTEXT):
            print(f"[X] pdftotext.exe 不存在: {PDFTOTEXT}")
            return False

        # 执行pdftotext命令
        # -layout: 保持布局
        # -enc UTF-8: 指定编码
        cmd = [
            PDFTOTEXT,
            "-layout",
            "-enc", "UTF-8",
            pdf_path,
            output_path
        ]

        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            # 检查输出文件
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"[OK] 文本提取成功!")
                print(f"[OK] 输出文件: {output_path}")
                print(f"[OK] 文件大小: {file_size / 1024:.2f} KB")
                return True
            else:
                print(f"[X] 输出文件未生成")
                return False
        else:
            print(f"[X] pdftotext执行失败")
            print(f"错误代码: {result.returncode}")
            print(f"标准错误: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"[X] 命令执行超时")
        return False
    except Exception as e:
        print(f"[X] 发生错误: {e}")
        return False

def check_poppler():
    """检查Poppler安装"""
    print("=" * 60)
    print("Poppler安装检查")
    print("=" * 60)

    # 检查bin目录
    bin_exists = os.path.exists(POPPLER_BIN)
    print(f"Poppler bin目录: {'OK' if bin_exists else 'X'} {POPPLER_BIN}")

    # 检查pdftotext
    pdfextract_exists = os.path.exists(PDFTOTEXT)
    print(f"pdftotext.exe: {'OK' if pdfextract_exists else 'X'}")

    # 尝试运行pdftotext --version
    if pdfextract_exists:
        try:
            result = subprocess.run(
                [PDFTOTEXT, "--version"],
                capture_output=True,
                text=True
            )
            print(f"pdftotext版本: {result.stdout.strip()}")
        except Exception as e:
            print(f"版本检查失败: {e}")

    print("=" * 60)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            check_poppler()
        else:
            # 处理PDF
            pdf_path = sys.argv[1]
            output_path = sys.argv[2] if len(sys.argv) > 2 else pdf_path.replace('.pdf', '.txt')

            print(f"=" * 60)
            print(f"PDF文本提取工具 (pdftotext)")
            print(f"=" * 60)
            print(f"输入PDF: {pdf_path}")

            extract_text_with_pdftotext(pdf_path, output_path)
    else:
        print("使用方法:")
        print("  python Poppler文本提取工具.py --check")
        print("  python Poppler文本提取工具.py <pdf文件> [输出文件]")
