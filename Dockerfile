FROM python:3.12-slim

# 不寫 .pyc、log 直接輸出不緩衝，這樣 Render 的 Logs 才看得到即時訊息
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 先只複製 requirements，套件沒變動時可以直接重用快取層，部署會快很多
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render 用 $PORT 指定要監聽的埠號；本機直接跑就退回 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
