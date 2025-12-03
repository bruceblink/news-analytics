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
  
### 在 Vercel 上部署（使用 Docker 构建）

项目中已包含 `Dockerfile`，可以直接使用 Vercel 的 Docker 构建器 `@vercel/docker` 部署整个应用。基本步骤：

1. 安装并登录 Vercel CLI（可选，但推荐用于初次部署）:

```
npm i -g vercel
vercel login
```

2. 在项目根目录创建 `vercel.json`（仓库已经提供示例配置）。部署时 Vercel 会使用 `Dockerfile` 来构建镜像。

3. 运行（交互式部署）:

```
vercel
```

或进行生产部署：

```
vercel --prod
```

注意事项：
- Vercel 在运行容器时会注入运行时环境变量 `PORT`，项目的 `Dockerfile` 已更新为在运行时读取 `PORT`（回退到 8000）。
- 若使用 Vercel 仓库集成（Git 部署），在 Vercel 项目设置中添加需要的环境变量（例如 `DATABASE_URL`）。
- 若要使用无服务器（Serverless）方式（不使用 Docker），需要将 FastAPI 迁移或拆分成单个函数文件，这需要额外适配，见下方“可选方案”。

