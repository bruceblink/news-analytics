from sqlalchemy import literal_column
from sqlalchemy.dialects.postgresql import insert

from app.db import AsyncSessionLocal
from app.models import news_keywords


async def save_news_keywords(items: list[dict]) -> None:

    if not items:
        return None

    async with AsyncSessionLocal() as session:

        stmt = insert(news_keywords).values(items)

        # ❗ 冲突更新（推荐：更新 weight）
        stmt = stmt.on_conflict_do_update(
            index_elements=["news_id", "keyword", "method"],
            set_={
                "weight": literal_column("excluded.weight"),
                "method": literal_column("excluded.method"),
            }
        )

        await session.execute(stmt)
        await session.commit()
        return None
