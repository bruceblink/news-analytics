from dataclasses import dataclass

@dataclass
class NewsKeywordsDTO:
    news_id: str
    word: str
    weight: float
    method: str


@dataclass
class NewsItemDTO:
    id: str
    title: str
    url: str
    source: str | None
    published_at: str | None
    score: float