import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from wordfreq_cn import generate_trend_wordcloud, extract_keywords_tfidf_per_doc

from ..config import settings
from ..dao import NewsKeywordsDTO
from ..utils.cleaner import clean_html

executor = ThreadPoolExecutor(max_workers=2)


# Helper to fetch documents from DB
async def docs_to_corpus(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    from collections import defaultdict

    corpus = defaultdict(list)  # 自动初始化不存在的键
    for r in rows:
        data = r.get("data", {})
        news_date = r.get("news_date", "")

        for item in data.get("items", []):
            title = item.get("title", "") if isinstance(item, dict) else ""
            hover = ""
            if isinstance(item, dict):
                extra = item.get("extra", {})
                hover = extra.get("hover", "") if isinstance(extra, dict) else ""

            text = f"{title} {hover}"
            text = clean_html(text)

            # 直接添加到对应日期的列表中
            corpus[news_date].append(text)
    return corpus


def compute_tfidf_top(
        corpus: list[dict],
        top_n: int = 5,
        max_features: int = None
):
    """
    对每条新闻提取 top_n 关键词（per-document TF-IDF）。
    依赖 extract_keywords_tfidf 返回的:
        - vectorizer
        - matrix (n_docs x n_features)
        - feature_names
    """
    if not corpus:
        return []

    # 1. 提取文本（content 为空时使用 title）
    news_ids = [item.get("id", "") for item in corpus]

    texts = [
        ((item.get("content") or "").strip() or item.get("title", "")).strip()
        for item in corpus
    ]

    # 避免空文本导致 vectorizer 报错
    texts = [t if t else " " for t in texts]

    # 2. 每篇新闻 top_n 的 TF-IDF
    per_doc_keywords = extract_keywords_tfidf_per_doc(
        corpus=texts,
        top_k=top_n,
        max_features=max_features
    )

    # 3. Flatten → List[NewsKeywordsDTO]
    results = [
        NewsKeywordsDTO(
            news_id=news_id,
            word=kw.word,
            weight=kw.weight,
            method="tfidf"
        )
        for news_id, kws in zip(news_ids, per_doc_keywords)
        for kw in kws
    ]

    return results


def generate_wordcloud(
    corpus: dict[str, list[str]], out_path: str, max_words: int | None = 200
) -> list[str]:
    return generate_trend_wordcloud(corpus, output_dir=out_path, max_words=max_words)


# Public coroutine wrappers
import asyncio


async def async_tfidf_top(corpus: list[dict], top_n: int = 5, max_features: int = None):
    loop = asyncio.get_running_loop()  # 应用于CPU密集型
    return await loop.run_in_executor(
        executor, compute_tfidf_top, corpus, top_n, max_features
    )


async def async_generate_wordcloud(
    corpus: dict[str, list[str]], file_dir: str | None = ""
) -> list[str]:
    out_path = os.path.join(settings.WORDCLOUD_DIR, file_dir)
    # 应用于文件I/O
    return await asyncio.to_thread(generate_wordcloud, corpus, out_path)
