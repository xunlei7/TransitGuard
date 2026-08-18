# 使用确定性的字符串规则和正则表达式，把用户自然语言转换成标准的 ParsedQuestion

from __future__ import annotations

import re

from .domain import Intent, ParsedQuestion

# frozenset 是不可修改的集合，适合保存固定配置
# 1234567ACEBDFMGJZLNQRW 是定义支持的地铁线路
SUBWAY_ROUTES = frozenset("1234567ACEBDFMGJZLNQRW")

# 提取数字线路： \b 是单词边界，(?:) 是非捕获组，? 是可选，\s* 是空格 0 次或多次，re.IGNORECASE 忽略大小写
_NUMBERED_ROUTE = re.compile(r"\b([1-7])(?:\s*(?:train|line))?\b", re.IGNORECASE)

# 提取字母线路
_LETTERED_ROUTE = re.compile(
    r"\b([ACEBDFMGJZLNQRW])\s+(?:train|line)\b",
    re.IGNORECASE,
)
_STOP_ID = re.compile(r"\bstop\s*(?:id\s*)?([A-Z0-9]{2,5}[NS]?)\b", re.IGNORECASE)

_ARRIVAL_TERMS = (
    "next train",
    "next arrival",
    "arrive",
    "arrival",
    "how long",
    "when is",
)
_STATUS_TERMS = (
    "delay",
    "delayed",
    "running",
    "service",
    "status",
    "suspended",
    "closure",
)


def _extract_route(text: str) -> str | None:
    for pattern in (_NUMBERED_ROUTE, _LETTERED_ROUTE):
        match = pattern.search(text)
        if match:
            raw_route = match.group(1)
            route = raw_route.upper()
            # A lowercase "a train" is ordinary English and cannot safely be
            # assumed to mean the A subway line. "A train" and "the a train"
            # remain unambiguous enough for this constrained parser.
            if raw_route == "a" and not text[:match.start()].rstrip().lower().endswith("the"):
                continue
            if route in SUBWAY_ROUTES:
                return route
    return None

# 这里的 * 表示它后面的参数必须使用参数名传递
def parse_question(text: str, *, stop_id: str | None = None) -> ParsedQuestion:
    clean = " ".join(str(text or "").strip().split())
    lowered = clean.lower()
    route_id = _extract_route(clean)
    stop_match = _STOP_ID.search(clean)
    parsed_stop_id = (stop_id or (stop_match.group(1) if stop_match else "")).upper() or None

    if any(term in lowered for term in _ARRIVAL_TERMS):
        return ParsedQuestion(clean, Intent.NEXT_ARRIVAL, route_id, parsed_stop_id)

    if any(term in lowered for term in _STATUS_TERMS):
        return ParsedQuestion(clean, Intent.SERVICE_STATUS, route_id, parsed_stop_id)

    return ParsedQuestion(
        clean,
        Intent.UNSUPPORTED,
        route_id,
        parsed_stop_id,
        "Only subway service-status and next-arrival questions are supported.",
    )
