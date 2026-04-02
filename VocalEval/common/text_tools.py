from __future__ import annotations

import re
from typing import Optional


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def char_tokens(text: str) -> list[str]:
    norm = normalize_text(text)
    return [ch for ch in norm if not ch.isspace()]


def word_tokens(text: str) -> list[str]:
    norm = normalize_text(text)
    return norm.split()


def edit_distance(a: list[str], b: list[str]) -> int:
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        dp[i][0] = i
    for j in range(len(b) + 1):
        dp[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return dp[-1][-1]


def wer(ref: str, hyp: str) -> Optional[float]:
    ref_tokens = word_tokens(ref)
    hyp_tokens = word_tokens(hyp)
    if not ref_tokens:
        return None
    return edit_distance(ref_tokens, hyp_tokens) / len(ref_tokens)


def cer(ref: str, hyp: str) -> Optional[float]:
    ref_tokens = char_tokens(ref)
    hyp_tokens = char_tokens(hyp)
    if not ref_tokens:
        return None
    return edit_distance(ref_tokens, hyp_tokens) / len(ref_tokens)
