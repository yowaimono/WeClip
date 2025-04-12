#!/bin/bash

set -e

PROJECT_ROOT=$(dirname "$(realpath "$0")")
BUILD_DIR="$PROJECT_ROOT/build"
SRC_DIR="$PROJECT_ROOT/src"
MAIN_UI_FILE="$SRC_DIR/main_ui.py"
APP_UI_DIR="$PROJECT_ROOT/app/ui"
WX_UI_FILE="$APP_UI_DIR/wx_ui.ui"
WX_UI_PY_OUTPUT="$BUILD_DIR/wx_ui.py"
DIST_DIR="$BUILD_DIR/dist"
BUILD_PYINSTALLER="$BUILD_DIR/pyinstaller_build"
PLAYWRIGHT_DRIVER_DIR="$PROJECT_ROOT/venv/Lib/site-packages/playwright/driver"

echo "开始打包成 EXE..."

# 确保 build 目录存在
mkdir -p "$BUILD_DIR"
mkdir -p "$BUILD_PYINSTALLER"
mkdir -p "$DIST_DIR"

# 处理 UI 文件
if [ -f "$WX_UI_FILE" ]; then
  echo "编译 UI 文件: $WX_UI_FILE -> $WX_UI_PY_OUTPUT"
  python -m PyQt5.uic.pyuic "$WX_UI_FILE" -o "$WX_UI_PY_OUTPUT"
fi

echo "安装 Playwright 浏览器驱动..."
source "$PROJECT_ROOT/venv/Scripts/activate"
playwright install
deactivate

echo "复制 Playwright 驱动文件..."
mkdir -p "$BUILD_DIR/playwright/driver"
cp -r "$PLAYWRIGHT_DRIVER_DIR" "$BUILD_DIR/playwright/"

echo "使用 PyInstaller 打包..."
"$PROJECT_ROOT/venv/Scripts/pyinstaller" \
  --onefile \
  --windowed \
  --name "WeChatArticleDownloader" \
  --distpath "$DIST_DIR" \
  --specpath "$DIST_DIR" \
  --workpath "$BUILD_PYINSTALLER" \
  --add-data "$BUILD_DIR/playwright/driver;playwright/driver" \
  --hidden-import="playwright._impl._pyinstaller" \
  --hidden-import="sqlite3" \
  --additional-hooks-dir="$PROJECT_ROOT/hooks" \
  "$MAIN_UI_FILE"

echo "打包完成，EXE 文件位于: $DIST_DIR/WeChatArticleDownloader.exe"