from sqlalchemy import Table, Column, BigInteger, String, Date, Text, TIMESTAMP, MetaData, ForeignKey, JSON, \
    UniqueConstraint, Boolean, Float
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
    Column("extracted", Boolean, nullable=False, server_default="false"),
    Column("extracted_at", TIMESTAMP(timezone=True), nullable=True),
    Column("error", Text, nullable=True),
    UniqueConstraint("news_from", "news_date", name="uniq_news_info")
)

news_item = Table(
    "news_item",
    metadata,
    Column("id", Text, primary_key=True),
    Column("news_info_id", BigInteger, ForeignKey("news_info.id", ondelete="CASCADE")),
    Column("title", Text, nullable=False),
    Column("url", Text, nullable=False),
    Column("published_at", Date),
    Column("source", String(50)),
    Column("content", Text),

    # ⭐ 新增字段
    Column("extracted", Boolean, nullable=False, server_default="false"),
    Column("extracted_at", TIMESTAMP(timezone=True), nullable=True),

    Column("created_at", TIMESTAMP(timezone=True), server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.current_timestamp()),
)

news_keywords = Table(
    "news_keywords",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("news_id",Text,ForeignKey("news_item.id", ondelete="CASCADE"),nullable=False,),
    Column("keyword", Text, nullable=False),
    Column("weight", Float, nullable=True),
    Column("method", Text, nullable=False),
    Column("created_at",TIMESTAMP(timezone=True),server_default=func.current_timestamp(),nullable=False),
    Column("updated_at",TIMESTAMP(timezone=True),server_default=func.current_timestamp(),nullable=False),
    UniqueConstraint("news_id", "keyword", "method", name="uq_news_keywords"),
)