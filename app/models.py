from sqlalchemy import Table, Column, Integer, BigInteger, String, Date, JSON, TIMESTAMP, MetaData, UniqueConstraint

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
