import re
import ssl
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .config import settings

# --------------------------
# 1. 修复 DATABASE_URL
# --------------------------
DATABASE_URL = settings.DATABASE_URL
ENVIRONMENT = settings.ENVIRONMENT  # development / production / staging


# --------------------------
# 2. 根据环境决定是否启用 SSL
# --------------------------

connect_args = {}

if ENVIRONMENT.lower() in ["production", "prod"]:
    ssl_context = ssl.create_default_context()
    connect_args = {"ssl": ssl_context}
else:
    # 本地环境，不使用 SSL
    connect_args = {}


# --------------------------
# 3. 创建异步 Engine
# --------------------------
engine = create_async_engine(
    re.sub(r'^postgresql:', 'postgresql+asyncpg:', DATABASE_URL),
    echo=True,
    connect_args=connect_args
)


# --------------------------
# 4. 异步会话工厂
# --------------------------
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# --------------------------
# 5. FastAPI 依赖注入函数
# --------------------------
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """异步生成器，提供数据库 session"""
    async with AsyncSessionLocal() as session:
        yield session
