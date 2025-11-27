import jieba
from typing import List

# Pre-load user dict or stopwords if needed
_stopwords = None

def load_stopwords(path: str = None):
    global _stopwords
    s = set()
    if path:
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                w = ln.strip()
                if w:
                    s.add(w)
    _stopwords = s

def tokenize_chinese(text: str) -> List[str]:
    if not text:
        return []
    words = jieba.lcut(text)
    if _stopwords:
        words = [w for w in words if w.strip() and w not in _stopwords]
    else:
        words = [w for w in words if w.strip()]
    return words
