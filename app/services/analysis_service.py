import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from wordfreq_cn import generate_trend_wordcloud, extract_keywords_tfidf_per_doc

from ..config import settings
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
) -> list[dict]:
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
        item.get("title", "").strip()
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
        {
            "news_id": news_id,
            "keyword": kw.word,
            "weight": kw.weight,
            "method": "tfidf"
        }
        for news_id, kws in zip(news_ids, per_doc_keywords)
        for kw in kws
    ]

    return results


def generate_wordcloud(
    corpus: dict[str, list[str]], out_path: str, max_words: int | None = 200
) -> list[str]:
    return generate_trend_wordcloud(corpus, output_dir=out_path, max_words=max_words)


def build_news_item_from_news_info(news: list[dict]) -> list[dict]:
    """从嵌套新闻数据中构建扁平化条目信息"""
    result = []

    for news_item in news:
        if not (data := news_item.get("data")):
            continue

        # 提取data中重复使用的字段
        news_info_id = news_item.get("id", 0)
        published_at = news_item.get("news_date", None)
        source = news_item.get("name", "")

        # 遍历items并构建结果
        for item in data.get("items", []):
            result.append({
                "item_id": item.get("id", ""),
                "news_info_id": news_info_id,
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published_at": published_at,
                "source": source,
            })

    return result


def build_news_item_from_news_info1(news: list[dict]) -> list[dict]:
    """
     列表生成式优化
    :param news:
    :return:
    """
    return [
        {
            "item_id": item.get("id", ""),
            "news_info_id": data.get("id", 0),
            "title": item.get("title", ""),
            "url": data.get("url", ""),
            "published_at": data.get("news_date", ""),
            "source": data.get("name", ""),
        }
        for news_item in news if (data := news_item.get("data"))
        for item in data.get("items", [])
    ]


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


import numpy as np
from gensim.models import Word2Vec
from sklearn.cluster import MiniBatchKMeans


def compute_embeddings(texts: list[str]) -> list[list[float]]:
    """
    使用 Word2Vec + 句向量平均  计算embedding
    """
    tokenized = [t.split() for t in texts]

    # 训练轻量级 word2vec
    w2v = Word2Vec(
        sentences=tokenized,
        vector_size=128,
        window=5,
        min_count=1,
        workers=4
    )

    def embed_sentence(words):
        vecs = [w2v.wv[w] for w in words if w in w2v.wv]
        return np.mean(vecs, axis=0) if vecs else np.zeros(w2v.vector_size)

    return [embed_sentence(words).tolist() for words in tokenized]


def cluster_embeddings(
        embeddings: list[list[float]],
        n_clusters: int = 50,
        batch_size: int = 64,
        random_state: int = 42
) -> list[int]:
    """
     使用kmeans聚类embeddings
    :param embeddings:
    :param n_clusters:
    :param batch_size:
    :param random_state:
    :return:
    """
    X = np.vstack(embeddings)
    kmeans = MiniBatchKMeans(
        n_clusters=n_clusters,
        batch_size=batch_size,
        random_state=random_state,
        max_iter=100
    )
    labels = kmeans.fit_predict(X)
    return labels.tolist()


def embedding_cluster_pipeline(texts: list[str], n_clusters: int = 50):
    """
     embedding -> cluster 流水线
    :param texts:
    :param n_clusters:
    :return:
    """
    embeddings = compute_embeddings(texts)
    cluster_ids = cluster_embeddings(embeddings, n_clusters)
    return embeddings, cluster_ids