# app/__init__.py

"""
应用主包，暴露项目公共 API。
常用导出: config, db, models, routers, services
"""

from . import models
from .config import settings
from .db import get_session

# 子包（routers/services/utils）让外部可以以 app.routers 形式访问
__all__ = [
    "settings",
    "get_session",
    "models",
]
