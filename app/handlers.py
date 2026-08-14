"""訊息處理邏輯。

刻意不依賴 LINE SDK，維持成純函式：輸入一段文字，輸出要回覆的文字。
這樣可以直接單元測試，之後換平台或加 AI 也只動這一層。
"""
import re
from datetime import date, timedelta

from app.schedule import Event, events_between, load_events, today

HELP_TEXT = (
    "我可以幫你查行程，試試看：\n"
    "・今天行程\n"
    "・明天行程 / 後天行程\n"
    "・本週行程 / 下週行程\n"
    "・最近行程（未來七天）\n"
    "・全部行程\n"
    "・8/20（直接輸入日期查那天）\n"
    "・說明"
)

# 打招呼用語，一律回同一句問候
GREETINGS = ("哈囉", "哈嘍", "嗨", "安安", "你好", "妳好", "hello", "hi", "hey")
GREETING_REPLY = "你今天還好嗎？"

# 使用者常會加上的語助詞，比對前先拿掉，讓「今天行程有哪些？」也能命中
NOISE_PATTERN = re.compile(r"(行程|安排|計畫|的|我|有|哪些|什麼|甚麼|嗎|呢|請問|查|看|一下|[?？!！。，,、~～\s])")

DATE_PATTERNS = (
    re.compile(r"^(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$"),
    re.compile(r"^(?P<month>\d{1,2})[/-](?P<day>\d{1,2})$"),
    re.compile(r"^(?P<month>\d{1,2})月(?P<day>\d{1,2})[日號]?$"),
)


def normalize(text: str) -> str:
    return NOISE_PATTERN.sub("", text.strip())


def week_range(anchor: date, offset_weeks: int = 0) -> tuple[date, date]:
    """回傳 anchor 所在那一週（週一到週日）的起訖日。"""
    monday = anchor - timedelta(days=anchor.weekday()) + timedelta(weeks=offset_weeks)
    return monday, monday + timedelta(days=6)


def parse_explicit_date(token: str, anchor: date) -> date | None:
    """解析 2026-08-20 / 8/20 / 8月20日 三種寫法；沒寫年份就用今年。"""
    for pattern in DATE_PATTERNS:
        matched = pattern.match(token)
        if not matched:
            continue
        groups = matched.groupdict()
        year = int(groups.get("year") or anchor.year)
        try:
            return date(year, int(groups["month"]), int(groups["day"]))
        except ValueError:  # 例如 2/30 這種不存在的日期
            return None
    return None


def resolve_range(text: str, anchor: date) -> tuple[str, date, date] | None:
    """把使用者的說法轉成 (標題, 起日, 迄日)；認不出來就回 None。"""
    token = normalize(text)

    relative_days = {
        "今天": 0, "今日": 0, "today": 0,
        "明天": 1, "明日": 1, "tomorrow": 1,
        "後天": 2,
        "昨天": -1, "昨日": -1,
    }
    if token in relative_days:
        day = anchor + timedelta(days=relative_days[token])
        return f"{day:%m/%d}（{'一二三四五六日'[day.weekday()]}）", day, day

    if token in ("本週", "這週", "本周", "這周"):
        start, end = week_range(anchor)
        return "本週", start, end

    if token in ("下週", "下周"):
        start, end = week_range(anchor, offset_weeks=1)
        return "下週", start, end

    if token in ("最近", "接下來", "未來"):
        return "未來七天", anchor, anchor + timedelta(days=6)

    if token in ("全部", "所有", "全"):
        return "全部", date.min, date.max

    explicit = parse_explicit_date(token, anchor)
    if explicit:
        return f"{explicit:%Y/%m/%d}", explicit, explicit

    return None


def format_events(title: str, events: list[Event]) -> str:
    """把行程排成回覆訊息；跨日的查詢會依日期分段。"""
    if not events:
        return f"【{title}】\n沒有安排，可以休息一下 🎉"

    lines = [f"【{title}行程】"]
    multi_day = len({e.date for e in events}) > 1
    current: date | None = None

    for event in events:
        if multi_day and event.date != current:
            current = event.date
            weekday = "一二三四五六日"[event.date.weekday()]
            lines.append(f"\n▍{event.date:%m/%d}（{weekday}）")
        lines.append(event.format_line())

    return "\n".join(lines)


def reply_for(text: str, anchor: date | None = None, events: list[Event] | None = None) -> str:
    """依使用者輸入決定回覆內容。anchor 與 events 可注入，方便測試。"""
    message = text.strip()
    anchor = anchor or today()

    token = normalize(message)

    if token in ("說明", "help", "Help", "指令", ""):
        return HELP_TEXT

    if token.lower() in GREETINGS:
        return GREETING_REPLY

    resolved = resolve_range(message, anchor)
    if resolved is None:
        return f"看不懂「{message}」😅\n\n{HELP_TEXT}"

    title, start, end = resolved
    source = load_events() if events is None else events
    return format_events(title, events_between(start, end, source))
