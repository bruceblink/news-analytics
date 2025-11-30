import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import text

from ..config import settings
from ..db import AsyncSessionLocal
from ..services.analysis_service import (
    docs_to_corpus,
    async_tfidf_top,
    async_generate_wordcloud,
)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


# helper to query news rows (simple)
async def _fetch_news_rows(
    start_date: str | None, end_date: str | None, limit: int = 1000
) -> list[dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        sql = "SELECT id, name, news_from, data, news_date FROM news_info"
        conds = []
        params = {}
        if start_date:
            conds.append("news_date >= :start_date")
            params["start_date"] = start_date
        if end_date:
            conds.append("news_date <= :end_date")
            params["end_date"] = end_date
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY news_date DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(text(sql), params)
        rows = []
        for row in result:
            row_dict = {
                "id": row.id,
                "name": row.name,
                "news_from": row.news_from,
                "news_date": (
                    row.news_date.isoformat() if row.news_date else None
                ),  # 格式化为 YYYY-MM-DD
                "data": row.data,
            }
            rows.append(row_dict)
        return rows


@router.get("/news", summary="获取新闻列表（分页）")
async def list_news(
    limit: int = Query(100, ge=1, le=500),
    start_date: str | None = None,
    end_date: str | None = None,
):
    rows = await _fetch_news_rows(start_date, end_date, limit)
    return {"count": len(rows), "items": rows}


@router.get("/tfidf", summary="返回 TF-IDF Top N 词")
async def tfidf_top(
    n: int = Query(50, ge=1, le=500),
    start_date: str | None = None,
    end_date: str | None = None,
):
    rows = await _fetch_news_rows(start_date, end_date, limit=5000)
    corpus = await docs_to_corpus(rows)
    if not corpus:
        return {"terms": []}
    top = await async_tfidf_top(corpus, top_n=n)
    return {"terms": top}


@router.get("/wordcloud", summary="生成词云并返回图片 URL")
async def wordcloud(start_date: str | None = None, end_date: str | None = None):
    rows = await _fetch_news_rows(start_date, end_date, limit=5000)
    corpus = await docs_to_corpus(rows)
    if not corpus:
        raise HTTPException(status_code=404, detail="No documents")

    out = await async_generate_wordcloud(corpus, file_dir="")
    # return direct file or url path list
    return {"urls": out}


@router.get("/wordcloud/image/{filename}")
async def wordcloud_image(filename: str):
    path = os.path.join(settings.WORDCLOUD_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="image/png")
