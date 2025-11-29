import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

from ..config import settings
from ..utils.cleaner import clean_html
from ..utils.tokenizer import tokenize_chinese
from wordfreq_cn import extract_keywords_tfidf

executor = ThreadPoolExecutor(max_workers=2)

# Load Chinese stopwords
with open(settings.STOPWORDS_FILE, encoding="utf-8") as f:
    CHINESE_STOPWORDS = list({line.strip() for line in f if line.strip()})

# Helper to fetch documents from DB
async def docs_to_corpus(rows: List[Dict[str, Any]]) -> List[str]:
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
    tokens = tokenize_chinese(text)
    tokens = [t for t in tokens if t not in CHINESE_STOPWORDS]
    return tokens

def compute_tfidf_top(corpus: List[str], top_n: int = 50, max_features: int = None):
    result = extract_keywords_tfidf(corpus, top_k=top_n, max_features=max_features)
    return [{"term": kws.word, "score": kws.weight} for kws in result.keywords]

def generate_wordcloud(corpus: List[str], out_path: str, max_words: int = 200):
    text = " ".join([" ".join([t for t in tokenize_chinese(t) if t not in CHINESE_STOPWORDS]) for t in corpus])
    if not os.path.exists(os.path.dirname(out_path)):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
    wc = WordCloud(
        font_path=f"{settings.STATIC_DIR}/ARHei.ttf",
        width=1200,
        height=600,
        max_words=max_words,
        stopwords=CHINESE_STOPWORDS
    )
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
