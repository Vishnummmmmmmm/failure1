import asyncio
from app.ingestors.google_scraper import scrape_google
from app.ingestors.reddit_scraper import scrape_reddit
from app.ingestors.twitter_scraper import scrape_twitter
from app.ingestors.instagram_scraper import scrape_instagram
from app.ingestors.facebook_scraper import scrape_facebook
from app.ingestors.threads_scraper import scrape_threads
from app.ingestors.base import PostSchema

async def ingest_all(keywords: list[str], brand_name: str) -> list[PostSchema]:
    """Run all 6 ingestors concurrently. Returns deduplicated flat list."""
    results = await asyncio.gather(
        scrape_google(keywords, brand_name),
        scrape_reddit(keywords, brand_name),
        scrape_twitter(keywords, brand_name),
        scrape_instagram(keywords, brand_name),
        scrape_facebook(keywords, brand_name),
        scrape_threads(keywords, brand_name),
        return_exceptions=True
    )

    posts = []
    seen = set()
    for batch in results:
        if isinstance(batch, Exception):
            print(f'[Orchestrator] Ingestor failed: {batch}')
            continue
        for p in batch:
            key = p.content[:80]
            if key not in seen:
                seen.add(key)
                posts.append(p)

    print(f'[Orchestrator] Total unique posts ingested: {len(posts)}')
    return posts
