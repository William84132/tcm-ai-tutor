#!/bin/bash
# post_session — 会话结束后执行潜意识维护
cd "$(dirname "$0")/../.."
python .subconscious/hooks/post_session.py 2>/dev/null
