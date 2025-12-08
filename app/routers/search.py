from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.dao.news_dao import fetch_news_rows

router = APIRouter(prefix="/api/search")


class SearchResponse(BaseModel):
    total: int
    items: list[dict]


def extract_keywords_from_query(q: str) -> list[str]:
    # 示例：真正使用你已有的 TF-IDF/Jieba 分词
    return q.split()


@router.get("/news", response_model=SearchResponse)
async def search_news(
        q: str = Query(...),
        limit: int = 20,
        offset: int = 0,
):
    keywords = extract_keywords_from_query(q)

    if not keywords:
        return SearchResponse(total=0, items=[])

    items = await fetch_news_rows(keywords, limit, offset)

    return SearchResponse(total=len(items), items=items)
