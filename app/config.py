"""環境設定：從 .env 讀取 LINE 憑證。"""
import os

from dotenv import load_dotenv

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
PORT = int(os.getenv("PORT", "8000"))


def check() -> None:
    """啟動前檢查必要環境變數，缺少就直接報錯，避免上線後才發現。"""
    missing = [
        name
        for name, value in (
            ("LINE_CHANNEL_ACCESS_TOKEN", CHANNEL_ACCESS_TOKEN),
            ("LINE_CHANNEL_SECRET", CHANNEL_SECRET),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "缺少環境變數：" + "、".join(missing) + "\n請複製 .env.example 成 .env 並填入憑證。"
        )
