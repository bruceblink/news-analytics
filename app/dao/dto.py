from dataclasses import dataclass

@dataclass
class NewsKeywordsDTO:
    news_id: str
    word: str
    weight: float
    method: str