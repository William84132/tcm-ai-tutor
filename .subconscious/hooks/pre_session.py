"""
pre_session — 会话开始钩子

从 whisper_package 读取预注入包，输出到 stdout（自动注入主会话）。
如果无内容或不处于 whisper 模式，不输出任何东西。
"""
import sys, pathlib, os

# 把项目根加入路径
root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from memory.storage import Storage
from core.whisper import WhisperSystem

MODE = os.environ.get("SUBCONSCIOUS_MODE", "whisper").strip().lower()
if MODE == "off":
    sys.exit(0)

storage = Storage()
pkg = storage.load_whisper_package()

ws = WhisperSystem(pkg=pkg)
output = ws.get_injection()

if output:
    # 输出到 stdout → Claude Code 自动注入为系统消息
    print(output)
    # 发送过的包清掉，避免下次重复
    storage.clear_whisper_package()
