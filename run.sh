#!/bin/bash


set -e


PROJECT_ROOT=$(dirname "$(realpath "$0")")
SRC_DIR="$PROJECT_ROOT/src"
VENV_DIR="$PROJECT_ROOT/venv"
MAIN_SCRIPT="$SRC_DIR/main_ui.py"

if [ ! -d "$VENV_DIR" ]; then
  echo "创建虚拟环境..."
  python3 -m venv "$VENV_DIR"
fi


echo "激活虚拟环境..."
source "$VENV_DIR/Scripts/activate"


if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
  echo "安装依赖..."
  pip install -r "$PROJECT_ROOT/requirements.txt"
fi

playwright install

echo "运行主程序..."
python "$MAIN_SCRIPT"


deactivate

echo "程序已结束。"