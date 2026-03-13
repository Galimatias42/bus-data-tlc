import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urlparse
from datetime import date
from pathlib import Path

def set_day():
    t = date.today().weekday()
    t = t if t<5 else 0
    path = Path(f"folder{t}","URL")
    return path

def read_the_urls(path):
    print(f"Reading URLs from {path}")
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def extract_article_info(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        title = article.title or ""
        authors = article.authors or []
        publish_date = article.publish_date.isoformat() if article.publish_date else None
        text = article.text.strip().replace("\n", " ")
        description = " ".join(text.split()[:150])
        source = urlparse(url).netloc.replace("www.", "")

        return {
            "url": url,
            "source": source,
            "title": title,
            "author": authors,
            "published_date": publish_date,
            "description": description
        }

    except Exception:
        # Fallback using BeautifulSoup
        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.content, "html.parser")

            title = soup.title.string.strip() if soup.title else ""
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text() for p in paragraphs)
            description = " ".join(text.strip().split()[:150])

            author_meta = soup.find("meta", attrs={"name": "author"}) or \
                          soup.find("meta", attrs={"property": "article:author"})
            author = [author_meta["content"]] if author_meta and author_meta.get("content") else []

            date_meta = soup.find("meta", attrs={"property": "article:published_time"}) or \
                        soup.find("meta", attrs={"name": "pubdate"})
            publish_date = date_meta["content"] if date_meta and date_meta.get("content") else None

            source = urlparse(url).netloc.replace("www.", "")

            return {
                "url": url,
                "source": source,
                "title": title,
                "author": author,
                "published_date": publish_date,
                "description": description
            }

        except Exception as e:
            return {
                "url": url,
                "source": None,
                "title": None,
                "author": [],
                "published_date": None,
                "description": f"Failed to extract: {str(e)}"
            }
        
def main(input_path):
    urls = read_the_urls(input_path)
    results = [extract_article_info(url) for url in urls]

    # New output location
    Path("output").mkdir(exist_ok=True)
    output_filename = Path(input_path).stem + ".json"
    output_path = Path("output") / output_filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} articles to {output_path}")

if __name__ == "__main__":
    base_path = set_day()
    if not base_path.exists():
        print(f"Path {base_path} does not exist. Skipping.")
        sys.exit(0)

    for file in os.listdir(base_path):
        if file.endswith(".txt"):
            full_path = base_path / file
            main(str(full_path))