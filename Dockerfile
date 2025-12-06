FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 1. 复制依赖声明文件
COPY pyproject.toml ./
COPY setup.cfg* ./

# 2. 安装依赖
RUN pip install --no-cache-dir .

# 3. 复制项目代码
COPY . .

# 4. 暴露端口（Render 会注入 PORT）
EXPOSE 8001
ENV APP_ENV=production
# 5. 启动命令
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}"]
