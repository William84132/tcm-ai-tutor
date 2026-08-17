#!/bin/bash
# pre_session — 会话开始时注入潜意识 whisper
cd "$(dirname "$0")/../.."  # 切到项目根 (subconscious 目录)
python .subconscious/hooks/pre_session.py 2>/dev/null
