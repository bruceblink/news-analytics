# helper to query news rows (simple)
from datetime import date

from sqlalchemy import select, and_

from app.db import AsyncSessionLocal
from app.models import news_item


async def fetch_news_item_rows(
        start_date: date | None,
        end_date: date | None,
        limit: int | None = 1000
) -> list[dict]:
    async with AsyncSessionLocal() as session:

        stmt = (
            select(
                news_item.c.id,
                news_item.c.news_info_id,
                news_item.c.title,
                news_item.c.url,
                news_item.c.published_at,
                news_item.c.source,
                news_item.c.content,
            )
        )

        conditions = [news_item.c.extracted == False]  # ⭐ 关键字未提取

        if start_date:
            conditions.append(news_item.c.published_at >= start_date)
        if end_date:
            conditions.append(news_item.c.published_at <= end_date)

        stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(news_item.c.published_at.desc()).limit(limit)

        result = await session.execute(stmt)
        rows = result.mappings().all()

        return [
            {
                "id": r["id"],
                "title": r["title"],
                "url": r["url"],
                "published_at": r["published_at"].isoformat() if r["published_at"] else None,
                "source": r["source"],
                "content": r["content"],
            }
            for r in rows
        ]
