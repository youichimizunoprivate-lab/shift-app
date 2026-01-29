#!/bin/bash

# このファイルの場所へ移動
cd "$(dirname "$0")"
export LC_ALL=ja_JP.UTF-8
export LANG=ja_JP.UTF-8

# Googleドライブへの大量同期を防ぐため、仮想環境をホームディレクトリ（同期対象外）に作成・移動
VENV_DIR="$HOME/.shift_app_venv"

echo "起動準備中..."

# 仮想環境がなければ作成
if [ ! -d "$VENV_DIR" ]; then
    echo "初回セットアップを行っています...（数分かかります）"
    # python3コマンドの確認
    if ! command -v python3 &> /dev/null; then
        echo "エラー: Python3が見つかりませんでした。インストールしてください。"
        exit 1
    fi
    python3 -m venv "$VENV_DIR"
fi

# 仮想環境を有効化
source "$VENV_DIR/bin/activate"

# 必要なライブラリのインストール
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# デスクトップに残っている古い仮想環境フォルダ（同期の原因）があれば削除
if [ -d ".venv" ]; then
    echo "Googleドライブの同期を止めるため、古い設定ファイル(.venv)を削除しています..."
    rm -rf ".venv"
    echo "削除完了。"
fi

# アプリ起動
streamlit run app.py