import re

def normalize(text: str) -> str:
    text = text.replace("’", "'").lower()
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def words(text: str) -> list[str]:
    s = normalize(text)
    return s.split() if s else []
