import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import settings
from app.routers import analysis

app = FastAPI(title="News Analytics API")

# 创建静态文件夹
os.makedirs(settings.WORDCLOUD_DIR, exist_ok=True)
# 挂载静态目录
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# include routers
app.include_router(analysis.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
