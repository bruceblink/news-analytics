import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from app import settings
from app.routers import analysis, search

app = FastAPI(title="News Analytics API")

# 创建静态文件夹
os.makedirs(settings.WORDCLOUD_DIR, exist_ok=True)
# 挂载静态目录
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# include routers
app.include_router(analysis.router, tags=["分析模块"])
app.include_router(search.router, tags=["搜索模块"])


@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
