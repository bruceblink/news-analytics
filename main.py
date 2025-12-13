import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from wordfreq_cn.core import get_tokenizer

from app import settings
from app.routers import analysis, search, news

# 获取日志器
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    # 服务启动时执行
    logger.info("检查并预取分词模型...")
    get_tokenizer() # 此时由于 Docker 已经下载好了，这里只是从磁盘加载到内存
    yield

app = FastAPI(title="News Analytics API", lifespan=lifespan)

# 创建静态文件夹
os.makedirs(settings.WORDCLOUD_DIR, exist_ok=True)
# 挂载静态目录
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# include routers
app.include_router(analysis.router, tags=["分析模块"])
app.include_router(search.router, tags=["搜索模块"])
app.include_router(news.router, tags=["新闻模块"])


@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
