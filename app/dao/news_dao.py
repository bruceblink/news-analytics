from sqlalchemy import select, func, or_

from app.db import AsyncSessionLocal
from app.models import news_item, news_keywords


async def fetch_news_rows(
        keywords: list[str],
        limit: int = 20,
        offset: int = 0,
) -> list[dict]:

    # --- 1) 处理关键词，去空格，忽略空字符串 ---
    keywords = [k.strip() for k in keywords if k.strip()]
    if not keywords:
        return []

    async with AsyncSessionLocal() as session:

        # --- 2) 聚合 TF-IDF 权重排名 ---
        conditions = [news_keywords.c.keyword.ilike(f"%{k}%") for k in keywords]

        stmt = (
            select(
                news_keywords.c.news_id,
                func.coalesce(func.sum(news_keywords.c.weight), 0).label("score")
            )
            .where(or_(*conditions))
            .group_by(news_keywords.c.news_id)
            .order_by(func.coalesce(func.sum(news_keywords.c.weight), 0).desc())
            .limit(limit)
            .offset(offset)
        )

        rows = (await session.execute(stmt)).all()
        if not rows:
            return []

        # --- 3) 获取匹配新闻 ID 和对应分数 ---
        news_ids = [r.news_id for r in rows]
        score_map = {r.news_id: r.score for r in rows}

        # --- 4) 回表查新闻详情 ---
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

        # --- 5) 组合结果，按 score 排序 ---
        items = []
        for r in news_rows:
            items.append(
                {
                    "id": r.id,
                    "title": r.title,
                    "url": r.url,
                    "source": r.source,
                    "published_at": r.published_at.isoformat() if r.published_at else None,
                    "score": score_map.get(r.id, 0),
                }
            )

        # 保证排序和前面聚合结果一致
        items.sort(key=lambda x: x["score"], reverse=True)

        return items