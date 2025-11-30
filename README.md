# FastAPI News Analytics

## 快速跑起来（本地）

1. 准备 PostgreSQL，并确认 `DATABASE_URL` 环境变量指向你的 DB（示例: postgresql+asyncpg://user:pass@host:5432/db）
2. 安装依赖:
   pip install -r requirements.txt
3. 运行:
   uvicorn app.main:app --reload --port 8000

## API 示例

- GET /health
- GET /api/analysis/news?limit=100
- GET /api/analysis/tfidf?n=50&start_date=2025-11-01&end_date=2025-11-27
- GET /api/analysis/wordcloud?start_date=2025-11-01&end_date=2025-11-27
  -> 返回 {"url": "/static/wordclouds/wc_xxx.png"}

## 部署

- 推荐打包成 Docker 镜像并部署到 Fly.io（或同类平台）
- 注意：需要将字体文件加入镜像或使用系统字体以支持中文词云

