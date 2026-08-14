"""LINE Bot webhook 入口（FastAPI + line-bot-sdk v3）。"""
import logging

from fastapi import FastAPI, HTTPException, Request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app import config
from app.handlers import reply_for

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config.check()

app = FastAPI(title="LINE Bot")
line_config = Configuration(access_token=config.CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(config.CHANNEL_SECRET)


@app.get("/")
def health() -> dict:
    """健康檢查，也方便確認部署後服務有活著。"""
    return {"status": "ok"}


@app.post("/callback")
async def callback(request: Request) -> str:
    """LINE 平台的 webhook；簽章驗證失敗一律拒絕。"""
    signature = request.headers.get("X-Line-Signature", "")
    body = (await request.body()).decode("utf-8")

    try:
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning(
            "簽章驗證失敗：請確認 Render 的 LINE_CHANNEL_SECRET "
            "與 LINE Console「Basic settings」分頁的 Channel secret 完全一致"
        )
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"


@webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent) -> None:
    """收到文字訊息時回覆。"""
    answer = reply_for(event.message.text)
    with ApiClient(line_config) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=answer)],
            )
        )
