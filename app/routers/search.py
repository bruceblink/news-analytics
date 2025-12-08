from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select, func

from app.db import AsyncSessionLocal
from app.models import news_keywords, news_item

router = APIRouter(prefix="/api/search")


class NewsItemModel(BaseModel):
    id: str
    title: str
    url: str
    source: str | None
    published_at: str | None
    score: float


class SearchResponse(BaseModel):
    total: int
    items: list[NewsItemModel]


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

    async with AsyncSessionLocal() as session:

        # --- 1) 聚合 TF-IDF 权重排名 ---
        stmt = (
            select(
                news_keywords.c.news_id,
                func.sum(news_keywords.c.weight).label("score")
            )
            .where(news_keywords.c.keyword.in_(keywords))
            .group_by(news_keywords.c.news_id)
            .order_by(func.sum(news_keywords.c.weight).desc())
            .limit(limit)
            .offset(offset)
        )

        rows = (await session.execute(stmt)).all()

        if not rows:
            return SearchResponse(total=0, items=[])

        news_ids = [r.news_id for r in rows]
        score_map = {r.news_id: r.score for r in rows}

        # --- 2) 回表查新闻详情 ---
        news_stmt = (
            select(
                news_item.c.id,
                news_item.c.title,
                news_item.c.url,
                news_item.c.source,
                news_item.c.published_at,
            )
            .where(news_item.c.id.in_(news_ids))
        )

        news_rows = (await session.execute(news_stmt)).all()

        # --- 3) 组合结果 ---
        items = []
        for r in news_rows:
            items.append(
                NewsItemModel(
                    id=r.id,
                    title=r.title,
                    url=r.url,
                    source=r.source,
                    published_at=(
                        r.published_at.isoformat() if r.published_at else None
                    ),
                    score=score_map[r.id],
                )
            )

        items.sort(key=lambda x: x.score, reverse=True)

        return SearchResponse(total=len(items), items=items)
