FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 1. 复制依赖声明文件（优先复制以利用Docker缓存层）
COPY pyproject.toml .

# 2. 安装依赖
RUN pip install --no-cache-dir .

# 3. 复制项目所有代码
COPY . .

# 4. 暴露端口（保留为参考，Vercel 会在运行时注入 PORT 环境变量）
EXPOSE 8000

# 5. 启动命令：使用 shell 启动以便在运行时读取环境变量 `PORT`（默认回退到 8000）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
