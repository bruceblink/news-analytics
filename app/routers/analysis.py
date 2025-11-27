from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy import text
from ..db import AsyncSessionLocal
from ..services.analysis_service import docs_to_corpus, async_tfidf_top, async_generate_wordcloud
from ..config import settings
import os
import uuid
import asyncio
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# helper to query news rows (simple)
async def _fetch_news_rows(start_date: Optional[str], end_date: Optional[str], limit: int = 1000):
    async with AsyncSessionLocal() as session:
        sql = "SELECT id, data, news_date FROM news_info"
        conds = []
        params = {}
        if start_date:
            conds.append("news_date >= :start_date"); params["start_date"] = start_date
        if end_date:
            conds.append("news_date <= :end_date"); params["end_date"] = end_date
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY news_date DESC LIMIT :limit"
        params["limit"] = limit
        res = await session.execute(text(sql), params)
        rows = [dict(r._mapping) for r in res.fetchall()]
        return rows

@router.get("/news", summary="获取新闻列表（分页）")
async def list_news(limit: int = Query(100, ge=1, le=500), start_date: Optional[str] = None, end_date: Optional[str] = None):
    rows = await _fetch_news_rows(start_date, end_date, limit)
    return {"count": len(rows), "items": rows}

@router.get("/tfidf", summary="返回 TF-IDF Top N 词")
async def tfidf_top(n: int = Query(50, ge=1, le=500), start_date: Optional[str] = None, end_date: Optional[str] = None):
    rows = await _fetch_news_rows(start_date, end_date, limit=5000)
    corpus = await docs_to_corpus(rows)
    if not corpus:
        return {"terms": []}
    top = await async_tfidf_top(corpus, top_n=n)
    return {"terms": top}

@router.get("/wordcloud", summary="生成词云并返回图片 URL")
async def wordcloud(start_date: Optional[str] = None, end_date: Optional[str] = None):
    rows = await _fetch_news_rows(start_date, end_date, limit=5000)
    corpus = await docs_to_corpus(rows)
    if not corpus:
        raise HTTPException(status_code=404, detail="No documents")
    filename = f"wc_{uuid.uuid4().hex}.png"
    out = await async_generate_wordcloud(corpus, filename)
    # return direct file or url path
    return {"url": f"/static/wordclouds/{os.path.basename(out)}"}

@router.get("/wordcloud/image/{filename}")
async def wordcloud_image(filename: str):
    path = os.path.join(settings.WORDCLOUD_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="image/png")
