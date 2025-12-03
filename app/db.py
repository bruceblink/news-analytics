from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .config import settings

# --------------------------
# 1. 修复 DATABASE_URL
# --------------------------
DATABASE_URL = settings.DATABASE_URL

# Render 默认 postgres:// 需要改为 asyncpg
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# --------------------------
# 2. 创建异步引擎
# --------------------------
engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,  # 部署生产可关闭
)

# --------------------------
# 3. 异步会话工厂
# --------------------------
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# --------------------------
# 4. 依赖注入函数
# --------------------------
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """异步生成器，提供数据库 session"""
    async with AsyncSessionLocal() as session:
        yield session
