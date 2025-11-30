import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from wordfreq_cn import extract_keywords_tfidf, generate_trend_wordcloud

from ..config import settings
from ..utils.cleaner import clean_html

executor = ThreadPoolExecutor(max_workers=2)


# Helper to fetch documents from DB
async def docs_to_corpus(rows: list[dict[str, Any]]) -> list[str]:
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


def compute_tfidf_top(corpus: list[str], top_n: int = 50, max_features: int = None):
    result = extract_keywords_tfidf(corpus, top_k=top_n, max_features=max_features)
    return [{"term": kws.word, "score": kws.weight} for kws in result.keywords]


def generate_wordcloud(
    corpus: list[str], out_path: str, max_words: int = 200
) -> list[str]:
    return generate_trend_wordcloud(corpus, output_dir=out_path, max_words=max_words)


# Public coroutine wrappers
import asyncio


async def async_tfidf_top(corpus: list[str], top_n: int = 50, max_features: int = None):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, compute_tfidf_top, corpus, top_n, max_features
    )


async def async_generate_wordcloud(corpus: list[str], filename: str):
    out_path = os.path.join(settings.WORDCLOUD_DIR, filename)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, generate_wordcloud, corpus, out_path)
