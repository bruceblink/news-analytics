from sqlalchemy import Table, Column, BigInteger, String, Date, Text, TIMESTAMP, MetaData, ForeignKey, JSON, \
    UniqueConstraint
from sqlalchemy.sql import func

metadata = MetaData()

news_info = Table(
    "news_info",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("name", String(50), nullable=False),
    Column("news_from", String(50), nullable=False),
    Column("news_date", Date, nullable=False),
    Column("data", JSON),
    Column("created_at", TIMESTAMP(timezone=True)),
    Column("updated_at", TIMESTAMP(timezone=True)),
    UniqueConstraint("news_from", "news_date", name="uniq_news_info")
)

news_item = Table(
    "news_item",
    metadata,
    Column("id", Text, primary_key=True),  # 使用Text对应PostgreSQL的text类型
    Column("news_info_id", BigInteger, ForeignKey("news_info.id", ondelete="CASCADE")),
    Column("title", Text, nullable=False),
    Column("url", Text, nullable=False),
    Column("published_at", Date),
    Column("source", String(50)),
    Column("content", Text),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.current_timestamp()),
)
