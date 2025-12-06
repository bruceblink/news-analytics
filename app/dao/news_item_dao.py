# helper to query news rows (simple)
from datetime import datetime, date
from typing import Any

from sqlalchemy import text

from app.db import AsyncSessionLocal


async def fetch_news_item_rows(
        start_date: date | None, end_date: date | None, limit: int | None = 1000
) -> list[dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        sql = "SELECT id, news_info_id, title, url, published_at, source, content FROM news_item"
        conds = []
        params = {}
        start_date = start_date or datetime.now().date()
        if start_date:
            conds.append("published_at >= :start_date")
            params["start_date"] = start_date  # 已经是 date 对象
        if end_date:
            conds.append("published_at <= :end_date")
            params["end_date"] = end_date

        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY published_at DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(text(sql), params)

        rows = [
            {
                "id": row.id,
                "title": row.title,
                "url": row.url,
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "source": row.source,
                "content": row.content,
            }
            for row in result
        ]

        return rows