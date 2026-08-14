"""行程資料層。

目前實作是讀 data/events.json。整個查詢介面只有 load_events() 和
events_between()，之後要換成 Google Calendar 或資料庫，只要改這個檔案。
"""
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Taipei")
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "events.json"


@dataclass(frozen=True)
class Event:
    date: date
    title: str
    start: str = ""
    end: str = ""
    location: str = ""
    note: str = ""

    @property
    def time_label(self) -> str:
        """把起訖時間排成一段好讀的字串；沒有時間就算全天。"""
        if not self.start:
            return "全天"
        return f"{self.start}-{self.end}" if self.end else self.start

    def format_line(self) -> str:
        parts = [f"{self.time_label}　{self.title}"]
        if self.location:
            parts.append(f"　　📍{self.location}")
        if self.note:
            parts.append(f"　　📝{self.note}")
        return "\n".join(parts)


def today() -> date:
    """以台北時間為準的今天；Render 主機時區是 UTC，不能直接用 date.today()。"""
    return datetime.now(TZ).date()


def load_events(path: Path = DATA_FILE) -> list[Event]:
    """讀取全部行程，依日期與開始時間排序。"""
    if not path.exists():
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    events = [
        Event(
            date=date.fromisoformat(item["date"]),
            title=item["title"],
            start=item.get("start", ""),
            end=item.get("end", ""),
            location=item.get("location", ""),
            note=item.get("note", ""),
        )
        for item in raw.get("events", [])
    ]
    # 沒有時間的全天行程排在當天最前面
    return sorted(events, key=lambda e: (e.date, e.start or "00:00"))


def events_between(start: date, end: date, events: list[Event] | None = None) -> list[Event]:
    """取出 [start, end] 區間內的行程，含頭含尾。"""
    source = load_events() if events is None else events
    return [e for e in source if start <= e.date <= end]


def events_on(day: date, events: list[Event] | None = None) -> list[Event]:
    return events_between(day, day, events)
