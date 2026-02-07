# -*- coding: utf-8 -*-
"""
CxM Kaohsiung 票況監控（GitHub Actions 版，可 fork 範例）
- 每 1 分鐘檢查 tixcraft 三個售票頁面
- 偵測指定區域若未顯示「售罄字樣」則視為可能可買
- 用 LINE Notify 通知
- 使用 actions/cache 保存上次通知的雜湊，避免重複通知
"""

import os
import re
import hashlib
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple

URLS = [
    "https://tixcraft.com/ticket/area/26_cxm/21777",
    "https://tixcraft.com/ticket/area/26_cxm/21671",
    "https://tixcraft.com/ticket/area/26_cxm/21672",
]

KEYWORDS = [
    "6880站區",
    "6280站區",
    "6880看台區",
    "6280看台區",
    "5880看台區",
    "4880看台區",
    "3880看台區",
]

# 可能的售罄字樣（可再自行擴充）
SELL_PATTERNS = ["已售完", "暫無票券", "尚未開賣", "Soldout", "Sold Out", "SOLD OUT"]

# 近鄰檢查的字元長度
TAIL_LEN = 80

# GitHub Secrets 會注入的變數
LINE_TOKEN = os.getenv("LINE_TOKEN", "")

# 用來和 actions/cache 搭配的檔案
STATE_DIR = ".state"
LAST_HASH_FILE = os.path.join(STATE_DIR, "last_notified.hash")


def fetch(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "zh-TW,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text("", strip=True)
    text = re.sub(r"\s+", "", text)
    return text


def is_sold_out_tail(tail: str) -> bool:
    t = tail.lower()
    return any(p.lower().replace(" ", "") in t for p in SELL_PATTERNS)


def probe(text: str, keywords: List[str]) -> List[str]:
    """
    對每個關鍵字：
    - 只要頁面出現該關鍵字
    - 且該關鍵字後 0~TAIL_LEN 內容中「沒有」售罄字樣
    => 視為「可能可買」
    """
    available = []
    for kw in keywords:
        matches = list(re.finditer(re.escape(kw), text))
        if not matches:
            continue
        can_buy = False
        for m in matches:
            tail = text[m.end(): m.end() + TAIL_LEN]
            if not is_sold_out_tail(tail):
                can_buy = True
                break
        if can_buy:
            available.append(kw)
    return sorted(set(available))


def build_summary(found: List[Tuple[str, List[str]]]) -> str:
    msg = "🎫 CxM Kaohsiung 有票啦！\n\n"
    for url, a in found:
        msg += f"{url}\n可買：{', '.join(a)}\n\n"
    return msg.strip()


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def load_last_hash() -> str:
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        if os.path.exists(LAST_HASH_FILE):
            with open(LAST_HASH_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""


def save_last_hash(h: str):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(LAST_HASH_FILE, "w", encoding="utf-8") as f:
            f.write(h)
    except Exception:
        pass


def notify_line(message: str):
    token = LINE_TOKEN.strip()
    if not token:
        print("WARN: LINE_TOKEN is empty, skip LINE Notify.")
        return
    try:
        r = requests.post(
            "https://notify-api.line.me/api/notify",
            headers={"Authorization": f"Bearer {token}"},
            data={"message": message},
            timeout=15,
        )
        r.raise_for_status()
    except Exception as e:
        print(f"ERROR: LINE Notify failed: {e}")


def main():
    results = []

    for url in URLS:
        try:
            html = fetch(url)
            text = extract_text(html)
            avail = probe(text, KEYWORDS)
            if avail:
                results.append((url, avail))
        except Exception as e:
            print(f"ERROR: fetch/probe failed for {url}: {e}")

    if not results:
        print("No available tickets this round.")
        return

    msg = build_summary(results)
    current_hash = sha1(msg)
    last_hash = load_last_hash()

    if current_hash == last_hash:
        print("Same availability as last notification. Skip notifying.")
        return

    notify_line(msg)
    save_last_hash(current_hash)
    print(msg)


if __name__ == "__main__":
    main()
