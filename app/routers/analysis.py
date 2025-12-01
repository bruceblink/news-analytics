import os
import re
from datetime import datetime, date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Depends, Path
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text

from ..config import settings
from ..db import AsyncSessionLocal
from ..services.analysis_service import (
    docs_to_corpus,
    async_tfidf_top,
    async_generate_wordcloud,
)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


# helper to query news rows (simple)
async def _fetch_news_rows(
    start_date: date | None, end_date: date | None, limit: int = 1000
) -> list[dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        sql = "SELECT id, name, news_from, data, news_date FROM news_info"
        conds = []
        params = {}
        start_date = start_date or datetime.now().date()
        if start_date:
            conds.append("news_date >= :start_date")
            params["start_date"] = start_date  # 已经是 date 对象
        if end_date:
            conds.append("news_date <= :end_date")
            params["end_date"] = end_date

        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY news_date DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(text(sql), params)

        rows = [
            {
                "id": row.id,
                "name": row.name,
                "news_from": row.news_from,
                "news_date": row.news_date.isoformat() if row.news_date else None,
                "data": row.data,
            }
            for row in result
        ]

        return rows


@router.get("/news", summary="获取新闻列表（分页）")
async def list_news(
    limit: int = Query(100, ge=1, le=500),
    start_date: str | None = None,
    end_date: str | None = None,
):
    rows = await _fetch_news_rows(start_date, end_date, limit)
    return {"count": len(rows), "items": rows}


class TFIDFQuery(BaseModel):
    n: int = Field(50, ge=1, le=500)
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def check_date_format(cls, v):
        if v is None:
            return v
        try:
            return date.fromisoformat(v)
        except ValueError:
            raise ValueError("日期格式错误，应为 YYYY-MM-DD")


@router.get("/tfidf", summary="返回 TF-IDF Top N 词")
async def tfidf_top(params: TFIDFQuery = Depends()):
    rows = await _fetch_news_rows(params.start_date, params.end_date, limit=params.n)

    corpus = await docs_to_corpus(rows)
    if not corpus:
        return {"terms": []}

    from collections import defaultdict

    tops = defaultdict(list)
    for k, v in corpus.items():
        tops[k] = await async_tfidf_top(v, top_n=params.n)

    return {"terms": tops}


class WordcloudQuery(TFIDFQuery):
    pass


@router.get("/wordcloud", summary="生成词云并返回图片 URL")
async def wordcloud(params: WordcloudQuery = Depends()):
    rows = await _fetch_news_rows(params.start_date, params.end_date, limit=params.n)
    corpus = await docs_to_corpus(rows)
    if not corpus:
        raise HTTPException(status_code=404, detail="No documents")

    out = await async_generate_wordcloud(corpus, file_dir="")
    # return direct file or url path list
    return {"urls": out}


# -------------------------
# 内部函数：返回最新文件
# -------------------------
def _get_latest_wordcloud_file(folder: str) -> str | None:
    """返回指定文件夹中修改时间最新的文件路径"""

    wordcloud_pic_dir = os.path.join(settings.WORDCLOUD_DIR, folder)

    if not os.path.exists(wordcloud_pic_dir):
        return None
    files_dir = [
        os.path.join(wordcloud_pic_dir, f) for f in os.listdir(wordcloud_pic_dir)
    ]
    files = [f for f in files_dir if os.path.isfile(f)]
    if not files:
        return None
    # 按修改时间排序
    latest_file = max(files, key=lambda f: os.path.getmtime(f))
    return latest_file


@router.get("/wordcloud/image", summary="获取词云图片（默认当天日期）")
async def wordcloud_image_default():
    """
    获取当天的词云图
    :return:
    """
    wordcloud_date = datetime.now().strftime("%Y-%m-%d")
    latest_file = _get_latest_wordcloud_file(wordcloud_date)
    if not latest_file:
        raise HTTPException(status_code=404, detail="当天没有可用词云图片")
    return FileResponse(latest_file, media_type="image/png")


def get_latest_date_folder():
    """
    获取最新更新的文件夹
    :return:
    """
    folders = []
    for name in os.listdir(settings.WORDCLOUD_DIR):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", name):
            folders.append(name)

    if not folders:
        return None

    # 依赖日期格式排序即可
    return max(folders)


@router.get("/wordcloud/image/latest", summary="获取最新生成的词云图片")
async def wordcloud_image_latest():
    # 遍历 WORDCLOUD_DIR 下的日期子文件夹
    if not os.path.exists(settings.WORDCLOUD_DIR):
        raise HTTPException(status_code=404, detail="没有可用的词云图片")

    latest_folder = get_latest_date_folder()
    if not latest_folder:
        raise HTTPException(status_code=404, detail="没有可用的词云图片")

    # 找到所有文件夹下的最新文件
    latest_file = _get_latest_wordcloud_file(latest_folder)

    if not latest_file:
        raise HTTPException(status_code=404, detail="没有可用的词云图片")

    return FileResponse(latest_file, media_type="image/png")


@router.get("/wordcloud/image/{wordcloud_date}", summary="获取词云图片（指定日期）")
async def wordcloud_image_with_date(
    wordcloud_date: str = Path(..., description="日期，格式 YYYY-MM-DD")
):
    """
    获取指定日期的词云图
    :param wordcloud_date:
    :return:
    """
    # 校验日期格式
    try:
        datetime.strptime(wordcloud_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="日期格式错误，必须为 YYYY-MM-DD")

    latest_file = _get_latest_wordcloud_file(wordcloud_date)
    if not latest_file:
        raise HTTPException(
            status_code=404, detail=f"{wordcloud_date} 没有可用词云图片"
        )
    return FileResponse(latest_file, media_type="image/png")
