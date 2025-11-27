# app/routers/__init__.py
"""
路由模块统一入口。
"""

from .analysis import router as analysis_router

__all__ = ["analysis_router"]
