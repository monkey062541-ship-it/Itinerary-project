from datetime import date

import pytest

from app.handlers import (
    GREETING_REPLY,
    parse_explicit_date,
    HELP_TEXT,
    normalize,
    reply_for,
    resolve_range,
    week_range,
)
from app.schedule import Event

# 2026-08-14 是星期五
ANCHOR = date(2026, 8, 14)

EVENTS = [
    Event(date=date(2026, 8, 14), title="專案週會", start="09:30", end="11:00", location="會議室 A"),
    Event(date=date(2026, 8, 14), title="客戶提案", start="14:00", end="15:30"),
    Event(date=date(2026, 8, 15), title="健檢", start="10:00", end="12:00", note="禁食"),
    Event(date=date(2026, 8, 17), title="報告截止日"),
    Event(date=date(2026, 8, 20), title="台中出差", start="08:00", end="21:00"),
]


def ask(text: str) -> str:
    return reply_for(text, anchor=ANCHOR, events=EVENTS)


def test_help():
    assert ask("說明") == HELP_TEXT
    assert ask("help") == HELP_TEXT


@pytest.mark.parametrize(
    "phrasing", ["哈囉", "哈囉！", "哈囉~", " 哈囉 ", "嗨", "安安", "你好", "Hello", "hi"]
)
def test_greetings(phrasing):
    assert ask(phrasing) == GREETING_REPLY


def test_today_lists_both_events():
    answer = ask("今天行程")
    assert "專案週會" in answer
    assert "客戶提案" in answer
    assert "健檢" not in answer


@pytest.mark.parametrize("phrasing", ["今天行程", "今天有什麼行程？", "今日", "查一下今天的行程"])
def test_today_phrasings_all_work(phrasing):
    assert "專案週會" in ask(phrasing)


def test_tomorrow_and_day_after():
    assert "健檢" in ask("明天行程")
    assert "沒有安排" in ask("後天行程")


def test_all_day_event_shows_as_all_day():
    assert "全天　報告截止日" in ask("8/17")


def test_week_groups_by_date():
    # 8/14 是週五，本週 = 8/10~8/16
    answer = ask("本週行程")
    assert "專案週會" in answer and "健檢" in answer
    assert "報告截止日" not in answer  # 8/17 是下週一
    assert "▍08/14（五）" in answer


def test_next_week():
    # 下週 = 8/17~8/23
    answer = ask("下週行程")
    assert "報告截止日" in answer and "台中出差" in answer
    assert "專案週會" not in answer


def test_upcoming_seven_days():
    # 未來七天 = 8/14~8/20，剛好含到 8/20
    answer = ask("最近行程")
    assert "健檢" in answer and "台中出差" in answer


def test_all_events():
    answer = ask("全部行程")
    assert all(name in answer for name in ("專案週會", "健檢", "報告截止日", "台中出差"))


@pytest.mark.parametrize("token", ["2026-08-15", "8/15", "8月15日"])
def test_explicit_date_formats(token):
    assert "健檢" in ask(token)


def test_invalid_date_stays_silent():
    assert ask("2/30") is None


@pytest.mark.parametrize(
    "chatter",
    ["幫我訂機票", "好啊那就這樣", "晚上要吃什麼", "哈哈哈", "明天記得帶傘", "ok", "👍"],
)
def test_unmatched_messages_stay_silent(chatter):
    """群組裡的一般對話不該被回應。"""
    assert ask(chatter) is None


def test_empty_day_still_replies():
    """命中關鍵詞但當天沒事，仍要回應，不能靜默。"""
    assert "沒有安排" in ask("8/18")


def test_normalize_strips_filler():
    assert normalize("今天的行程有哪些？") == "今天"


def test_week_range_is_monday_to_sunday():
    start, end = week_range(ANCHOR)
    assert (start, end) == (date(2026, 8, 10), date(2026, 8, 16))


def test_resolve_range_unknown():
    assert resolve_range("隨便打字", ANCHOR) is None


# --- 只寫月日時的年份推算（今天固定為 2026-08-14）---


@pytest.mark.parametrize(
    "token, expected",
    [
        ("8/15", date(2026, 8, 15)),   # 今年還沒到 → 今年
        ("8/14", date(2026, 8, 14)),   # 就是今天 → 今年
        ("3/27", date(2027, 3, 27)),   # 今年已經過了 → 明年
        ("3月27日", date(2027, 3, 27)),
        ("8/13", date(2027, 8, 13)),   # 昨天也算已經過了
    ],
)
def test_month_day_rolls_to_next_year_when_past(token, expected):
    assert parse_explicit_date(token, ANCHOR) == expected


@pytest.mark.parametrize(
    "token, expected",
    [
        ("2026-03-27", date(2026, 3, 27)),  # 寫了年份就照寫的算，不推算
        ("2027-03-27", date(2027, 3, 27)),
    ],
)
def test_explicit_year_is_respected(token, expected):
    assert parse_explicit_date(token, ANCHOR) == expected


def test_impossible_date_returns_none():
    assert parse_explicit_date("2/30", ANCHOR) is None
