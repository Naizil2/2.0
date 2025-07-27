import json
import random
from datetime import datetime, timedelta

categories = [
    "Politics", "Science", "Health", "Sports", "India", "World",
    "Business", "Tech", "Travel", "Art"
]

news = []
base_date = datetime(2024, 1, 1)
for i in range(1, 2001):  # Use 2001 for a smaller test, or 20001 for full
    category = random.choice(categories)
    date = base_date + timedelta(days=random.randint(0, 200))
    news.append({
        "img": f"https://source.unsplash.com/400x250/?news,{i}",
        "title": f"Fake News Article #{i}",
        "summary": f"This is a summary for fake news article number {i}.",
        "category": category,
        "date": date.strftime("%Y-%m-%d")
    })

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(news, f, indent=2)