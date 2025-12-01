import os
from datetime import datetime, date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
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
    start_date: date | None, end_date: date | None, limit: int = 1000
) -> list[dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        sql = "SELECT id, name, news_from, data, news_date FROM news_info"
        conds = []
        params = {}
        start_date = start_date or datetime.now().date()
        if start_date:
            conds.append("news_date >= :start_date")
            params["start_date"] = start_date  # 已经是 date 对象
        if end_date:
            conds.append("news_date <= :end_date")
            params["end_date"] = end_date

        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY news_date DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(text(sql), params)

        rows = [
            {
                "id": row.id,
                "name": row.name,
                "news_from": row.news_from,
                "news_date": row.news_date.isoformat() if row.news_date else None,
                "data": row.data,
            }
            for row in result
        ]

        return rows


@router.get("/news", summary="获取新闻列表（分页）")
async def list_news(
    limit: int = Query(100, ge=1, le=500),
    start_date: str | None = None,
    end_date: str | None = None,
):
    rows = await _fetch_news_rows(start_date, end_date, limit)
    return {"count": len(rows), "items": rows}


class TFIDFQuery(BaseModel):
    n: int = Field(50, ge=1, le=500)
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def check_date_format(cls, v):
        if v is None:
            return v
        try:
            return date.fromisoformat(v)
        except ValueError:
            raise ValueError("日期格式错误，应为 YYYY-MM-DD")


@router.get("/tfidf", summary="返回 TF-IDF Top N 词")
async def tfidf_top(params: TFIDFQuery = Depends()):
    rows = await _fetch_news_rows(params.start_date, params.end_date, limit=5000)

    corpus = await docs_to_corpus(rows)
    if not corpus:
        return {"terms": []}

    from collections import defaultdict

    tops = defaultdict(list)
    for k, v in corpus.items():
        tops[k] = await async_tfidf_top(v, top_n=params.n)

    return {"terms": tops}


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
