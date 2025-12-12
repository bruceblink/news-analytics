from app.dao import save_news_keywords, update_news_item_extracted_state
from app.dao.news_info_dao import update_news_info_extracted_state
from app.dao.news_item_dao import save_news_items
from app.db import AsyncSessionLocal


async def extract_keywords_task(items: list[dict]):
    """
     提取新闻关键字
    :param items:
    :return:
    """

    async with AsyncSessionLocal() as session:
        async with session.begin():   # ← ★ 事务开始
            await save_news_keywords(session, items)
            await update_news_item_extracted_state(session, items)

        # async with session.begin() 会自动 commit 或 rollback


async def extract_news_items_task(items: list[dict]):
    """
     提取新闻items
    :param items:
    :return:
    """

    async with AsyncSessionLocal() as session:
        async with session.begin():   # ← ★ 事务开始
            await save_news_items(session, items)
            await update_news_info_extracted_state(session, items)