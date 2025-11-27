import os
import io
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
from datetime import date
from ..config import settings
from ..utils.cleaner import clean_html
from ..utils.tokenizer import tokenize_chinese

executor = ThreadPoolExecutor(max_workers=2)

# Helper to fetch documents from DB: will be called in router with session
async def docs_to_corpus(rows: List[Dict[str, Any]]) -> List[str]:
    # Each row expected to have 'data' JSON with title/extra etc.
    corpus = []
    for r in rows:
        data = r.get("data") or {}
        for item in data.get("items", []):
            title = item.get("title", "") if isinstance(item, dict) else ""
            hover = ""
            if isinstance(item, dict):
                extra = item.get("extra", {})
                # try multiple fields
                hover = extra.get("hover", "") if isinstance(extra, dict) else ""
            text = f"{title} {hover}"
            text = clean_html(text)
            corpus.append(text)
    return corpus

def _chinese_tokenizer_for_tfidf(text: str):
    # returns list of tokens or a string (scikit-learn expects callable that returns iterable)
    return tokenize_chinese(text)

def compute_tfidf_top(corpus: List[str], top_n: int = 50, max_features: int = None):
    # run in threadpool (blocking)
    max_features = max_features or settings.TFIDF_MAX_FEATURES
    vect = TfidfVectorizer(
        tokenizer=_chinese_tokenizer_for_tfidf,
        max_features=max_features,
        token_pattern=None  # disable default token pattern because we're using tokenizer
    )
    X = vect.fit_transform(corpus)
    names = vect.get_feature_names_out()
    # compute mean tf-idf across docs and take top_n
    import numpy as np
    scores = X.mean(axis=0).A1  # average tf-idf across documents
    idx = (-scores).argsort()[:top_n]
    return [{"term": names[i], "score": float(scores[i])} for i in idx]

def generate_wordcloud(corpus: List[str], out_path: str, max_words: int = 200):
    text = " ".join([" ".join(tokenize_chinese(t)) for t in corpus])
    if not os.path.exists(os.path.dirname(out_path)):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
    wc = WordCloud(font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                   width=1200, height=600, max_words=max_words)
    wc.generate(text)
    wc.to_file(out_path)
    return out_path

# Public coroutine wrappers
import asyncio

async def async_tfidf_top(corpus: List[str], top_n: int = 50, max_features: int = None):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, compute_tfidf_top, corpus, top_n, max_features)

async def async_generate_wordcloud(corpus: List[str], filename: str):
    out_path = os.path.join(settings.WORDCLOUD_DIR, filename)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, generate_wordcloud, corpus, out_path)
