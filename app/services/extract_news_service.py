from app.dao import save_news_keywords, update_news_item_extracted_state
from app.db import AsyncSessionLocal


async def extract_keywords_task(items: list[dict]):

    async with AsyncSessionLocal() as session:
        async with session.begin():   # ← ★ 事务开始
            await save_news_keywords(session, items)
            await update_news_item_extracted_state(session, items)

        # async with session.begin() 会自动 commit 或 rollback