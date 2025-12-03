FROM python:3.12-slim

# 安装系统依赖（wordcloud / matplotlib 需要）
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

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
EXPOSE 8000

# 5. 启动命令
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
