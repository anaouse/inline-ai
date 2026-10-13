#!/usr/bin/env bash
# 打包为无控制台窗口的 Windows exe，输出到 dist/inline-ai.exe
set -euo pipefail
cd "$(dirname "$0")"

NAME="inline-ai"
BUILD_DIR="build"

mkdir -p "$BUILD_DIR"

# pyinstaller 按 spec 文件所在目录解析图标路径，这里统一传绝对路径。
ICON_PATH="$PWD/$BUILD_DIR/$NAME.ico"
if command -v cygpath >/dev/null 2>&1; then
    ICON_PATH="$(cygpath -w "$ICON_PATH")"
fi

echo "==> 生成图标"
uv run python - "$BUILD_DIR/$NAME.ico" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, "src")
from inline_ai.icon import make_icon

target = Path(sys.argv[1])
make_icon(256).save(
    target, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
)
print(f"图标已写入 {target}")
PY

echo "==> 打包 exe"
uv run pyinstaller \
    --noconfirm \
    --clean \
    --onefile \
    --windowed \
    --name "$NAME" \
    --icon "$ICON_PATH" \
    --paths src \
    --collect-all pynput \
    --collect-submodules pystray \
    --hidden-import pystray._win32 \
    --distpath dist \
    --workpath "$BUILD_DIR/work" \
    --specpath "$BUILD_DIR" \
    src/inline_ai/main.py

echo "==> 完成：dist/$NAME.exe"
echo "把 .env 放在 exe 同目录，双击运行后通过托盘图标右键退出。"
