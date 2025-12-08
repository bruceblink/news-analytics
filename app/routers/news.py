from fastapi import APIRouter

from app.dao.news_item_dao import fetch_news_by_id

router = APIRouter(prefix="/api/news")


@router.get("/{news_id}")
async def get_news_detail(news_id: str):
    # 返回新闻详情
    return await fetch_news_by_id(news_id)

@router.get("/{news_id}/related")
async def get_related_news(news_id: str, limit: int = 10):
    # 返回相关推荐新闻
    pass

@router.get("/trending")
async def trending_news():
    # 返回热点关键词或热门新闻
    pass

@router.get("/cluster")
async def news_cluster():
    # 返回新闻聚类 / 主题
    pass
