import json

with open("news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

cleaned = [n for n in news if all(k in n for k in ("img", "title", "summary", "category", "date"))]

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, indent=2)