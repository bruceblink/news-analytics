import re

def clean_html(text: str) -> str:
    if not text:
        return ""
    # remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # remove URLs
    text = re.sub(r"https?://\S+", " ", text)
    # normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
