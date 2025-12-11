import wordfreq_cn
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.dao import fetch_news_item_by_keywords

router = APIRouter(prefix="/api/search")


class SearchResponse(BaseModel):
    total: int
    items: list[dict]


@router.get("/news", response_model=SearchResponse)
async def search_news(
        q: str = Query(...),
        limit: int = 20,
        offset: int = 0,
):
    keywords = wordfreq_cn.segment_text(q)

    if not keywords:
        return SearchResponse(total=0, items=[])

    items = await fetch_news_item_by_keywords(keywords, limit, offset)

    return SearchResponse(total=len(items), items=items)
