FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 1. 复制依赖声明文件（优先复制以利用Docker缓存层）
COPY pyproject.toml .

# 2. 安装依赖
RUN pip install --no-cache-dir .

# 3. 复制项目所有代码
COPY . .

# 4. 暴露端口（与uvicorn运行端口一致）
EXPOSE 8000

# 5. 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
